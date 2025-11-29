import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Camera, Mic, Volume2, CheckCircle, XCircle, ArrowRight, Loader, Play, Target, AlertCircle, RefreshCw } from 'lucide-react';
import axios from 'axios';

interface PictureExercise {
  id: number;
  picture_url: string;
  picture_name: string;
  target_text: string;
  difficulty: string;
}

interface FeedbackResult {
  transcription: string;
  accuracy: number;
  wab_score: number;
  severity: string;
  feedback: string;
  feedback_audio_url: string;
  word_corrections: any[];
  practice_suggestions: string[];
}

const PictureTherapy: React.FC = () => {
  const [exercises, setExercises] = useState<PictureExercise[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [language, setLanguage] = useState('en');
  const [difficulty] = useState('easy');
  
  // Session states
  const [hasPlayedWord, setHasPlayedWord] = useState(false);
  const [isPlayingWord, setIsPlayingWord] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [result, setResult] = useState<FeedbackResult | null>(null);
  const [showResult, setShowResult] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const wordAudioRef = useRef<HTMLAudioElement>(null);
  const feedbackAudioRef = useRef<HTMLAudioElement>(null);

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';

  // Mock exercises data
  const mockExercises: Record<string, PictureExercise[]> = {
    en: [
      { id: 1, picture_name: 'Apple', target_text: 'apple', difficulty: 'easy', picture_url: '/images/exercises/apple.jpg' },
      { id: 2, picture_name: 'Cat', target_text: 'cat', difficulty: 'easy', picture_url: '/images/exercises/cat.jpg' },
      { id: 3, picture_name: 'House', target_text: 'house', difficulty: 'easy', picture_url: '/images/exercises/house.jpg' },
      { id: 4, picture_name: 'Dog', target_text: 'dog', difficulty: 'easy', picture_url: '/images/exercises/dog.jpg' },
      { id: 5, picture_name: 'Car', target_text: 'car', difficulty: 'easy', picture_url: '/images/exercises/car.jpg' },
      { id: 6, picture_name: 'Book', target_text: 'book', difficulty: 'easy', picture_url: '/images/exercises/book.jpg' },
      { id: 7, picture_name: 'Chair', target_text: 'chair', difficulty: 'medium', picture_url: '/images/exercises/chair.jpg' },
      { id: 8, picture_name: 'Table', target_text: 'table', difficulty: 'medium', picture_url: '/images/exercises/table.jpg' },
      { id: 9, picture_name: 'Flower', target_text: 'flower', difficulty: 'medium', picture_url: '/images/exercises/flower.jpg' },
      { id: 10, picture_name: 'Tree', target_text: 'tree', difficulty: 'medium', picture_url: '/images/exercises/tree.jpg' },
    ],
    hi: [
      { id: 1, picture_name: 'Apple', target_text: 'सेब', difficulty: 'easy', picture_url: '/images/exercises/apple.jpg' },
      { id: 2, picture_name: 'Cat', target_text: 'बिल्ली', difficulty: 'easy', picture_url: '/images/exercises/cat.jpg' },
      { id: 3, picture_name: 'House', target_text: 'घर', difficulty: 'easy', picture_url: '/images/exercises/house.jpg' },
      { id: 4, picture_name: 'Dog', target_text: 'कुत्ता', difficulty: 'easy', picture_url: '/images/exercises/dog.jpg' },
      { id: 5, picture_name: 'Car', target_text: 'गाड़ी', difficulty: 'easy', picture_url: '/images/exercises/car.jpg' },
      { id: 6, picture_name: 'Book', target_text: 'किताब', difficulty: 'easy', picture_url: '/images/exercises/book.jpg' },
      { id: 7, picture_name: 'Chair', target_text: 'कुर्सी', difficulty: 'medium', picture_url: '/images/exercises/chair.jpg' },
      { id: 8, picture_name: 'Table', target_text: 'मेज़', difficulty: 'medium', picture_url: '/images/exercises/table.jpg' },
      { id: 9, picture_name: 'Flower', target_text: 'फूल', difficulty: 'medium', picture_url: '/images/exercises/flower.jpg' },
      { id: 10, picture_name: 'Tree', target_text: 'पेड़', difficulty: 'medium', picture_url: '/images/exercises/tree.jpg' },
    ],
    kn: [
      { id: 1, picture_name: 'Apple', target_text: 'ಸೇಬು', difficulty: 'easy', picture_url: '/images/exercises/apple.jpg' },
      { id: 2, picture_name: 'Cat', target_text: 'ಬೆಕ್ಕು', difficulty: 'easy', picture_url: '/images/exercises/cat.jpg' },
      { id: 3, picture_name: 'House', target_text: 'ಮನೆ', difficulty: 'easy', picture_url: '/images/exercises/house.jpg' },
      { id: 4, picture_name: 'Dog', target_text: 'ನಾಯಿ', difficulty: 'easy', picture_url: '/images/exercises/dog.jpg' },
      { id: 5, picture_name: 'Car', target_text: 'ಕಾರು', difficulty: 'easy', picture_url: '/images/exercises/car.jpg' },
      { id: 6, picture_name: 'Book', target_text: 'ಪುಸ್ತಕ', difficulty: 'easy', picture_url: '/images/exercises/book.jpg' },
      { id: 7, picture_name: 'Chair', target_text: 'ಕುರ್ಚಿ', difficulty: 'medium', picture_url: '/images/exercises/chair.jpg' },
      { id: 8, picture_name: 'Table', target_text: 'ಮೇಜು', difficulty: 'medium', picture_url: '/images/exercises/table.jpg' },
      { id: 9, picture_name: 'Flower', target_text: 'ಹೂವು', difficulty: 'medium', picture_url: '/images/exercises/flower.jpg' },
      { id: 10, picture_name: 'Tree', target_text: 'ಮರ', difficulty: 'medium', picture_url: '/images/exercises/tree.jpg' },
    ]
  };

  useEffect(() => {
    setExercises(mockExercises[language] || mockExercises.en);
    setCurrentIndex(0);
    resetExercise();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [language, difficulty]);

  const resetExercise = () => {
    setHasPlayedWord(false);
    setIsPlayingWord(false);
    setIsRecording(false);
    setAudioBlob(null);
    setResult(null);
    setShowResult(false);
  };

  // Step 1: Play the word (TTS)
  const playWord = async () => {
    if (!exercises[currentIndex]) return;
    
    setIsPlayingWord(true);
    const targetText = exercises[currentIndex].target_text;
    
    try {
      // Generate TTS audio for the target word
      const ttsUrl = `${API_BASE_URL}/api/tts?text=${encodeURIComponent(targetText)}&language=${language}`;
      
      if (wordAudioRef.current) {
        wordAudioRef.current.src = ttsUrl;
        wordAudioRef.current.onended = () => {
          setIsPlayingWord(false);
          setHasPlayedWord(true);
        };
        wordAudioRef.current.onerror = () => {
          setIsPlayingWord(false);
          setHasPlayedWord(true);
          console.error('Error playing word audio');
        };
        await wordAudioRef.current.play();
      }
    } catch (error) {
      console.error('Error playing word:', error);
      setIsPlayingWord(false);
      setHasPlayedWord(true);
    }
  };

  // Step 2: Start recording patient's speech
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        setAudioBlob(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert('Could not access microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // Step 3: Process audio and get feedback (same as therapy session)
  const processAudio = async () => {
    if (!audioBlob || !exercises[currentIndex]) {
      console.error('Missing audio or exercise:', { audioBlob: !!audioBlob, exercise: !!exercises[currentIndex] });
      alert('Please record your voice first before submitting.');
      return;
    }

    console.log('🎤 Processing audio for:', exercises[currentIndex].target_text);
    console.log('📦 Audio blob size:', audioBlob.size, 'bytes');
    
    setIsProcessing(true);
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.wav');
    formData.append('target_sentence', exercises[currentIndex].target_text);
    formData.append('language', language);

    try {
      console.log('📤 Sending request to:', `${API_BASE_URL}/api/process-audio`);
      
      // Use the same endpoint as therapy session
      const response = await axios.post(
        `${API_BASE_URL}/api/process-audio`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' }
        }
      );

      console.log('✅ Response received:', response.data);
      setResult(response.data);
      setShowResult(true);
    } catch (error: any) {
      console.error('❌ Error processing audio:', error);
      console.error('Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status
      });
      
      alert(`Error processing audio: ${error.response?.data?.detail || error.message || 'Unknown error'}. Please check console and try again.`);
    } finally {
      setIsProcessing(false);
    }
  };

  // Step 4: Play feedback audio
  const playFeedbackAudio = () => {
    if (result && feedbackAudioRef.current) {
      feedbackAudioRef.current.src = `${API_BASE_URL}${result.feedback_audio_url}`;
      feedbackAudioRef.current.play();
    }
  };

  // Play pronunciation tip using TTS
  const playPronunciationTip = (tip: string) => {
    const utterance = new SpeechSynthesisUtterance(tip);
    utterance.lang = language === 'hi' ? 'hi-IN' : language === 'kn' ? 'kn-IN' : 'en-US';
    utterance.rate = 0.8;
    speechSynthesis.speak(utterance);
  };

  const nextExercise = () => {
    if (currentIndex < exercises.length - 1) {
      setCurrentIndex(currentIndex + 1);
      resetExercise();
    }
  };

  const tryAgain = () => {
    resetExercise();
  };

  if (exercises.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-sky-blue-light via-white to-lilac-light dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 flex items-center justify-center">
        <Loader className="w-12 h-12 animate-spin text-forest dark:text-sage" />
      </div>
    );
  }

  const currentExercise = exercises[currentIndex];

  return (
    <div className="min-h-screen py-8">
      <div className="container mx-auto px-4 max-w-5xl">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card mb-6"
        >
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-3xl font-display font-bold text-gray-900 dark:text-white flex items-center">
              <div className="w-12 h-12 bg-gradient-to-br from-sky-blue to-lilac rounded-xl flex items-center justify-center mr-3">
                <Camera className="w-6 h-6 text-white" />
              </div>
              Picture Therapy Session
            </h1>
            
            {/* Language Selection */}
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="px-4 py-2 border border-gray-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-forest dark:focus:ring-sage"
              disabled={hasPlayedWord}
            >
              <option value="en">🇬🇧 English</option>
              <option value="hi">🇮🇳 Hindi (हिंदी)</option>
              <option value="kn">🇮🇳 Kannada (ಕನ್ನಡ)</option>
            </select>
          </div>

          {/* Progress */}
          <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-2">
            <span className="flex items-center">
              <Target className="w-4 h-4 mr-1" />
              Exercise {currentIndex + 1} of {exercises.length}
            </span>
            <span className="px-3 py-1 bg-sage/20 dark:bg-sage/10 text-forest dark:text-sage-light rounded-full text-xs font-medium">
              {currentExercise?.difficulty}
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-slate-700 rounded-full h-3">
            <div
              className="bg-gradient-to-r from-forest to-sage h-3 rounded-full transition-all duration-500"
              style={{ width: `${((currentIndex + 1) / exercises.length) * 100}%` }}
            />
          </div>
        </motion.div>

        {/* Main Exercise Card */}
        <AnimatePresence mode="wait">
          {!showResult ? (
            <motion.div
              key="exercise"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="card"
            >
              {/* Picture Display */}
              <div className="mb-8">
                <div className="relative bg-gradient-to-br from-sky-blue/10 via-lilac/10 to-sage/10 dark:from-slate-800 dark:via-slate-700 dark:to-slate-800 rounded-2xl p-8 flex items-center justify-center min-h-[450px] border-2 border-sage/20 dark:border-sage/10">
                  <motion.img
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.2 }}
                    src={currentExercise.picture_url}
                    alt={currentExercise.picture_name}
                    className="max-w-full max-h-[400px] rounded-xl shadow-2xl object-contain"
                  />
                  <div className="absolute top-4 right-4 bg-white dark:bg-slate-800 px-3 py-1 rounded-full shadow-lg">
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">📸 {currentExercise.picture_name}</span>
                  </div>
                </div>
              </div>

              {/* Target Word */}
              <div className="text-center mb-8">
                <motion.h2
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                  className="text-5xl font-display font-bold gradient-text mb-3"
                >
                  {currentExercise.target_text}
                </motion.h2>
                <p className="text-gray-500 dark:text-gray-400 text-lg">Say this word clearly</p>
              </div>

            {/* Step-by-step Instructions */}
            <div className="space-y-4">
              {/* Step 1: Listen to the word */}
              {!hasPlayedWord && (
                <div className="text-center">
                  <p className="text-lg text-gray-700 mb-4">
                    👂 Step 1: Listen to the word
                  </p>
                  <button
                    onClick={playWord}
                    disabled={isPlayingWord}
                    className="flex items-center space-x-2 px-8 py-4 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold mx-auto disabled:opacity-50"
                  >
                    {isPlayingWord ? (
                      <>
                        <Volume2 className="w-6 h-6 animate-pulse" />
                        <span>Playing...</span>
                      </>
                    ) : (
                      <>
                        <Play className="w-6 h-6" />
                        <span>Play Word</span>
                      </>
                    )}
                  </button>
                </div>
              )}

              {/* Step 2: Record your speech */}
              {hasPlayedWord && !audioBlob && (
                <div className="text-center">
                  <p className="text-lg text-gray-700 mb-4">
                    🎤 Step 2: Now you say it!
                  </p>
                  <button
                    onClick={isRecording ? stopRecording : startRecording}
                    className={`flex items-center space-x-2 px-8 py-4 rounded-lg font-semibold text-white mx-auto transition-all ${
                      isRecording
                        ? 'bg-red-500 hover:bg-red-600 animate-pulse'
                        : 'bg-indigo-600 hover:bg-indigo-700'
                    }`}
                  >
                    <Mic className="w-6 h-6" />
                    <span>{isRecording ? 'Stop Recording' : 'Start Recording'}</span>
                  </button>
                </div>
              )}

              {/* Step 3: Submit for feedback */}
              {audioBlob && (
                <div className="text-center">
                  <p className="text-lg text-gray-700 mb-4">
                    ✅ Step 3: Get your feedback
                  </p>
                  <div className="flex justify-center space-x-4">
                    <button
                      onClick={processAudio}
                      disabled={isProcessing}
                      className="flex items-center space-x-2 px-8 py-4 bg-green-600 hover:bg-green-700 text-white rounded-lg font-semibold disabled:opacity-50"
                    >
                      {isProcessing ? (
                        <>
                          <Loader className="w-6 h-6 animate-spin" />
                          <span>Processing...</span>
                        </>
                      ) : (
                        <>
                          <CheckCircle className="w-6 h-6" />
                          <span>Submit</span>
                        </>
                      )}
                    </button>
                    <button
                      onClick={tryAgain}
                      className="flex items-center space-x-2 px-8 py-4 bg-gray-500 hover:bg-gray-600 text-white rounded-lg font-semibold"
                    >
                      <XCircle className="w-6 h-6" />
                      <span>Record Again</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        ) : (
          /* Results Display */
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl p-8 space-y-6"
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                <CheckCircle className="w-7 h-7 text-green-500" />
                Your Results
              </h2>
            </div>

            {/* Accuracy Score */}
            <div className="p-6 bg-gradient-to-r from-green-50 to-blue-50 dark:from-green-900/20 dark:to-blue-900/20 rounded-xl">
              <div className="flex items-center justify-between mb-3">
                <span className="text-gray-700 dark:text-gray-300 font-medium">Accuracy Score</span>
                <span className={`text-3xl font-bold ${
                  result!.accuracy >= 80 ? 'text-green-600 dark:text-green-400' :
                  result!.accuracy >= 60 ? 'text-yellow-600 dark:text-yellow-400' :
                  'text-red-600 dark:text-red-400'
                }`}>
                  {result!.accuracy.toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                <div
                  className={`h-3 rounded-full transition-all duration-500 ${
                    result!.accuracy >= 80
                      ? 'bg-gradient-to-r from-green-500 to-green-600'
                      : result!.accuracy >= 60
                      ? 'bg-gradient-to-r from-yellow-500 to-yellow-600'
                      : 'bg-gradient-to-r from-red-500 to-red-600'
                  }`}
                  style={{ width: `${result!.accuracy}%` }}
                />
              </div>
            </div>

            {/* Transcription */}
            <div className="mb-6 p-4 bg-gray-50 dark:bg-slate-800 rounded-xl">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">You said:</p>
              <p className="text-xl font-semibold text-gray-900 dark:text-white">{result!.transcription}</p>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Target: {currentExercise.target_text}</p>
            </div>

            {/* Feedback with Audio */}
            <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-sm text-blue-800 dark:text-blue-400 font-medium mb-1">Feedback</p>
                  <p className="text-blue-700 dark:text-blue-300 text-lg">{result!.feedback}</p>
                </div>
                <button
                  onClick={playFeedbackAudio}
                  className="ml-4 inline-flex items-center px-3 py-1 text-xs font-medium text-blue-700 bg-blue-100 rounded-full hover:bg-blue-200 dark:bg-blue-800 dark:text-blue-300 dark:hover:bg-blue-700 transition-colors"
                  title="Play feedback audio"
                >
                  <Volume2 className="w-3 h-3 mr-1" />
                  Play Audio
                </button>
              </div>
            </div>

            {/* Word Corrections */}
            {result!.word_corrections && result!.word_corrections.length > 0 && (
              <div className="mb-6 p-4 bg-orange-50 dark:bg-orange-900/20 rounded-xl">
                <h4 className="flex items-center text-sm font-medium text-orange-800 dark:text-orange-400 mb-3">
                  <Target className="w-4 h-4 mr-1" />
                  Word-by-Word Corrections
                </h4>
                <div className="space-y-3">
                  {result!.word_corrections.map((correction: any, index: number) => (
                    <div key={index} className="p-3 bg-white dark:bg-slate-800 rounded-lg border border-orange-200 dark:border-orange-800">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-lg font-semibold text-orange-900 dark:text-orange-100">
                              {correction.word}
                            </span>
                            <span className="text-xs bg-orange-100 dark:bg-orange-800 text-orange-700 dark:text-orange-300 px-2 py-1 rounded-full">
                              Word {index + 1}
                            </span>
                          </div>
                          <p className="text-sm text-orange-700 dark:text-orange-300 mb-1">
                            <strong>Issue:</strong> {correction.issue}
                          </p>
                          <p className="text-sm text-orange-800 dark:text-orange-200 mb-2">
                            <strong>Correction:</strong> {correction.correction}
                          </p>
                          <div className="flex items-center gap-2">
                            <p className="text-xs text-orange-600 dark:text-orange-400 bg-orange-100 dark:bg-orange-900/30 p-2 rounded flex-1">
                              💡 <strong>Tip:</strong> {correction.pronunciation_tip}
                            </p>
                            <button
                              onClick={() => playPronunciationTip(correction.pronunciation_tip)}
                              className="inline-flex items-center px-2 py-1 text-xs font-medium text-orange-700 bg-orange-100 rounded hover:bg-orange-200 dark:bg-orange-800 dark:text-orange-300 dark:hover:bg-orange-700 transition-colors"
                              title="Play tip"
                            >
                              <Volume2 className="w-3 h-3" />
                            </button>
                          </div>
                        </div>
                        <button
                          onClick={() => playPronunciationTip(correction.word)}
                          className="ml-3 inline-flex items-center px-2 py-1 text-xs font-medium text-orange-700 bg-orange-100 rounded hover:bg-orange-200 dark:bg-orange-800 dark:text-orange-300 dark:hover:bg-orange-700 transition-colors"
                        >
                          <Volume2 className="w-3 h-3 mr-1" />
                          Play
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Practice Suggestions */}
            {result!.practice_suggestions && result!.practice_suggestions.length > 0 && (
              <div className="mb-6 p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-xl">
                <h4 className="flex items-center text-sm font-medium text-yellow-800 dark:text-yellow-400 mb-2">
                  <AlertCircle className="w-4 h-4 mr-1" />
                  Practice Tips
                </h4>
                <ul className="text-sm text-yellow-700 dark:text-yellow-300 space-y-1">
                  {result!.practice_suggestions.map((suggestion: string, index: number) => (
                    <li key={index}>• {suggestion}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex justify-center gap-4 pt-4">
              <button
                onClick={tryAgain}
                className="inline-flex items-center px-6 py-3 bg-gray-600 hover:bg-gray-700 dark:bg-gray-700 dark:hover:bg-gray-600 text-white rounded-xl font-semibold transition-all shadow-lg hover:shadow-xl"
              >
                <RefreshCw className="w-5 h-5 mr-2" />
                Try Again
              </button>
              {currentIndex < exercises.length - 1 && (
                <button
                  onClick={nextExercise}
                  className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-xl font-semibold transition-all shadow-lg hover:shadow-xl"
                >
                  Next Exercise
                  <ArrowRight className="w-5 h-5 ml-2" />
                </button>
              )}
            </div>
          </motion.div>
        )}
        </AnimatePresence>

        {/* Hidden audio elements */}
        <audio ref={wordAudioRef} className="hidden" />
        <audio ref={feedbackAudioRef} className="hidden" />
      </div>
    </div>
  );
};

export default PictureTherapy;
