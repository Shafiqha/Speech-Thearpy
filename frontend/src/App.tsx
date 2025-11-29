import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';

// Pages
import LandingPage from './pages/LandingPage';
import PatientDashboard from './pages/PatientDashboard';
import TherapySession from './pages/TherapySession';
import PictureTherapy from './pages/PictureTherapy';
import LipAnimationExercise from './pages/LipAnimationExercise';
import About from './pages/About';
import Contact from './pages/Contact';
import Login from './pages/Login';
import Register from './pages/Register';

// Components
import Header from './components/Header';
import LoadingScreen from './components/LoadingScreen';
import ProtectedRoute from './components/ProtectedRoute';

// Context
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { LanguageProvider } from './context/LanguageContext';

function App() {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate initial loading
    setTimeout(() => {
      setLoading(false);
    }, 2000);
  }, []);

  if (loading) {
    return <LoadingScreen />;
  }

  return (
    <ThemeProvider>
      <AuthProvider>
        <LanguageProvider>
          <Router>
            <div className="min-h-screen bg-gradient-to-br from-sky-blue-light via-white to-lilac-light dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
              <Header />
              <AnimatePresence mode="wait">
                <Routes>
                  <Route path="/" element={<LandingPage />} />
                  <Route path="/login" element={<Login />} />
                  <Route path="/register" element={<Register />} />
                  <Route path="/about" element={<About />} />
                  <Route path="/contact" element={<Contact />} />
                  <Route path="/picture-therapy" element={<PictureTherapy />} />
                  
                  {/* Protected Routes */}
                  <Route path="/patient/*" element={
                    <ProtectedRoute userType="patient">
                      <Routes>
                        <Route path="dashboard" element={<PatientDashboard />} />
                        <Route path="session" element={<TherapySession />} />
                        <Route path="picture-therapy" element={<PictureTherapy />} />
                        <Route path="lip-animation" element={<LipAnimationExercise />} />
                      </Routes>
                    </ProtectedRoute>
                  } />
                  
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </AnimatePresence>
            </div>
          </Router>
        </LanguageProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
