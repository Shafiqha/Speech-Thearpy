import React, { useState, useRef, useEffect } from 'react';
import { Video, Mic, Camera, CheckCircle, XCircle, Volume2, RotateCcw } from 'lucide-react';
import axios from 'axios';

interface Viseme {
  phoneme: string;
  viseme: string;
  viseme_id: number;
  start_time: number;
  duration: number;
  end_time: number;
}

interface WordAnalysis {
  word: string;
  language: string;
  phonemes: string[];
  visemes: Viseme[];
  total_duration: number;
  phoneme_count: number;
  viseme_count: number;
}

interface VideoGeneration {
  success: boolean;
  word: string;
  language: string;
  video_url: string;
  audio_url: string;
  phonemes: string[];
  visemes: Viseme[];
  duration_ms: number;
}

interface PracticeResult {
  success: boolean;
  accuracy: number;
  lip_sync_score: number;
  transcription: string;
  feedback: string;
  errors: string[];
  phoneme_accuracy: { [key: string]: number };
  viseme_accuracy: { [key: string]: number };
  video_analysis: any;
}

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const LipAnimationExercise: React.FC = () => {
  const [word, setWord] = useState('');
  const [language, setLanguage] = useState('en');
  const [wordAnalysis, setWordAnalysis] = useState<WordAnalysis | null>(null);
  const [videoGeneration, setVideoGeneration] = useState<VideoGeneration | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isPracticing, setIsPracticing] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [practiceResult, setPracticeResult] = useState<PracticeResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const userVideoRef = useRef<HTMLVideoElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const recordedChunksRef = useRef<Blob[]>([]);
  const audioChunksRef = useRef<Blob[]>([]);
  const feedbackAudioRef = useRef<HTMLAudioElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  // Force video to load when videoGeneration changes
  useEffect(() => {
    if (videoGeneration && videoRef.current) {
      const videoUrl = `${API_BASE_URL}${videoGeneration.video_url}`;
      console.log('🎬 Loading video:', videoUrl);
      
      videoRef.current.src = videoUrl;
      videoRef.current.load();
      
      videoRef.current.addEventListener('loadeddata', () => {
        console.log('✅ Video loaded, attempting to play...');
        videoRef.current?.play().catch(err => {
          console.log('⚠️ Autoplay prevented (this is normal):', err);
        });
      });
      
      videoRef.current.addEventListener('error', (e) => {
        console.error('❌ Video error:', e);
        console.error('Video URL:', videoUrl);
        console.error('Video error code:', videoRef.current?.error?.code);
        console.error('Video error message:', videoRef.current?.error?.message);
      });
    }
  }, [videoGeneration]);

  const analyzeWord = async () => {
    if (!word.trim()) {
      alert('Please enter a word');
      return;
    }

    try {
      const response = await axios.post(`${API_BASE_URL}/api/lip-animation/analyze-word`, {
        word: word.trim(),
        language
      });
      setWordAnalysis(response.data);
    } catch (error) {
      console.error('Word analysis failed:', error);
      alert('Failed to analyze word. Please try again.');
    }
  };

  const generateVideo = async () => {
    if (!word.trim()) {
      alert('Please enter a word');
      return;
    }

    setIsGenerating(true);
    console.log('🎬 Generating video for:', word, 'Language:', language);
    
    try {
      // First, analyze the word
      console.log('📊 Step 1: Analyzing word...');
      const analysisResponse = await axios.post(`${API_BASE_URL}/api/lip-animation/analyze-word`, {
        word: word.trim(),
        language
      });
      setWordAnalysis(analysisResponse.data);
      console.log('✅ Word analysis complete:', analysisResponse.data);
      
      // Then generate video
      console.log('🎥 Step 2: Generating video...');
      const response = await axios.post(`${API_BASE_URL}/api/lip-animation/generate-video`, {
        word: word.trim(),
        language
      });
      
      console.log('✅ Video generation response:', response.data);
      setVideoGeneration(response.data);
      
      // Log the URLs for debugging
      console.log('📹 Video URL:', `${API_BASE_URL}${response.data.video_url}`);
      console.log('🔊 Audio URL:', `${API_BASE_URL}${response.data.audio_url}`);
      
    } catch (error: any) {
      console.error('❌ Video generation failed:', error);
      console.error('Error details:', error.response?.data || error.message);
      
      let errorMessage = 'Failed to generate video. ';
      if (error.response) {
        errorMessage += `Server error: ${error.response.status}. `;
        errorMessage += error.response.data?.detail || 'Please check if backend is running.';
      } else if (error.request) {
        errorMessage += 'Cannot connect to server. Please ensure backend is running on port 8000.';
      } else {
        errorMessage += error.message;
      }
      
      alert(errorMessage);
    } finally {
      setIsGenerating(false);
    }
  };

  const startPractice = async () => {
    try {
      console.log('🎥 Requesting camera and microphone access...');
      
      // Request camera and microphone access with specific constraints
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: 'user'
        },
        audio: {
          echoCancellation: true,
          noiseSuppression: true
        }
      });
      
      console.log('✅ Camera access granted');
      console.log('Stream tracks:', stream.getTracks().map(t => `${t.kind}: ${t.label}`));
      console.log('Video tracks active:', stream.getVideoTracks()[0]?.enabled);
      
      streamRef.current = stream;
      
      // IMPORTANT: Set practicing state FIRST so video element renders
      setIsPracticing(true);
      setPracticeResult(null);
      
      // Wait a moment for React to render the video element
      setTimeout(() => {
        if (userVideoRef.current) {
          console.log('📹 Setting video srcObject...');
          userVideoRef.current.srcObject = stream;
          
          // Force video to play
          userVideoRef.current.onloadedmetadata = () => {
            console.log('✅ Video metadata loaded');
            console.log('Video dimensions:', userVideoRef.current?.videoWidth, 'x', userVideoRef.current?.videoHeight);
            userVideoRef.current?.play()
              .then(() => console.log('✅ Video playing!'))
              .catch(err => console.error('❌ Failed to play video:', err));
          };
          
          console.log('✅ Video element configured');
        } else {
          console.error('❌ Video element ref is still null after timeout');
          alert('Camera preview failed to initialize. Please try again.');
        }
      }, 100);
      
      console.log('✅ Practice mode activated');
    } catch (error: any) {
      console.error('❌ Failed to access camera/microphone:', error);
      
      let errorMessage = 'Camera access failed. ';
      if (error.name === 'NotAllowedError') {
        errorMessage += 'Please allow camera and microphone permissions in your browser.';
      } else if (error.name === 'NotFoundError') {
        errorMessage += 'No camera or microphone found. Please connect a device.';
      } else if (error.name === 'NotReadableError') {
        errorMessage += 'Camera is already in use by another application.';
      } else {
        errorMessage += error.message;
      }
      
      alert(errorMessage);
    }
  };

  const startRecording = () => {
    if (!streamRef.current) {
      alert('Camera not initialized. Please try again.');
      return;
    }

    recordedChunksRef.current = [];
    audioChunksRef.current = [];

    try {
      // Try different mimeTypes for better compatibility
      let videoMimeType = 'video/webm;codecs=vp8';
      if (!MediaRecorder.isTypeSupported(videoMimeType)) {
        videoMimeType = 'video/webm';
      }

      // Create video recorder
      const videoRecorder = new MediaRecorder(streamRef.current, {
        mimeType: videoMimeType
      });

      videoRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          recordedChunksRef.current.push(event.data);
          console.log('Video chunk recorded:', event.data.size, 'bytes');
        }
      };

      videoRecorder.onerror = (event) => {
        console.error('Video recorder error:', event);
        alert('Video recording failed. Please try again.');
      };

      // Create audio-only recorder
      const audioStream = new MediaStream(
        streamRef.current.getAudioTracks()
      );
      
      let audioMimeType = 'audio/webm';
      if (!MediaRecorder.isTypeSupported(audioMimeType)) {
        audioMimeType = 'audio/wav';
      }

      const audioRecorder = new MediaRecorder(audioStream, {
        mimeType: audioMimeType
      });

      audioRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
          console.log('Audio chunk recorded:', event.data.size, 'bytes');
        }
      };

      audioRecorder.onerror = (event) => {
        console.error('Audio recorder error:', event);
      };

      mediaRecorderRef.current = videoRecorder;
      
      // Start recording with timeslice to get data chunks
      videoRecorder.start(100); // Get data every 100ms
      audioRecorder.start(100);
      
      setIsRecording(true);

      console.log('✅ Recording started successfully');
    } catch (error) {
      console.error('Failed to start recording:', error);
      alert('Failed to start recording. Please check camera permissions.');
    }
  };

  const stopRecording = async () => {
    if (!mediaRecorderRef.current) return;

    return new Promise<void>((resolve) => {
      mediaRecorderRef.current!.onstop = () => {
        console.log('Recording stopped');
        resolve();
      };
      
      mediaRecorderRef.current!.stop();
      setIsRecording(false);
    });
  };

  const submitPractice = async () => {
    await stopRecording();
    
    if (recordedChunksRef.current.length === 0 || audioChunksRef.current.length === 0) {
      alert('No recording found. Please record again.');
      return;
    }

    setIsAnalyzing(true);

    try {
      const videoBlob = new Blob(recordedChunksRef.current, { type: 'video/webm' });
      const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });

      const formData = new FormData();
      formData.append('video', videoBlob, 'practice.webm');
      formData.append('audio', audioBlob, 'practice.webm');
      formData.append('word', word.trim());
      formData.append('language', language);

      const response = await axios.post(
        `${API_BASE_URL}/api/lip-animation/submit-practice`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      setPracticeResult(response.data);
    } catch (error) {
      console.error('Practice submission failed:', error);
      alert('Failed to analyze your practice. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const stopPractice = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    
    if (userVideoRef.current) {
      userVideoRef.current.srcObject = null;
    }
    
    setIsPracticing(false);
    setIsRecording(false);
  };

  const reset = () => {
    setWord('');
    setWordAnalysis(null);
    setVideoGeneration(null);
    setPracticeResult(null);
    stopPractice();
  };

  const speakFeedback = (text: string) => {
    // Use Web Speech API to read feedback aloud
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel(); // Stop any ongoing speech
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.9; // Slightly slower for clarity
      utterance.pitch = 1.0;
      utterance.volume = 1.0;
      window.speechSynthesis.speak(utterance);
      console.log('🔊 Speaking feedback:', text);
    } else {
      alert('Text-to-speech not supported in this browser');
    }
  };

  return (
    <div className="min-h-screen py-8">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="card mb-8">
          <h1 className="text-3xl font-display font-bold gradient-text mb-2">
            Lip Animation Exercise
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Practice pronunciation with visual lip movements and real-time feedback
          </p>
        </div>

        {/* Word Input Section */}
        <div className="card mb-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            1. Enter a Word
          </h2>
          
          <div className="flex gap-4 mb-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Word to Practice
              </label>
              <input
                type="text"
                value={word}
                onChange={(e) => setWord(e.target.value)}
                placeholder="Enter a word (e.g., hello, नमस्ते, ನಮಸ್ಕಾರ)"
                className="input-field"
              />
            </div>
            
            <div className="w-48">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Language
              </label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="input-field"
              >
                <option value="en">English</option>
                <option value="hi">Hindi</option>
                <option value="kn">Kannada</option>
              </select>
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={analyzeWord}
              className="btn-primary"
            >
              Analyze Word
            </button>
            
            <button
              onClick={generateVideo}
              disabled={isGenerating}
              className="btn-secondary flex items-center gap-2 disabled:opacity-50"
            >
              <Video size={20} />
              {isGenerating ? 'Generating...' : 'Generate Video'}
            </button>

            <button
              onClick={reset}
              className="px-6 py-3 bg-gray-600 dark:bg-slate-600 text-white rounded-xl hover:bg-gray-700 dark:hover:bg-slate-700 transition-all flex items-center gap-2"
            >
              <RotateCcw size={20} />
              Reset
            </button>
          </div>
        </div>

        {/* Phoneme/Viseme Breakdown */}
        {wordAnalysis && (
          <div className="card mb-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              2. Phoneme & Viseme Breakdown
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <h3 className="font-semibold text-gray-700 mb-2">Phonemes</h3>
                <div className="flex flex-wrap gap-2">
                  {wordAnalysis.phonemes.map((phoneme, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 bg-blue-200 text-blue-800 rounded-full text-sm font-mono"
                    >
                      {phoneme}
                    </span>
                  ))}
                </div>
              </div>

              <div className="bg-green-50 p-4 rounded-lg">
                <h3 className="font-semibold text-gray-700 mb-2">
                  Visemes ({wordAnalysis.viseme_count})
                </h3>
                <p className="text-sm text-gray-600">
                  Duration: {wordAnalysis.total_duration}ms
                </p>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Phoneme
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Viseme
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Start (ms)
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Duration (ms)
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {wordAnalysis.visemes.map((viseme, idx) => (
                    <tr key={idx}>
                      <td className="px-4 py-2 text-sm font-mono">{viseme.phoneme}</td>
                      <td className="px-4 py-2 text-sm">{viseme.viseme}</td>
                      <td className="px-4 py-2 text-sm">{viseme.start_time}</td>
                      <td className="px-4 py-2 text-sm">{viseme.duration}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Video Display */}
        {videoGeneration && (
          <div className="card mb-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              3. Watch Lip Animation
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">Video Animation</h3>
                <video
                  ref={videoRef}
                  controls
                  className="w-full rounded-lg border-2 border-gray-300 dark:border-gray-600"
                  src={`${API_BASE_URL}${videoGeneration.video_url}`}
                  onError={(e) => {
                    console.error('❌ Video failed to load:', `${API_BASE_URL}${videoGeneration.video_url}`);
                    console.error('Video error:', e);
                  }}
                  onLoadedData={() => {
                    console.log('✅ Video loaded successfully');
                  }}
                >
                  Your browser does not support the video tag.
                </video>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                  URL: {`${API_BASE_URL}${videoGeneration.video_url}`}
                </p>
              </div>

              <div>
                <h3 className="font-semibold text-gray-700 mb-2">Audio Pronunciation</h3>
                <div className="bg-gray-50 p-6 rounded-lg flex items-center justify-center h-64">
                  <div className="text-center">
                    <Volume2 size={48} className="mx-auto mb-4 text-blue-600" />
                    <audio
                      controls
                      className="w-full"
                      src={`${API_BASE_URL}${videoGeneration.audio_url}`}
                    >
                      Your browser does not support the audio tag.
                    </audio>
                    <p className="mt-4 text-sm text-gray-600">
                      Listen to the pronunciation and watch the lip movements
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Practice Section */}
        {videoGeneration && (
          <div className="card mb-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              4. Practice with Camera
            </h2>

            {!isPracticing ? (
              <button
                onClick={startPractice}
                className="btn-primary flex items-center gap-2 text-lg"
              >
                <Camera size={24} />
                Start Practice
              </button>
            ) : (
              <div>
                <div className="mb-4 relative">
                  <video
                    ref={userVideoRef}
                    autoPlay
                    playsInline
                    muted
                    className="w-full max-w-2xl mx-auto rounded-lg border-4 border-purple-300"
                    style={{ backgroundColor: '#000', minHeight: '400px', maxHeight: '600px' }}
                  />
                  {!streamRef.current && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50 rounded-lg">
                      <div className="text-center text-white">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
                        <p>Initializing camera...</p>
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex gap-3 justify-center">
                  {!isRecording ? (
                    <button
                      onClick={startRecording}
                      className="px-6 py-3 bg-red-600 text-white rounded-xl hover:bg-red-700 transition-all flex items-center gap-2"
                    >
                      <Mic size={20} />
                      Start Recording
                    </button>
                  ) : (
                    <button
                      onClick={submitPractice}
                      disabled={isAnalyzing}
                      className="px-6 py-3 bg-green-600 text-white rounded-xl hover:bg-green-700 transition-all flex items-center gap-2 disabled:opacity-50"
                    >
                      <CheckCircle size={20} />
                      {isAnalyzing ? 'Analyzing...' : 'Stop & Analyze'}
                    </button>
                  )}

                  <button
                    onClick={stopPractice}
                    className="px-6 py-3 bg-gray-600 dark:bg-slate-600 text-white rounded-xl hover:bg-gray-700 dark:hover:bg-slate-700 transition-all"
                  >
                    Cancel
                  </button>
                </div>

                {isRecording && (
                  <div className="mt-4 text-center">
                    <div className="inline-flex items-center gap-2 px-4 py-2 bg-red-100 text-red-800 rounded-full">
                      <div className="w-3 h-3 bg-red-600 rounded-full animate-pulse" />
                      Recording in progress...
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Results Section */}
        {practiceResult && (
          <div className="card">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              5. Practice Results
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="bg-blue-50 p-4 rounded-lg text-center">
                <h3 className="text-sm font-medium text-gray-600 mb-1">Accuracy</h3>
                <p className="text-3xl font-bold text-blue-600">
                  {practiceResult.accuracy.toFixed(1)}%
                </p>
              </div>

              <div className="bg-green-50 p-4 rounded-lg text-center">
                <h3 className="text-sm font-medium text-gray-600 mb-1">Lip Sync Score</h3>
                <p className="text-3xl font-bold text-green-600">
                  {practiceResult.lip_sync_score.toFixed(1)}%
                </p>
              </div>

              <div className="bg-purple-50 p-4 rounded-lg text-center">
                <h3 className="text-sm font-medium text-gray-600 mb-1">Transcription</h3>
                <p className="text-lg font-semibold text-purple-600">
                  {practiceResult.transcription || 'N/A'}
                </p>
              </div>
            </div>

            <div className="bg-gray-50 dark:bg-slate-700/50 p-4 rounded-lg mb-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold text-gray-700 dark:text-gray-300">Feedback</h3>
                <button
                  onClick={() => speakFeedback(practiceResult.feedback)}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <Volume2 size={18} />
                  Listen
                </button>
              </div>
              <p className="text-gray-700 dark:text-gray-300 whitespace-pre-line">{practiceResult.feedback}</p>
            </div>

            {practiceResult.errors.length > 0 && (
              <div className="bg-red-50 p-4 rounded-lg mb-4">
                <h3 className="font-semibold text-red-800 mb-2 flex items-center gap-2">
                  <XCircle size={20} />
                  Errors Detected
                </h3>
                <ul className="list-disc list-inside space-y-1">
                  {practiceResult.errors.map((error, idx) => (
                    <li key={idx} className="text-red-700 text-sm">{error}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h3 className="font-semibold text-gray-700 mb-2">Phoneme Accuracy</h3>
                <div className="space-y-2">
                  {Object.entries(practiceResult.phoneme_accuracy).map(([phoneme, accuracy]) => (
                    <div key={phoneme} className="flex items-center gap-2">
                      <span className="font-mono text-sm w-12">{phoneme}</span>
                      <div className="flex-1 bg-gray-200 rounded-full h-4">
                        <div
                          className="bg-blue-600 h-4 rounded-full transition-all"
                          style={{ width: `${accuracy}%` }}
                        />
                      </div>
                      <span className="text-sm w-12 text-right">{accuracy.toFixed(0)}%</span>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="font-semibold text-gray-700 mb-2">Viseme Accuracy</h3>
                <div className="space-y-2">
                  {Object.entries(practiceResult.viseme_accuracy).map(([viseme, accuracy]) => (
                    <div key={viseme} className="flex items-center gap-2">
                      <span className="text-sm w-12">{viseme}</span>
                      <div className="flex-1 bg-gray-200 rounded-full h-4">
                        <div
                          className="bg-green-600 h-4 rounded-full transition-all"
                          style={{ width: `${accuracy}%` }}
                        />
                      </div>
                      <span className="text-sm w-12 text-right">{accuracy.toFixed(0)}%</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LipAnimationExercise;
