import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  Mic,
  MicOff,
  Volume2,
  ChevronRight,
  RefreshCw,
  Check,
  AlertCircle,
  Target,
  Award,
  Brain,
  Sparkles,
  Loader2,
  Globe
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { sessionAPI } from '../services/api';

interface Sentence {
  id: string;
  text: string;
  language: string;
  difficulty: 'easy' | 'medium' | 'hard';
  category: string;
  targetWords: string[];
}

interface WordCorrection {
  word: string;
  position: number;
  issue: string;
  correction: string;
  pronunciation_tip: string;
}

interface SessionResult {
  transcription: string;
  accuracy: number;
  wab_score: number;
  severity: string;
  feedback: string;
  detailed_errors: string[];
  practice_suggestions: string[];
  feedback_audio_url?: string; // New TTS feedback URL
  word_corrections?: WordCorrection[]; // Detailed word-level corrections
}

const TherapySession: React.FC = () => {
  const { user } = useAuth();
  const { language: contextLanguage, setLanguage } = useLanguage();
  const navigate = useNavigate();
  
  // Session State
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionLanguage, setSessionLanguage] = useState(contextLanguage);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isLoadingSentences, setIsLoadingSentences] = useState(false);
  const [currentSentence, setCurrentSentence] = useState<Sentence | null>(null);
  const [sessionResult, setSessionResult] = useState<SessionResult | null>(null);
  const [availableSentences, setAvailableSentences] = useState<Sentence[]>([]);
  const [sentenceIndex, setSentenceIndex] = useState(0);
  
  // Progress tracking
  const [sessionProgress, setSessionProgress] = useState({
    current: 1,
    total: 10,
    completed: 0,
    accuracy: 0,
    totalWabScore: 0
  });
  
  // Adaptive difficulty based on WAB-AQ score
  const [currentDifficulty, setCurrentDifficulty] = useState<'easy' | 'medium' | 'hard'>('easy');
  const [userWabScore, setUserWabScore] = useState(user?.wabScore || 50);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Language options
  const languageOptions = [
    { code: 'en', name: 'English', flag: '🇬🇧' },
    { code: 'hi', name: 'हिंदी', flag: '🇮🇳' },
    { code: 'kn', name: 'ಕನ್ನಡ', flag: '🇮🇳' }
  ];

  // Initialize session on component mount
  useEffect(() => {
    initializeSession();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Load sentences when language or difficulty changes
  useEffect(() => {
    if (sessionId) {
      console.log(`🔄 Loading sentences for ${sessionLanguage}/${currentDifficulty}`);
      loadSentencesFromAPI();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionLanguage, currentDifficulty, sessionId]);

  // Determine difficulty based on WAB-AQ score (like interactive_therapy.py)
  const getDifficultyFromWabScore = (wabScore: number): 'easy' | 'medium' | 'hard' => {
    if (wabScore >= 76) return 'hard';    // Mild aphasia
    if (wabScore >= 51) return 'medium';  // Moderate aphasia  
    return 'easy';                        // Severe/Very severe aphasia
  };

  const initializeSession = async () => {
    try {
      // Start session with backend - backend will determine difficulty from database
      const response = await sessionAPI.startSession(
        sessionLanguage, 
        currentDifficulty,  // Use current difficulty (will be overridden by backend if needed)
        user?.id
      );
      setSessionId(response.session_id);
      
      // ALWAYS use the difficulty returned by backend (it reads from database)
      if (response.current_difficulty) {
        setCurrentDifficulty(response.current_difficulty as 'easy' | 'medium' | 'hard');
        console.log(`📊 Backend set difficulty to: ${response.current_difficulty}`);
      }
      
      // Log progress information
      if (response.progress) {
        console.log(`📈 User progress:`, response.progress);
        console.log(`   Easy: ${response.progress.easy}, Medium: ${response.progress.medium}, Hard: ${response.progress.hard}`);
      }
      
      console.log(`🎯 Session started: ${response.session_id}`);
      console.log(`📊 Difficulty: ${response.current_difficulty} (WAB-AQ: ${userWabScore})`);
    } catch (error) {
      console.error('Failed to initialize session:', error);
      // Fallback to offline mode
      setSessionId('offline-session');
    }
  };

  const loadSentencesFromAPI = async (difficultyOverride?: 'easy' | 'medium' | 'hard') => {
    setIsLoadingSentences(true);
    const difficultyToUse = difficultyOverride || currentDifficulty;
    try {
      const response = await sessionAPI.getSentences(
        sessionLanguage, 
        difficultyToUse, 
        sessionProgress.total
      );
      
      setAvailableSentences(response.sentences);
      setSentenceIndex(0);
      
      if (response.sentences.length > 0) {
        setCurrentSentence(response.sentences[0]);
      }
      
      console.log(`📚 Loaded ${response.sentences.length} sentences for ${sessionLanguage}/${difficultyToUse}`);
    } catch (error) {
      console.error('Failed to load sentences:', error);
      // Fallback to mock data
      loadFallbackSentences();
    } finally {
      setIsLoadingSentences(false);
    }
  };

  const loadFallbackSentences = () => {
    const mockSentences = {
      easy: [
        { id: '1', text: 'Hello', language: sessionLanguage, difficulty: 'easy' as const, category: 'greeting', targetWords: ['Hello'] },
        { id: '2', text: 'Water', language: sessionLanguage, difficulty: 'easy' as const, category: 'basic', targetWords: ['Water'] }
      ],
      medium: [
        { id: '3', text: 'I am hungry', language: sessionLanguage, difficulty: 'medium' as const, category: 'feeling', targetWords: ['hungry'] }
      ],
      hard: [
        { id: '4', text: 'I need medical assistance', language: sessionLanguage, difficulty: 'hard' as const, category: 'medical', targetWords: ['medical', 'assistance'] }
      ]
    };
    
    setAvailableSentences(mockSentences[currentDifficulty] || []);
    if (mockSentences[currentDifficulty]?.length > 0) {
      setCurrentSentence(mockSentences[currentDifficulty][0]);
    }
  };

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
        processAudio(audioBlob);
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert('Please allow microphone access to use speech therapy.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      setIsRecording(false);
    }
  };

  const processAudio = async (blob: Blob) => {
    if (!currentSentence || !sessionId) {
      console.error('Missing sentence or session ID');
      return;
    }
    
    console.log('🎤 Processing audio...');
    console.log('📦 Audio blob size:', blob.size, 'bytes');
    console.log('🎯 Target sentence:', currentSentence.text);
    console.log('🌍 Language:', sessionLanguage);
    
    setIsProcessing(true);
    
    try {
      // Send audio to backend API for real processing
      const result = await sessionAPI.processAudio(
        blob,
        currentSentence.text,
        sessionLanguage,
        sessionId
      );
      
      console.log('✅ Backend response:', result);
      console.log('📝 Transcription:', result.transcription);
      console.log('📊 Accuracy:', result.accuracy);
      console.log('💬 Feedback:', result.feedback);
      
      setSessionResult(result);
      
      // Update progress and WAB score
      const newWabScore = result.wab_score;
      setUserWabScore(newWabScore);
      
      setSessionProgress(prev => ({
        ...prev,
        completed: prev.completed + 1,
        accuracy: (prev.accuracy * prev.completed + result.accuracy) / (prev.completed + 1),
        totalWabScore: prev.totalWabScore + newWabScore
      }));
      
      // Adaptive difficulty adjustment based on performance
      const avgWabScore = (sessionProgress.totalWabScore + newWabScore) / (sessionProgress.completed + 1);
      const newDifficulty = getDifficultyFromWabScore(avgWabScore);
      
      if (newDifficulty !== currentDifficulty) {
        console.log(`🔄 Adjusting difficulty: ${currentDifficulty} → ${newDifficulty} (WAB-AQ: ${avgWabScore})`);
        setCurrentDifficulty(newDifficulty);
      }
      
      console.log(`📊 Session result: ${result.accuracy}% accuracy, WAB-AQ: ${newWabScore}, Severity: ${result.severity}`);
      
    } catch (error) {
      console.error('Error processing audio:', error);
      
      // Show actual error to user - DO NOT use fake high scores
      const errorResult: SessionResult = {
        transcription: '[Error processing audio]',
        accuracy: 0,
        wab_score: 0,
        severity: 'Unable to assess',
        feedback: 'Error processing audio. Please check your microphone and try again.',
        detailed_errors: ['Audio processing failed', 'Please ensure microphone is working'],
        practice_suggestions: ['Check microphone permissions', 'Try recording again']
      };
      setSessionResult(errorResult);
      
      // Show alert to user
      alert('Error processing audio. Please check your microphone and internet connection, then try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const playExample = async () => {
    if (!currentSentence) return;
    
    try {
      // Use backend TTS API
      await sessionAPI.textToSpeech(currentSentence.text, sessionLanguage);
    } catch (error) {
      console.error('Error with TTS API, falling back to browser TTS:', error);
      // Fallback to browser TTS
      const utterance = new SpeechSynthesisUtterance(currentSentence.text);
      utterance.lang = sessionLanguage === 'hi' ? 'hi-IN' : sessionLanguage === 'kn' ? 'kn-IN' : 'en-US';
      utterance.rate = 0.8;
      speechSynthesis.speak(utterance);
    }
  };

  const nextSentence = async () => {
    if (sessionProgress.current < sessionProgress.total) {
      setSessionProgress(prev => ({ ...prev, current: prev.current + 1 }));
      
      // Load next sentence from available sentences
      const nextIndex = sentenceIndex + 1;
      if (nextIndex < availableSentences.length) {
        setSentenceIndex(nextIndex);
        setCurrentSentence(availableSentences[nextIndex]);
      } else {
        // Reload sentences if we've run out
        loadSentencesFromAPI();
      }
      
      setSessionResult(null);
    } else {
      // Session complete - call backend to finalize
      try {
        if (sessionId) {
          const completionResult = await sessionAPI.completeSession(sessionId);
          console.log('✅ Session completed:', completionResult);
          
          // Check if user progressed to next difficulty
          if (completionResult.next_difficulty && completionResult.next_difficulty !== currentDifficulty) {
            // Show progression message
            const message = completionResult.progression_message || 
              `Congratulations! You've progressed to ${completionResult.next_difficulty} difficulty!`;
            
            // Show modal/alert with progression message
            if (window.confirm(`${message}\n\nWould you like to start a new session at ${completionResult.next_difficulty} difficulty?`)) {
              console.log(`🎉 User accepted progression to ${completionResult.next_difficulty}`);
              
              // Update difficulty state FIRST
              const newDifficulty = completionResult.next_difficulty as 'easy' | 'medium' | 'hard';
              setCurrentDifficulty(newDifficulty);
              
              // Reset progress for new session
              setSessionProgress({
                current: 1,
                total: 10,
                completed: 0,
                accuracy: 0,
                totalWabScore: 0
              });
              
              // Clear current sentence and result
              setCurrentSentence(null);
              setSessionResult(null);
              
              // Wait a moment for database commit to complete
              console.log(`⏳ Waiting for database update...`);
              await new Promise(resolve => setTimeout(resolve, 500));
              
              // Initialize new session - backend will read updated difficulty from database
              console.log(`🔄 Initializing new session at ${newDifficulty}...`);
              await initializeSession();
              
              // Verify the difficulty was set correctly
              console.log(`🔍 Current difficulty after init: ${currentDifficulty}`);
              
              // Load sentences for new difficulty (pass explicitly to avoid state timing issues)
              console.log(`📚 Loading sentences for ${newDifficulty} difficulty...`);
              await loadSentencesFromAPI(newDifficulty);
              
              console.log(`✅ New session ready at ${newDifficulty} difficulty!`);
              
              return; // Don't navigate away
            }
          } else if (completionResult.progression_message) {
            // Show encouragement message
            alert(completionResult.progression_message);
          }
        }
      } catch (error) {
        console.error('Error completing session:', error);
      }
      
      // Navigate to dashboard
      navigate('/patient/dashboard');
    }
  };

  const changeLanguage = (newLanguage: 'en' | 'hi' | 'kn') => {
    setSessionLanguage(newLanguage);
    setLanguage(newLanguage);
    console.log(`🌍 Language changed to: ${newLanguage}`);
  };

  const getAccuracyColor = (accuracy: number) => {
    if (accuracy >= 90) return 'text-green-600';
    if (accuracy >= 70) return 'text-yellow-600';
    if (accuracy >= 50) return 'text-orange-600';
    return 'text-red-600';
  };

  const getAccuracyLabel = (accuracy: number) => {
    if (accuracy >= 90) return 'Excellent';
    if (accuracy >= 70) return 'Good';
    if (accuracy >= 50) return 'Fair';
    return 'Needs Work';
  };

  const playFeedbackAudio = async (feedbackAudioUrl: string) => {
    try {
      // Create full URL for the TTS endpoint
      const fullUrl = `http://localhost:8000${feedbackAudioUrl}`;
      
      // Create and play audio
      const audio = new Audio(fullUrl);
      await audio.play();
    } catch (error) {
      console.error('Error playing feedback audio:', error);
      
      // Fallback: use the feedback text with browser TTS
      if (sessionResult?.feedback) {
        const utterance = new SpeechSynthesisUtterance(sessionResult.feedback);
        utterance.lang = sessionLanguage === 'hi' ? 'hi-IN' : sessionLanguage === 'kn' ? 'kn-IN' : 'en-US';
        utterance.rate = 0.8;
        speechSynthesis.speak(utterance);
      }
    }
  };

  const playWordPronunciation = async (word: string) => {
    try {
      // Use backend TTS API for individual word pronunciation
      await sessionAPI.textToSpeech(word, sessionLanguage);
    } catch (error) {
      console.error('Error playing word pronunciation:', error);
      
      // Fallback to browser TTS
      const utterance = new SpeechSynthesisUtterance(word);
      utterance.lang = sessionLanguage === 'hi' ? 'hi-IN' : sessionLanguage === 'kn' ? 'kn-IN' : 'en-US';
      utterance.rate = 0.7; // Slower for learning
      speechSynthesis.speak(utterance);
    }
  };

  if (isLoadingSentences) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin mx-auto mb-4 text-sky-blue" />
          <p className="text-gray-600 dark:text-gray-400">Loading therapy content...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-8">
      <div className="container mx-auto px-4 max-w-4xl">
        {/* Header with Language Selection */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-3xl font-display font-bold text-gray-900 dark:text-white">
              Speech Therapy Session
            </h2>
            
            {/* Language Selector */}
            <div className="flex items-center space-x-2">
              <Globe className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              <select
                value={sessionLanguage}
                onChange={(e) => changeLanguage(e.target.value as 'en' | 'hi' | 'kn')}
                className="px-3 py-2 rounded-xl border border-gray-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-gray-900 dark:text-gray-100"
              >
                {languageOptions.map((lang) => (
                  <option key={lang.code} value={lang.code}>
                    {lang.flag} {lang.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
          
          {/* Progress Bar */}
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600 dark:text-gray-400">
              Progress: {sessionProgress.current} / {sessionProgress.total} sentences
            </span>
            <span className="text-sm font-medium text-forest dark:text-sage">
              Difficulty: {currentDifficulty} (WAB-AQ: {userWabScore})
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-slate-700 rounded-full h-3">
            <motion.div
              className="bg-gradient-to-r from-sky-blue to-lilac h-3 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${(sessionProgress.completed / sessionProgress.total) * 100}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </div>

        {/* Main Session Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card"
        >
          {currentSentence && (
            <>
              {/* Sentence Display */}
              <div className="text-center mb-8">
                <div className="inline-flex items-center space-x-2 px-3 py-1 bg-sage/20 dark:bg-sage/10 rounded-full mb-4">
                  <Target className="w-4 h-4 text-forest dark:text-sage" />
                  <span className="text-sm font-medium text-forest dark:text-sage">
                    {currentSentence.category}
                  </span>
                </div>
                
                <h3 className="text-3xl font-display font-bold text-gray-900 dark:text-white mb-4">
                  "{currentSentence.text}"
                </h3>
                
                <div className="flex items-center justify-center space-x-2">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Target words:</span>
                  <div className="flex flex-wrap gap-2">
                    {currentSentence.targetWords.map((word, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-sky-blue/20 dark:bg-sky-blue/10 text-forest dark:text-sky-blue rounded text-sm font-medium"
                      >
                        {word}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Recording Controls */}
              <div className="flex items-center justify-center space-x-4 mb-8">
                <button
                  onClick={playExample}
                  className="p-4 bg-gray-100 dark:bg-slate-700 rounded-xl hover:bg-gray-200 dark:hover:bg-slate-600 transition-colors"
                  disabled={isRecording || isProcessing}
                >
                  <Volume2 className="w-6 h-6 text-gray-700 dark:text-gray-300" />
                </button>
                
                <motion.button
                  whileTap={{ scale: 0.95 }}
                  onClick={isRecording ? stopRecording : startRecording}
                  disabled={isProcessing}
                  className={`p-6 rounded-full transition-all ${
                    isRecording
                      ? 'bg-red-500 hover:bg-red-600 animate-pulse'
                      : 'bg-gradient-to-r from-sky-blue to-lilac hover:from-sky-blue-dark hover:to-lilac-dark'
                  }`}
                >
                  {isRecording ? (
                    <MicOff className="w-8 h-8 text-white" />
                  ) : (
                    <Mic className="w-8 h-8 text-white" />
                  )}
                </motion.button>
                
                <button
                  onClick={() => loadSentencesFromAPI()}
                  className="p-4 bg-gray-100 dark:bg-slate-700 rounded-xl hover:bg-gray-200 dark:hover:bg-slate-600 transition-colors"
                  disabled={isRecording || isProcessing}
                >
                  <RefreshCw className="w-6 h-6 text-gray-700 dark:text-gray-300" />
                </button>
              </div>

              {/* Status Messages */}
              <AnimatePresence>
                {isRecording && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="text-center mb-6"
                  >
                    <div className="inline-flex items-center space-x-2 text-red-600 dark:text-red-400">
                      <div className="w-2 h-2 bg-red-600 dark:bg-red-400 rounded-full animate-pulse" />
                      <span className="font-medium">Recording... Speak clearly!</span>
                    </div>
                  </motion.div>
                )}
                
                {isProcessing && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="text-center mb-6"
                  >
                    <div className="inline-flex items-center space-x-2 text-blue-600 dark:text-blue-400">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span className="font-medium">Processing your speech...</span>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Results Display */}
              {sessionResult && !isProcessing && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="space-y-6"
                >
                  {/* Accuracy Score */}
                  <div className="text-center">
                    <div className="inline-flex items-center justify-center w-32 h-32 rounded-full bg-gradient-to-br from-sky-blue/20 to-lilac/20 dark:from-sky-blue/10 dark:to-lilac/10 mb-4">
                      <div className="text-center">
                        <div className={`text-4xl font-bold ${getAccuracyColor(sessionResult.accuracy)}`}>
                          {Math.round(sessionResult.accuracy)}%
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          {getAccuracyLabel(sessionResult.accuracy)}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Transcription */}
                  <div className="p-4 bg-gray-50 dark:bg-slate-700/50 rounded-xl">
                    <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                      You said:
                    </h4>
                    <p className="text-lg text-gray-900 dark:text-white">
                      "{sessionResult.transcription}"
                    </p>
                  </div>

                  {/* Main Feedback with TTS */}
                  {sessionResult.feedback && (
                    <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="text-sm font-medium text-blue-800 dark:text-blue-400">
                          Feedback
                        </h4>
                        {sessionResult.feedback_audio_url && (
                          <button
                            onClick={() => playFeedbackAudio(sessionResult.feedback_audio_url!)}
                            className="inline-flex items-center px-3 py-1 text-xs font-medium text-blue-700 bg-blue-100 rounded-full hover:bg-blue-200 dark:bg-blue-800 dark:text-blue-300 dark:hover:bg-blue-700 transition-colors"
                          >
                            <Volume2 className="w-3 h-3 mr-1" />
                            Play Audio
                          </button>
                        )}
                      </div>
                      <p className="text-sm text-blue-700 dark:text-blue-300">
                        {sessionResult.feedback}
                      </p>
                    </div>
                  )}

                  {/* Word-Level Corrections */}
                  {sessionResult.word_corrections && sessionResult.word_corrections.length > 0 && (
                    <div className="p-4 bg-orange-50 dark:bg-orange-900/20 rounded-xl">
                      <h4 className="flex items-center text-sm font-medium text-orange-800 dark:text-orange-400 mb-3">
                        <Target className="w-4 h-4 mr-1" />
                        Word-by-Word Corrections
                      </h4>
                      <div className="space-y-3">
                        {sessionResult.word_corrections.map((correction, index) => (
                          <div key={index} className="p-3 bg-white dark:bg-slate-800 rounded-lg border border-orange-200 dark:border-orange-800">
                            <div className="flex items-start justify-between mb-2">
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="text-lg font-semibold text-orange-900 dark:text-orange-100">
                                    {correction.word}
                                  </span>
                                  <span className="text-xs bg-orange-100 dark:bg-orange-800 text-orange-700 dark:text-orange-300 px-2 py-1 rounded-full">
                                    Word {correction.position + 1}
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
                                    onClick={() => playWordPronunciation(correction.pronunciation_tip)}
                                    className="inline-flex items-center px-2 py-1 text-xs font-medium text-orange-700 bg-orange-100 rounded hover:bg-orange-200 dark:bg-orange-800 dark:text-orange-300 dark:hover:bg-orange-700 transition-colors"
                                    title="Play tip"
                                  >
                                    <Volume2 className="w-3 h-3" />
                                  </button>
                                </div>
                              </div>
                              <button
                                onClick={() => playWordPronunciation(correction.word)}
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

                  {/* Detailed Feedback */}
                  <div className="grid md:grid-cols-2 gap-4">
                    <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-xl">
                      <h4 className="flex items-center text-sm font-medium text-green-800 dark:text-green-400 mb-2">
                        <Check className="w-4 h-4 mr-1" />
                        Strengths
                      </h4>
                      <ul className="text-sm text-green-700 dark:text-green-300 space-y-1">
                        {sessionResult.detailed_errors.slice(0, 2).map((item: string, index: number) => (
                          <li key={index}>• {item}</li>
                        ))}
                      </ul>
                    </div>
                    
                    <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-xl">
                      <h4 className="flex items-center text-sm font-medium text-yellow-800 dark:text-yellow-400 mb-2">
                        <AlertCircle className="w-4 h-4 mr-1" />
                        Practice Tips
                      </h4>
                      <ul className="text-sm text-yellow-700 dark:text-yellow-300 space-y-1">
                        {sessionResult.practice_suggestions.map((tip: string, index: number) => (
                          <li key={index}>• {tip}</li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Severity Info */}
                  <div className="flex items-center justify-between p-4 bg-gradient-to-r from-sage/10 to-forest/10 rounded-xl">
                    <div className="flex items-center space-x-3">
                      <Brain className="w-5 h-5 text-forest dark:text-sage" />
                      <div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">WAB-AQ Score</div>
                        <div className="text-lg font-semibold text-gray-900 dark:text-white">
                          {Math.round(sessionResult.wab_score)}
                        </div>
                      </div>
                    </div>
                    <div className="px-3 py-1 bg-white dark:bg-slate-800 rounded-full">
                      <span className="text-sm font-medium text-forest dark:text-sage">
                        {sessionResult.severity}
                      </span>
                    </div>
                  </div>

                  {/* Next Button */}
                  <div className="flex justify-center">
                    <button
                      onClick={nextSentence}
                      className="btn-primary inline-flex items-center"
                    >
                      {sessionProgress.current < sessionProgress.total ? (
                        <>
                          Next Sentence
                          <ChevronRight className="w-5 h-5 ml-2" />
                        </>
                      ) : (
                        <>
                          <Award className="w-5 h-5 mr-2" />
                          Complete Session
                        </>
                      )}
                    </button>
                  </div>
                </motion.div>
              )}
            </>
          )}
        </motion.div>

        {/* Session Summary (if completed) */}
        {sessionProgress.completed === sessionProgress.total && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mt-8 card bg-gradient-to-br from-sky-blue/20 to-lilac/20 dark:from-sky-blue/10 dark:to-lilac/10 text-center"
          >
            <Sparkles className="w-12 h-12 mx-auto mb-4 text-forest dark:text-sage" />
            <h3 className="text-2xl font-bold mb-2 gradient-text">Session Complete!</h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Great job! You completed {sessionProgress.total} sentences with an average accuracy of {Math.round(sessionProgress.accuracy)}%
            </p>
            <button
              onClick={() => navigate('/patient/dashboard')}
              className="btn-primary inline-flex items-center"
            >
              Back to Dashboard
              <ChevronRight className="w-5 h-5 ml-2" />
            </button>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default TherapySession;
