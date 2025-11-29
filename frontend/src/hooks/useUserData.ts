/**
 * Custom hook to fetch user-specific data from database
 */

import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';

interface UserStats {
  totalSessions: number;
  totalExercises: number;
  averageAccuracy: number;
  recentSessions: any[];
}

interface ProgressData {
  date: string;
  sessions_completed: number;
  total_exercises: number;
  average_accuracy: number;
  streak_days: number;
}

export const useUserData = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState<UserStats | null>(null);
  const [progress, setProgress] = useState<ProgressData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }

    const fetchUserData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch user statistics
        const statsResponse = await fetch(`http://localhost:8000/api/db/stats/${user.id}`);
        if (statsResponse.ok) {
          const statsData = await statsResponse.json();
          setStats({
            totalSessions: statsData.total_sessions || 0,
            totalExercises: statsData.total_exercises || 0,
            averageAccuracy: statsData.average_accuracy || 0,
            recentSessions: statsData.recent_sessions || []
          });
        }

        // Fetch progress data (last 30 days)
        const progressResponse = await fetch(`http://localhost:8000/api/db/progress/${user.id}?days=30`);
        if (progressResponse.ok) {
          const progressData = await progressResponse.json();
          setProgress(progressData);
        }

      } catch (err) {
        console.error('Failed to fetch user data:', err);
        setError('Failed to load user data');
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
  }, [user]);

  return { stats, progress, loading, error };
};

export const useUserSessions = (limit: number = 10) => {
  const { user } = useAuth();
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }

    const fetchSessions = async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/db/sessions/patient/${user.id}?limit=${limit}`);
        if (response.ok) {
          const data = await response.json();
          setSessions(data);
        }
      } catch (err) {
        console.error('Failed to fetch sessions:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchSessions();
  }, [user, limit]);

  return { sessions, loading };
};

export const createSession = async (userId: string, sessionData: {
  session_type: string;
  language: string;
  difficulty?: string;
}) => {
  const response = await fetch('http://localhost:8000/api/db/sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      patient_id: userId,
      ...sessionData
    })
  });

  if (!response.ok) {
    throw new Error('Failed to create session');
  }

  return await response.json();
};

export const saveExerciseAttempt = async (attemptData: {
  session_id: string;
  patient_id: string;
  exercise_type: string;
  target_text: string;
  transcription?: string;
  accuracy?: number;
  wab_score?: number;
  feedback?: string;
}) => {
  const response = await fetch('http://localhost:8000/api/db/attempts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(attemptData)
  });

  if (!response.ok) {
    throw new Error('Failed to save exercise attempt');
  }

  return await response.json();
};
