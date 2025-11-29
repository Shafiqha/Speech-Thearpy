import React from 'react';
import { motion } from 'framer-motion';
import { Heart, Brain, Globe2, Award, Users, Target } from 'lucide-react';

const About: React.FC = () => {
  const technicalSpecs = [
    { name: 'Wav2Vec 2.0 XLSR-53', role: '317M Parameters', image: '🧠' },
    { name: 'Dual-Head Architecture', role: 'Word + Phoneme Analysis', image: '🔍' },
    { name: 'CTC Loss Function', role: 'Temporal Classification', image: '📊' },
    { name: 'Rhubarb Lip Sync', role: '95% Viseme Accuracy', image: '👄' }
  ];

  const values = [
    {
      icon: Heart,
      title: 'Compassionate Care',
      description: 'We prioritize patient comfort and emotional well-being throughout the therapy journey.'
    },
    {
      icon: Brain,
      title: 'Evidence-Based',
      description: 'Our methods are grounded in the latest research in speech pathology and neuroscience.'
    },
    {
      icon: Globe2,
      title: 'Inclusive Access',
      description: 'Multilingual support ensures therapy is accessible to diverse communities.'
    },
    {
      icon: Target,
      title: 'Personalized Approach',
      description: 'Every patient receives customized therapy adapted to their unique needs and progress.'
    }
  ];

  return (
    <div className="min-h-screen py-12">
      <div className="container mx-auto px-4">
        {/* Hero Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-16"
        >
          <h1 className="text-5xl font-display font-bold gradient-text mb-6">
            About SpeechTherapy AI
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
            Revolutionizing aphasia rehabilitation through cutting-edge AI technology 
            and compassionate, personalized care.
          </p>
        </motion.div>

        {/* Mission Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mb-16"
        >
          <div className="card bg-gradient-to-br from-sky-blue/20 to-lilac/20 dark:from-sky-blue/10 dark:to-lilac/10">
            <div className="grid md:grid-cols-2 gap-8 items-center">
              <div>
                <h2 className="text-3xl font-display font-bold mb-4 text-gray-900 dark:text-white">
                  Our Mission
                </h2>
                <p className="text-gray-600 dark:text-gray-300 mb-4">
                  Built on Wav2Vec 2.0 XLSR-53 architecture with 317M parameters, pre-trained on 
                  56,000 hours of speech across 53 languages. Our dual-head model provides both 
                  word-level transcription and phoneme-level analysis for comprehensive error detection.
                </p>
                <p className="text-gray-600 dark:text-gray-300">
                  Validated severity assessment using WAB-AQ scoring with 0.87 correlation to clinical 
                  assessments and 89% agreement with speech therapists. Assessment time reduced from 
                  20-30 minutes to just 2-3 minutes.
                </p>
              </div>
              <div className="flex justify-center">
                <div className="relative">
                  <div className="absolute inset-0 bg-gradient-to-br from-sage to-forest rounded-full blur-3xl opacity-20"></div>
                  <Award className="w-48 h-48 text-forest dark:text-sage relative z-10" />
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Values Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mb-16"
        >
          <h2 className="text-3xl font-display font-bold text-center mb-12 gradient-text">
            Our Core Values
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {values.map((value, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                viewport={{ once: true }}
                className="card text-center"
              >
                <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-sky-blue to-lilac rounded-xl flex items-center justify-center">
                  <value.icon className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-lg font-semibold mb-2 text-gray-900 dark:text-white">
                  {value.title}
                </h3>
                <p className="text-gray-600 dark:text-gray-400 text-sm">
                  {value.description}
                </p>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Research Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mb-16"
        >
          <div className="card">
            <h2 className="text-3xl font-display font-bold mb-6 gradient-text">
              Research & Innovation
            </h2>
            <div className="grid md:grid-cols-3 gap-6">
              <div>
                <h3 className="text-xl font-semibold mb-3 text-gray-900 dark:text-white">
                  AI-Powered Assessment
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  Wav2Vec 2.0 with 12 transformer layers achieving 88% average accuracy across 
                  Hindi (88-91%), Kannada (85-89%), and English (92-95%) with under 500ms CPU latency.
                </p>
              </div>
              <div>
                <h3 className="text-xl font-semibold mb-3 text-gray-900 dark:text-white">
                  Adaptive Learning
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  Progressive difficulty system with 4 levels (Easy/Medium/Hard/Conversation) using 
                  Levenshtein distance and phoneme alignment for real-time performance tracking.
                </p>
              </div>
              <div>
                <h3 className="text-xl font-semibold mb-3 text-gray-900 dark:text-white">
                  Clinical Validation
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  Based on Western Aphasia Battery (WAB-AQ) with 0.92 test-retest reliability. 
                  Visual feedback integration shown to improve outcomes by 35%.
                </p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Team Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mb-16"
        >
          <h2 className="text-3xl font-display font-bold text-center mb-12 gradient-text">
            Technical Architecture
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {technicalSpecs.map((member, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.1 }}
                viewport={{ once: true }}
                className="card text-center"
              >
                <div className="text-6xl mb-4">{member.image}</div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {member.name}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {member.role}
                </p>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Stats Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="card bg-gradient-to-br from-sage/20 to-forest/20 dark:from-sage/10 dark:to-forest/10"
        >
          <div className="grid md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-4xl font-bold gradient-text mb-2">317M</div>
              <div className="text-gray-600 dark:text-gray-400">Model Parameters</div>
            </div>
            <div>
              <div className="text-4xl font-bold gradient-text mb-2">88%</div>
              <div className="text-gray-600 dark:text-gray-400">ASR Accuracy</div>
            </div>
            <div>
              <div className="text-4xl font-bold gradient-text mb-2">56K</div>
              <div className="text-gray-600 dark:text-gray-400">Training Hours</div>
            </div>
            <div>
              <div className="text-4xl font-bold gradient-text mb-2">350ms</div>
              <div className="text-gray-600 dark:text-gray-400">CPU Latency</div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default About;
