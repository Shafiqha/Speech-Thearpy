import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Camera, Mic, Volume2, CheckCircle, XCircle, ArrowRight, Loader, Play, Sparkles, Target, Award } from 'lucide-react';
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
  feedback_audio_url?: string;
  word_corrections?: any[];
  practice_suggestions?: string[];
}

const PictureTherapy: React.FC = () => {
  const [language, setLanguage] = useState('en');
  const [difficulty, setDifficulty] = useState('easy');
  const [exercises, setExercises] = useState<PictureExercise[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState<FeedbackResult | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [hasPlayedWord, setHasPlayedWord] = useState(false);
  const [isPlayingWord, setIsPlayingWord] = useState(false);

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
  }, [language, difficulty]);

  const resetExercise = () => {
    setAudioBlob(null);
    setResult(null);
    setShowResult(false);
    setHasPlayedWord(false);
    setIsPlayingWord(false);
  };

  const playWord = async () => {
    setIsPlayingWord(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/api/tts`, {
        text: exercises[currentIndex].target_text,
        language: language
      }, { responseType: 'blob' });

      const audioUrl = URL.createObjectURL(response.data);
      const audio = new Audio(audioUrl);
      audio.onended = () => {
        setIsPlayingWord(false);
        setHasPlayedWord(true);
      };
      audio.play();
    } catch (error) {
      console.error('Error playing word:', error);
      setIsPlayingWord(false);
      setHasPlayedWord(true);
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
        setAudioBlob(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Could not access microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const processAudio = async () => {
    if (!audioBlob) return;

    setIsProcessing(true);
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.wav');
    formData.append('target_text', exercises[currentIndex].target_text);
    formData.append('language', language);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/practice/feedback`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setResult(response.data);
      setShowResult(true);
    } catch (error) {
      console.error('Error processing audio:', error);
      alert('Error processing your recording. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const playFeedbackAudio = () => {
    if (result?.feedback_audio_url && feedbackAudioRef.current) {
      feedbackAudioRef.current.src = `${API_BASE_URL}${result.feedback_audio_url}`;
      feedbackAudioRef.current.play();
    }
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

        {/* Main Content */}
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
              <div className="space-y-6">
                {/* Step 1: Listen */}
                {!hasPlayedWord && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                    className="text-center"
                  >
                    <div className="inline-flex items-center px-4 py-2 bg-sky-blue/20 dark:bg-sky-blue/10 rounded-full mb-4">
                      <span className="text-2xl mr-2">👂</span>
                      <span className="text-lg font-medium text-gray-700 dark:text-gray-300">Step 1: Listen to the word</span>
                    </div>
                    <button
                      onClick={playWord}
                      disabled={isPlayingWord}
                      className="btn-primary inline-flex items-center space-x-2 px-8 py-4 disabled:opacity-50"
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
                  </motion.div>
                )}

                {/* Step 2: Record */}
                {hasPlayedWord && !audioBlob && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-center"
                  >
                    <div className="inline-flex items-center px-4 py-2 bg-lilac/20 dark:bg-lilac/10 rounded-full mb-4">
                      <span className="text-2xl mr-2">🎤</span>
                      <span className="text-lg font-medium text-gray-700 dark:text-gray-300">Step 2: Now you say it!</span>
                    </div>
                    <button
                      onClick={isRecording ? stopRecording : startRecording}
                      className={`inline-flex items-center space-x-2 px-8 py-4 rounded-xl font-semibold text-white transition-all shadow-lg ${
                        isRecording
                          ? 'bg-red-500 hover:bg-red-600 animate-pulse'
                          : 'bg-gradient-to-r from-forest to-sage hover:from-forest-dark hover:to-sage-dark'
                      }`}
                    >
                      <Mic className="w-6 h-6" />
                      <span>{isRecording ? 'Stop Recording' : 'Start Recording'}</span>
                    </button>
                  </motion.div>
                )}

                {/* Step 3: Submit */}
                {audioBlob && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-center"
                  >
                    <div className="inline-flex items-center px-4 py-2 bg-sage/20 dark:bg-sage/10 rounded-full mb-4">
                      <span className="text-2xl mr-2">✅</span>
                      <span className="text-lg font-medium text-gray-700 dark:text-gray-300">Step 3: Get your feedback</span>
                    </div>
                    <div className="flex justify-center space-x-4">
                      <button
                        onClick={processAudio}
                        disabled={isProcessing}
                        className="btn-primary inline-flex items-center space-x-2 px-8 py-4 disabled:opacity-50"
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
                        className="btn-secondary inline-flex items-center space-x-2 px-8 py-4"
                      >
                        <XCircle className="w-6 h-6" />
                        <span>Record Again</span>
                      </button>
                    </div>
                  </motion.div>
                )}
              </div>
            </motion.div>
          ) : (
            /* Results Display */
            <motion.div
              key="results"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="card"
            >
              <div className="flex items-center mb-6">
                <div className="w-12 h-12 bg-gradient-to-br from-sage to-forest rounded-xl flex items-center justify-center mr-3">
                  <Award className="w-6 h-6 text-white" />
                </div>
                <h2 className="text-2xl font-display font-bold text-gray-900 dark:text-white">Your Results</h2>
              </div>

              {/* Accuracy Score */}
              <div className="mb-6 p-6 bg-gradient-to-br from-sage/10 to-forest/10 dark:from-sage/5 dark:to-forest/5 rounded-xl">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-gray-700 dark:text-gray-300 font-medium flex items-center">
                    <Target className="w-5 h-5 mr-2" />
                    Accuracy Score
                  </span>
                  <span className="text-3xl font-bold gradient-text">
                    {result!.accuracy.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-slate-700 rounded-full h-4">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${result!.accuracy}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    className={`h-4 rounded-full ${
                      result!.accuracy >= 80
                        ? 'bg-gradient-to-r from-green-500 to-green-600'
                        : result!.accuracy >= 60
                        ? 'bg-gradient-to-r from-yellow-500 to-yellow-600'
                        : 'bg-gradient-to-r from-red-500 to-red-600'
                    }`}
                  />
                </div>
              </div>

              {/* Transcription */}
              <div className="mb-6 p-5 bg-sky-blue/10 dark:bg-slate-800 rounded-xl border border-sky-blue/20 dark:border-slate-700">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2 font-medium">You said:</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white mb-3">{result!.transcription}</p>
                <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                  <Sparkles className="w-4 h-4 mr-1" />
                  <span>Target: <span className="font-medium text-forest dark:text-sage">{currentExercise.target_text}</span></span>
                </div>
              </div>

              {/* Feedback */}
              <div className="mb-6 p-5 bg-lilac/10 dark:bg-slate-800 rounded-xl border border-lilac/20 dark:border-slate-700">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="text-sm text-forest dark:text-sage font-semibold mb-2 flex items-center">
                      <Sparkles className="w-4 h-4 mr-1" />
                      Feedback
                    </p>
                    <p className="text-gray-800 dark:text-gray-200 text-lg leading-relaxed">{result!.feedback}</p>
                  </div>
                  <button
                    onClick={playFeedbackAudio}
                    className="ml-4 p-3 bg-gradient-to-br from-forest to-sage hover:from-forest-dark hover:to-sage-dark text-white rounded-xl shadow-lg transition-all"
                    title="Play feedback audio"
                  >
                    <Volume2 className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex space-x-4">
                <button
                  onClick={tryAgain}
                  className="flex-1 btn-secondary inline-flex items-center justify-center space-x-2"
                >
                  <XCircle className="w-5 h-5" />
                  <span>Try Again</span>
                </button>
                {currentIndex < exercises.length - 1 && (
                  <button
                    onClick={nextExercise}
                    className="flex-1 btn-primary inline-flex items-center justify-center space-x-2"
                  >
                    <span>Next Exercise</span>
                    <ArrowRight className="w-5 h-5" />
                  </button>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Hidden Audio Elements */}
        <audio ref={wordAudioRef} />
        <audio ref={feedbackAudioRef} />
      </div>
    </div>
  );
};

export default PictureTherapy;
