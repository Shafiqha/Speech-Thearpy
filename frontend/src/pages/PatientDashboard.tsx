import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadialBarChart,
  RadialBar,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import {
  Mic,
  TrendingUp,
  Award,
  Calendar,
  Clock,
  Target,
  Activity,
  ChevronRight,
  Play,
  BookOpen,
  Brain,
  Heart,
  Camera,
  MessageSquare,
  Video
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { useUserData, useUserSessions } from '../hooks/useUserData';

const PatientDashboard: React.FC = () => {
  const { user } = useAuth();
  const { t } = useLanguage();
  const { stats: userStats, progress, loading: statsLoading } = useUserData();
  const { sessions: recentSessionsData, loading: sessionsLoading } = useUserSessions(5);
  
  const [stats, setStats] = useState({
    totalSessions: 0,
    weekStreak: 5,
    averageAccuracy: 0,
    currentLevel: 'Medium',
    wabScore: user?.wabScore || 65,
    severityLevel: user?.severityLevel || 'Moderate'
  });

  const [categoryData, setCategoryData] = useState([
    { name: 'Easy', value: 0, fill: '#ADD4EB', total_exercises: 0 },
    { name: 'Medium', value: 0, fill: '#A6BAA3', total_exercises: 0 },
    { name: 'Hard', value: 0, fill: '#B8A5D6', total_exercises: 0 }
  ]);

  // Update stats when userStats loads
  useEffect(() => {
    if (userStats) {
      setStats(prev => ({
        ...prev,
        totalSessions: userStats.totalSessions,
        averageAccuracy: Math.round(userStats.averageAccuracy)
      }));
    }
  }, [userStats]);

  // Fetch category performance data
  useEffect(() => {
    const fetchCategoryPerformance = async () => {
      if (!user?.id) return;
      
      try {
        const response = await fetch(`http://localhost:8000/api/db/category-performance/${user.id}`);
        if (response.ok) {
          const data = await response.json();
          if (data.categories && data.categories.length > 0) {
            setCategoryData(data.categories);
          }
        }
      } catch (error) {
        console.error('Failed to fetch category performance:', error);
      }
    };

    fetchCategoryPerformance();
  }, [user?.id]);

  // Weekly progress data from database
  const [progressData, setProgressData] = useState([
    { date: 'Mon', accuracy: 0, wabScore: 0 },
    { date: 'Tue', accuracy: 0, wabScore: 0 },
    { date: 'Wed', accuracy: 0, wabScore: 0 },
    { date: 'Thu', accuracy: 0, wabScore: 0 },
    { date: 'Fri', accuracy: 0, wabScore: 0 },
    { date: 'Sat', accuracy: 0, wabScore: 0 },
    { date: 'Sun', accuracy: 0, wabScore: 0 }
  ]);

  // Fetch weekly progress
  useEffect(() => {
    const fetchProgress = async () => {
      if (!user?.id) return;
      try {
        const response = await fetch(`http://localhost:8000/api/db/progress/${user.id}?days=7`);
        if (response.ok) {
          const data = await response.json();
          if (data && data.length > 0) {
            const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
            const chartData = data.reverse().map((item: any) => {
              const date = new Date(item.date);
              return {
                date: dayNames[date.getDay()],
                accuracy: item.average_accuracy || 0,
                wabScore: item.wab_score || 0
              };
            });
            setProgressData(chartData);
          }
        }
      } catch (error) {
        console.error('Failed to fetch progress:', error);
      }
    };
    fetchProgress();
  }, [user?.id]);

  // Severity distribution data
  const severityData = [
    { name: 'Completed', value: stats.wabScore, fill: '#A6BAA3' },
    { name: 'Remaining', value: 100 - stats.wabScore, fill: '#E5E7EB' }
  ];

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'mild': return 'text-green-600 bg-green-100 dark:bg-green-900/20';
      case 'moderate': return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/20';
      case 'severe': return 'text-orange-600 bg-orange-100 dark:bg-orange-900/20';
      case 'very severe': return 'text-red-600 bg-red-100 dark:bg-red-900/20';
      default: return 'text-gray-600 bg-gray-100 dark:bg-gray-900/20';
    }
  };

  // Use real sessions data or fallback to empty array
  const recentSessions = recentSessionsData.length > 0 
    ? recentSessionsData.map((session: any) => ({
        id: session.session_id,
        date: new Date(session.start_time).toLocaleDateString(),
        duration: session.duration_seconds ? `${Math.round(session.duration_seconds / 60)} min` : 'In progress',
        accuracy: Math.round(session.average_accuracy),
        difficulty: session.difficulty.charAt(0).toUpperCase() + session.difficulty.slice(1)
      }))
    : [];

  return (
    <div className="min-h-screen py-8">
      <div className="container mx-auto px-4">
        {/* Welcome Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-display font-bold text-gray-900 dark:text-white mb-2">
            Welcome back, {user?.name}! 👋
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Your therapy journey continues. Keep up the great work!
          </p>
        </motion.div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
            className="card"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-gradient-to-br from-sky-blue to-lilac rounded-xl flex items-center justify-center">
                <Activity className="w-6 h-6 text-white" />
              </div>
              <span className="text-2xl font-bold gradient-text">{stats.totalSessions}</span>
            </div>
            <h3 className="text-gray-600 dark:text-gray-400 text-sm">Total Sessions</h3>
            <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">+3 this week</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            className="card"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-gradient-to-br from-sage to-forest rounded-xl flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-white" />
              </div>
              <span className="text-2xl font-bold gradient-text">{stats.averageAccuracy}%</span>
            </div>
            <h3 className="text-gray-600 dark:text-gray-400 text-sm">Average Accuracy</h3>
            <p className="text-xs text-green-600 dark:text-green-400 mt-1">↑ 5% improvement</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3 }}
            className="card"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-gradient-to-br from-lilac to-slate-blue rounded-xl flex items-center justify-center">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <span className="text-2xl font-bold gradient-text">{stats.wabScore}</span>
            </div>
            <h3 className="text-gray-600 dark:text-gray-400 text-sm">WAB-AQ Score</h3>
            <div className={`inline-flex px-2 py-1 rounded-full text-xs font-medium mt-1 ${getSeverityColor(stats.severityLevel)}`}>
              {stats.severityLevel}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.4 }}
            className="card"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-gradient-to-br from-sky-blue to-sage rounded-xl flex items-center justify-center">
                <Award className="w-6 h-6 text-white" />
              </div>
              <span className="text-2xl font-bold gradient-text">{stats.weekStreak}</span>
            </div>
            <h3 className="text-gray-600 dark:text-gray-400 text-sm">Day Streak</h3>
            <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">Keep it going!</p>
          </motion.div>
        </div>

        {/* Main Content Grid */}
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Left Column - Charts */}
          <div className="lg:col-span-2 space-y-6">
            {/* Progress Chart */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="card"
            >
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  Weekly Progress
                </h2>
                <select className="px-3 py-1 rounded-lg border border-gray-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-sm">
                  <option>This Week</option>
                  <option>Last Week</option>
                  <option>This Month</option>
                </select>
              </div>
              
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={progressData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="date" stroke="#6b7280" />
                  <YAxis stroke="#6b7280" />
                  <Tooltip />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="accuracy" 
                    stroke="#ADD4EB" 
                    strokeWidth={2}
                    dot={{ fill: '#ADD4EB', r: 4 }}
                    name="Accuracy %"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="wabScore" 
                    stroke="#A6BAA3" 
                    strokeWidth={2}
                    dot={{ fill: '#A6BAA3', r: 4 }}
                    name="WAB Score"
                  />
                </LineChart>
              </ResponsiveContainer>
            </motion.div>

            {/* Category Performance */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
              className="card"
            >
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
                Performance by Category
              </h2>
              
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={categoryData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="name" stroke="#6b7280" />
                  <YAxis stroke="#6b7280" />
                  <Tooltip />
                  <Bar dataKey="value" fill="#ADD4EB" radius={[8, 8, 0, 0]}>
                    {categoryData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </motion.div>
          </div>

          {/* Right Column - Actions & Recent */}
          <div className="space-y-6">
            {/* Start Session Card */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.7 }}
              className="card bg-gradient-to-br from-sky-blue/20 to-lilac/20 dark:from-sky-blue/10 dark:to-lilac/10 border-0"
            >
              <div className="text-center py-4">
                <div className="w-20 h-20 mx-auto mb-4 bg-white dark:bg-slate-800 rounded-2xl flex items-center justify-center shadow-lg">
                  <Mic className="w-10 h-10 text-forest dark:text-sage" />
                </div>
                <h3 className="text-xl font-semibold mb-2 text-gray-900 dark:text-white">
                  Ready for Today's Session?
                </h3>
                <p className="text-gray-600 dark:text-gray-400 text-sm mb-6">
                  Choose your therapy type
                </p>
                
                {/* Therapy Session Button */}
                <Link
                  to="/patient/session"
                  className="btn-primary w-full inline-flex items-center justify-center mb-3"
                >
                  <MessageSquare className="w-5 h-5 mr-2" />
                  Therapy Session
                </Link>
                
                {/* Picture Therapy Button */}
                <Link
                  to="/patient/picture-therapy"
                  className="btn-secondary w-full inline-flex items-center justify-center mb-3"
                >
                  <Camera className="w-5 h-5 mr-2" />
                  Picture Therapy
                </Link>

                {/* Lip Animation Exercise Button */}
                <Link
                  to="/patient/lip-animation"
                  className="btn-secondary w-full inline-flex items-center justify-center bg-gradient-to-r from-purple-500 to-indigo-500 hover:from-purple-600 hover:to-indigo-600 text-white border-0"
                >
                  <Video className="w-5 h-5 mr-2" />
                  Lip Animation Exercise
                </Link>
              </div>
            </motion.div>

            {/* Recent Sessions */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.8 }}
              className="card"
            >
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                Recent Sessions
              </h2>
              
              <div className="space-y-3">
                {recentSessions.map((session) => (
                  <div
                    key={session.id}
                    className="p-3 bg-gray-50 dark:bg-slate-700/50 rounded-xl hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        {session.date}
                      </span>
                      <span className="text-xs px-2 py-1 bg-sage/20 dark:bg-sage/10 text-forest dark:text-sage-light rounded-full">
                        {session.difficulty}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-xs text-gray-600 dark:text-gray-400">
                      <span className="flex items-center">
                        <Clock className="w-3 h-3 mr-1" />
                        {session.duration}
                      </span>
                      <span className="flex items-center">
                        <Target className="w-3 h-3 mr-1" />
                        {session.accuracy}% accuracy
                      </span>
                    </div>
                  </div>
                ))}
              </div>
              
              <button className="w-full mt-4 text-sm text-forest dark:text-sage-light hover:text-forest-dark dark:hover:text-sage font-medium flex items-center justify-center">
                View All Sessions
                <ChevronRight className="w-4 h-4 ml-1" />
              </button>
            </motion.div>

            {/* Tips Card */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.9 }}
              className="card bg-gradient-to-br from-sage/10 to-forest/10"
            >
              <div className="flex items-start space-x-3">
                <BookOpen className="w-5 h-5 text-forest dark:text-sage mt-1" />
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                    Today's Tip
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Practice speaking slowly and clearly. Focus on pronouncing each syllable distinctly for better results.
                  </p>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PatientDashboard;
