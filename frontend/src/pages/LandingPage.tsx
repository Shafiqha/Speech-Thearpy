import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Activity, 
  Brain, 
  Globe2, 
  Heart, 
  Mic, 
  TrendingUp,
  Users,
  Award,
  ChevronRight,
  Play,
  Sparkles
} from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

const LandingPage: React.FC = () => {
  const { t } = useLanguage();

  const features = [
    {
      icon: Globe2,
      title: 'Multilingual Support',
      description: 'Full support for Hindi (हिंदी), Kannada (ಕನ್ನಡ), and English with single 317M parameter model',
      color: 'from-sky-blue to-lilac'
    },
    {
      icon: Brain,
      title: 'Dual-Head ASR Model',
      description: 'Wav2Vec 2.0 with word-level and phoneme-level analysis for precise error detection',
      color: 'from-sage to-forest'
    },
    {
      icon: TrendingUp,
      title: 'WAB-AQ Assessment',
      description: '2-3 minute assessment vs traditional 20-30 minutes with 89% therapist agreement',
      color: 'from-lilac to-slate-blue'
    },
    {
      icon: Heart,
      title: 'Real-time Feedback',
      description: 'Lip-synchronized animations with 95% phoneme accuracy and <500ms latency',
      color: 'from-sky-blue to-sage'
    }
  ];

  const stats = [
    { value: '88%', label: 'ASR Accuracy' },
    { value: '3', label: 'Languages' },
    { value: '0.87', label: 'Clinical Correlation' },
    { value: '350ms', label: 'CPU Latency' }
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden py-20 lg:py-32">
        <div className="absolute inset-0 bg-gradient-to-br from-sky-blue/20 via-transparent to-lilac/20"></div>
        
        <div className="container mx-auto px-4 relative z-10">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <motion.div
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
            >
              <div className="inline-flex items-center space-x-2 px-4 py-2 bg-sky-blue/20 dark:bg-sky-blue/10 rounded-full mb-6">
                <Sparkles className="w-4 h-4 text-forest dark:text-sky-blue" />
                <span className="text-sm font-medium text-forest dark:text-sky-blue">
                  AI-Powered Speech Therapy
                </span>
              </div>
              
              <h1 className="text-5xl lg:text-6xl font-display font-bold mb-6">
                <span className="gradient-text">Empowering</span>{' '}
                <span className="text-gray-900 dark:text-white">Recovery</span>
                <br />
                <span className="text-gray-900 dark:text-white">Through</span>{' '}
                <span className="gradient-text">Speech</span>
              </h1>
              
              <p className="text-xl text-gray-600 dark:text-gray-300 mb-8 leading-relaxed">
                Research-grade speech therapy with 317M parameter Wav2Vec 2.0 model trained on 56,000 hours of speech. 
                Dual-head architecture for word and phoneme-level analysis with real-time visual feedback.
              </p>
              
              <div className="flex flex-col sm:flex-row gap-4">
                <Link to="/register" className="btn-primary inline-flex items-center justify-center">
                  <Play className="w-5 h-5 mr-2" />
                  {t('startTherapy')}
                </Link>
                <Link to="/login" className="btn-secondary inline-flex items-center justify-center">
                  Login
                  <ChevronRight className="w-5 h-5 ml-2" />
                </Link>
              </div>
            </motion.div>
            
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="relative"
            >
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-br from-sky-blue to-lilac rounded-3xl blur-3xl opacity-30"></div>
                <div className="relative bg-white dark:bg-slate-800 rounded-3xl p-8 shadow-2xl">
                  <div className="flex items-center justify-center">
                    <div className="relative">
                      <motion.div
                        animate={{ 
                          scale: [1, 1.2, 1],
                          rotate: [0, 180, 360]
                        }}
                        transition={{ 
                          duration: 4,
                          repeat: Infinity,
                          repeatType: "reverse"
                        }}
                        className="absolute inset-0 bg-gradient-to-br from-sky-blue to-lilac rounded-full blur-xl opacity-50"
                      ></motion.div>
                      <Mic className="w-32 h-32 text-forest dark:text-sage relative z-10" />
                    </div>
                  </div>
                  
                  <div className="mt-8 grid grid-cols-3 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold gradient-text">Easy</div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">Level 1</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold gradient-text">Medium</div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">Level 2</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold gradient-text">Hard</div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">Level 3</div>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-gradient-to-r from-sky-blue/10 via-transparent to-lilac/10">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                viewport={{ once: true }}
                className="text-center"
              >
                <div className="text-4xl font-bold gradient-text mb-2">{stat.value}</div>
                <div className="text-gray-600 dark:text-gray-400">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="text-4xl font-display font-bold mb-4">
              <span className="gradient-text">Advanced Features</span>
            </h2>
            <p className="text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
              Comprehensive therapy tools designed for optimal patient outcomes
            </p>
          </motion.div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                viewport={{ once: true }}
                className="card hover:scale-105 transition-transform duration-300"
              >
                <div className={`w-12 h-12 bg-gradient-to-br ${feature.color} rounded-xl flex items-center justify-center mb-4`}>
                  <feature.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-lg font-semibold mb-2 text-gray-900 dark:text-white">
                  {feature.title}
                </h3>
                <p className="text-gray-600 dark:text-gray-400 text-sm">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-br from-sage/20 to-forest/20 dark:from-sage/10 dark:to-forest/10">
        <div className="container mx-auto px-4 text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
          >
            <Users className="w-16 h-16 mx-auto mb-6 text-forest dark:text-sage" />
            <h2 className="text-4xl font-display font-bold mb-4 text-gray-900 dark:text-white">
              Ready to Begin Your Journey?
            </h2>
            <p className="text-xl text-gray-600 dark:text-gray-300 mb-8 max-w-2xl mx-auto">
              Join thousands of patients using our platform for better speech therapy outcomes
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/register" className="btn-primary inline-flex items-center">
                <Heart className="w-5 h-5 mr-2" />
                Start Your Journey
              </Link>
              <Link to="/login" className="btn-secondary inline-flex items-center">
                <Award className="w-5 h-5 mr-2" />
                Sign In
              </Link>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;
