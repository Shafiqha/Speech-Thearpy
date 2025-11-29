import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
  id: string;
  name: string;
  email: string;
  userType: 'patient';
  language?: string;
  severityLevel?: string;
  wabScore?: number;
}

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string, userType: string) => Promise<void>;
  register: (userData: any) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for stored user session
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
    setLoading(false);
  }, []);

  const login = async (email: string, password: string, userType: string) => {
    try {
      // Call actual database API
      const response = await fetch('http://localhost:8000/api/db/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Login failed');
      }

      const userData = await response.json();
      
      // Create user object from API response
      const authenticatedUser: User = {
        id: userData.user_id,
        name: userData.name,
        email: userData.email,
        userType: 'patient',
        language: 'en'
      };

      // Get patient profile data
      try {
        const profileResponse = await fetch(`http://localhost:8000/api/db/users/${userData.user_id}`);
        if (profileResponse.ok) {
          const profileData = await profileResponse.json();
          authenticatedUser.severityLevel = profileData.severity_level;
          authenticatedUser.wabScore = profileData.wab_score;
        }
      } catch (err) {
        console.error('Failed to fetch profile:', err);
      }

      setUser(authenticatedUser);
      localStorage.setItem('user', JSON.stringify(authenticatedUser));
      localStorage.setItem('userId', userData.user_id);
      localStorage.setItem('token', 'jwt-token-' + userData.user_id);
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const register = async (userData: any) => {
    try {
      // Call actual database API
      const response = await fetch('http://localhost:8000/api/db/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: userData.email,
          password: userData.password,
          name: userData.name,
          user_type: userData.userType,
          phone: userData.phone,
          date_of_birth: userData.dateOfBirth,
          gender: userData.gender
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Registration failed');
      }

      const registeredUser = await response.json();

      const newUser: User = {
        id: registeredUser.user_id,
        name: registeredUser.name,
        email: registeredUser.email,
        userType: 'patient',
        language: userData.language || 'en'
      };

      setUser(newUser);
      localStorage.setItem('user', JSON.stringify(newUser));
      localStorage.setItem('userId', registeredUser.user_id);
      localStorage.setItem('token', 'jwt-token-' + registeredUser.user_id);
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('user');
    localStorage.removeItem('token');
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};
