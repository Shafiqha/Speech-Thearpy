import axios from 'axios';

// API Base URL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Unauthorized - redirect to login
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// -------------------- Auth APIs --------------------

export const authAPI = {
  register: async (userData: any) => {
    const response = await api.post('/api/auth/register', userData);
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token);
    }
    return response.data;
  },

  login: async (email: string, password: string, userType: string) => {
    const response = await api.post('/api/auth/login', {
      email,
      password,
      userType,
    });
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token);
    }
    return response.data;
  },

  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },
};

// -------------------- Therapy Session APIs --------------------

export const sessionAPI = {
  startSession: async (language: string, difficulty: string, patientId?: string) => {
    const response = await api.post('/api/session/start', {
      language,
      difficulty,
      patient_id: patientId,
    });
    return response.data;
  },

  getSentences: async (language: string, difficulty: string, count: number = 5) => {
    const response = await api.get('/api/sentences', {
      params: { language, difficulty, count },
    });
    return response.data;
  },

  processAudio: async (audioBlob: Blob, targetSentence: string, language: string, sessionId?: string) => {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.wav');
    formData.append('target_sentence', targetSentence);
    formData.append('language', language);
    if (sessionId) {
      formData.append('session_id', sessionId);
    }

    const response = await api.post('/api/process-audio', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  completeSession: async (sessionId: string) => {
    const response = await api.post(`/api/session/${sessionId}/complete`);
    return response.data;
  },

  textToSpeech: async (text: string, language: string) => {
    const response = await api.post('/api/tts', 
      { text, language },
      { responseType: 'blob' }
    );
    
    // Create audio URL from blob
    const audioUrl = URL.createObjectURL(response.data);
    
    // Play audio
    const audio = new Audio(audioUrl);
    await audio.play();
    
    return audioUrl;
  },
};

// -------------------- Patient APIs --------------------

export const patientAPI = {
  getProgress: async (patientId: string) => {
    const response = await api.get(`/api/patient/progress/${patientId}`);
    return response.data;
  },

  getSessions: async (patientId: string, limit: number = 10) => {
    const response = await api.get(`/api/patient/sessions/${patientId}`, {
      params: { limit },
    });
    return response.data;
  },

  updateProfile: async (patientId: string, data: any) => {
    const response = await api.put(`/api/patient/${patientId}`, data);
    return response.data;
  },
};

// -------------------- Utility APIs --------------------

export const utilityAPI = {
  healthCheck: async () => {
    const response = await api.get('/health');
    return response.data;
  },

  getLanguages: () => {
    return [
      { code: 'en', name: 'English', flag: '🇬🇧' },
      { code: 'hi', name: 'हिंदी', flag: '🇮🇳' },
      { code: 'kn', name: 'ಕನ್ನಡ', flag: '🇮🇳' },
    ];
  },

  getDifficulties: () => {
    return ['easy', 'medium', 'hard'];
  },

  getSeverityLevels: () => {
    return [
      { range: '0-25', name: 'Very Severe', color: 'red' },
      { range: '26-50', name: 'Severe', color: 'orange' },
      { range: '51-75', name: 'Moderate', color: 'yellow' },
      { range: '76-100', name: 'Mild', color: 'green' },
    ];
  },
};

export default api;
