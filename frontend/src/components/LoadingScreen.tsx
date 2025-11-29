import React from 'react';
import { motion } from 'framer-motion';
import { Activity } from 'lucide-react';

const LoadingScreen: React.FC = () => {
  return (
    <div className="fixed inset-0 bg-gradient-to-br from-sky-blue-light via-white to-lilac-light dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 flex items-center justify-center z-50">
      <div className="text-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          className="inline-block"
        >
          <div className="w-20 h-20 bg-gradient-to-br from-sky-blue to-lilac rounded-2xl flex items-center justify-center">
            <Activity className="w-12 h-12 text-white" />
          </div>
        </motion.div>
        
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mt-6 text-2xl font-display font-bold gradient-text"
        >
          SpeechTherapy AI
        </motion.h2>
        
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="mt-2 text-gray-600 dark:text-gray-400"
        >
          Loading your therapy session...
        </motion.p>
        
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: "100%" }}
          transition={{ duration: 2, ease: "easeInOut" }}
          className="mt-6 h-1 bg-gradient-to-r from-sky-blue to-lilac rounded-full mx-auto max-w-xs"
        />
      </div>
    </div>
  );
};

export default LoadingScreen;
