import React, { createContext, useContext, useState, ReactNode } from 'react';

type Language = 'en' | 'hi' | 'kn';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  translations: typeof translations;
  t: (key: string) => string;
}

const translations = {
  en: {
    welcome: 'Welcome to Speech Therapy',
    startTherapy: 'Start Therapy',
    register: 'Register',
    dashboard: 'Dashboard',
    progress: 'Progress',
    sessions: 'Sessions',
    severity: 'Severity',
    language: 'Language',
    selectLanguage: 'Select Language',
    english: 'English',
    hindi: 'Hindi',
    kannada: 'Kannada',
    record: 'Record',
    stop: 'Stop',
    playExample: 'Play Example',
    nextSentence: 'Next Sentence',
    accuracy: 'Accuracy',
    excellent: 'Excellent',
    good: 'Good',
    fair: 'Fair',
    needsWork: 'Needs Work',
    mild: 'Mild',
    moderate: 'Moderate',
    severe: 'Severe',
    verySevere: 'Very Severe',
    about: 'About',
    contact: 'Contact',
    logout: 'Logout',
    profile: 'Profile',
    settings: 'Settings',
    help: 'Help',
    mission: 'Our Mission',
    team: 'Our Team',
    research: 'Research',
    contactUs: 'Contact Us',
    email: 'Email',
    password: 'Password',
    name: 'Name',
    phone: 'Phone',
    message: 'Message',
    send: 'Send',
    cancel: 'Cancel',
    save: 'Save',
    edit: 'Edit',
    delete: 'Delete',
    view: 'View',
    export: 'Export',
    import: 'Import',
    search: 'Search',
    filter: 'Filter',
    sort: 'Sort',
    loading: 'Loading...',
    error: 'Error',
    success: 'Success',
    warning: 'Warning',
    info: 'Info'
  },
  hi: {
    welcome: 'स्पीच थेरेपी में आपका स्वागत है',
    startTherapy: 'थेरेपी शुरू करें',
    register: 'पंजीकरण',
    dashboard: 'डैशबोर्ड',
    progress: 'प्रगति',
    sessions: 'सत्र',
    severity: 'गंभीरता',
    language: 'भाषा',
    selectLanguage: 'भाषा चुनें',
    english: 'अंग्रेज़ी',
    hindi: 'हिंदी',
    kannada: 'कन्नड़',
    record: 'रिकॉर्ड',
    stop: 'रोकें',
    playExample: 'उदाहरण चलाएं',
    nextSentence: 'अगला वाक्य',
    accuracy: 'सटीकता',
    excellent: 'उत्कृष्ट',
    good: 'अच्छा',
    fair: 'ठीक',
    needsWork: 'सुधार की जरूरत',
    mild: 'हल्का',
    moderate: 'मध्यम',
    severe: 'गंभीर',
    verySevere: 'बहुत गंभीर',
    about: 'के बारे में',
    contact: 'संपर्क',
    logout: 'लॉग आउट',
    profile: 'प्रोफ़ाइल',
    settings: 'सेटिंग्स',
    help: 'मदद',
    mission: 'हमारा मिशन',
    team: 'हमारी टीम',
    research: 'अनुसंधान',
    contactUs: 'हमसे संपर्क करें',
    email: 'ईमेल',
    password: 'पासवर्ड',
    name: 'नाम',
    phone: 'फोन',
    message: 'संदेश',
    send: 'भेजें',
    cancel: 'रद्द करें',
    save: 'सहेजें',
    edit: 'संपादित करें',
    delete: 'हटाएं',
    view: 'देखें',
    export: 'निर्यात',
    import: 'आयात',
    search: 'खोजें',
    filter: 'फ़िल्टर',
    sort: 'क्रमबद्ध करें',
    loading: 'लोड हो रहा है...',
    error: 'त्रुटि',
    success: 'सफलता',
    warning: 'चेतावनी',
    info: 'जानकारी'
  },
  kn: {
    welcome: 'ಸ್ಪೀಚ್ ಥೆರಪಿಗೆ ಸ್ವಾಗತ',
    startTherapy: 'ಚಿಕಿತ್ಸೆ ಪ್ರಾರಂಭಿಸಿ',
    register: 'ನೋಂದಣಿ',
    dashboard: 'ಡ್ಯಾಶ್‌ಬೋರ್ಡ್',
    progress: 'ಪ್ರಗತಿ',
    sessions: 'ಸೆಷನ್‌ಗಳು',
    severity: 'ತೀವ್ರತೆ',
    language: 'ಭಾಷೆ',
    selectLanguage: 'ಭಾಷೆ ಆಯ್ಕೆಮಾಡಿ',
    english: 'ಇಂಗ್ಲಿಷ್',
    hindi: 'ಹಿಂದಿ',
    kannada: 'ಕನ್ನಡ',
    record: 'ರೆಕಾರ್ಡ್',
    stop: 'ನಿಲ್ಲಿಸಿ',
    playExample: 'ಉದಾಹರಣೆ ಪ್ಲೇ ಮಾಡಿ',
    nextSentence: 'ಮುಂದಿನ ವಾಕ್ಯ',
    accuracy: 'ನಿಖರತೆ',
    excellent: 'ಅತ್ಯುತ್ತಮ',
    good: 'ಒಳ್ಳೆಯದು',
    fair: 'ಸರಿ',
    needsWork: 'ಸುಧಾರಣೆ ಬೇಕು',
    mild: 'ಸೌಮ್ಯ',
    moderate: 'ಮಧ್ಯಮ',
    severe: 'ತೀವ್ರ',
    verySevere: 'ಅತ್ಯಂತ ತೀವ್ರ',
    about: 'ಬಗ್ಗೆ',
    contact: 'ಸಂಪರ್ಕ',
    logout: 'ಲಾಗ್ ಔಟ್',
    profile: 'ಪ್ರೊಫೈಲ್',
    settings: 'ಸೆಟ್ಟಿಂಗ್‌ಗಳು',
    help: 'ಸಹಾಯ',
    mission: 'ನಮ್ಮ ಧ್ಯೇಯ',
    team: 'ನಮ್ಮ ತಂಡ',
    research: 'ಸಂಶೋಧನೆ',
    contactUs: 'ನಮ್ಮನ್ನು ಸಂಪರ್ಕಿಸಿ',
    email: 'ಇಮೇಲ್',
    password: 'ಪಾಸ್‌ವರ್ಡ್',
    name: 'ಹೆಸರು',
    phone: 'ಫೋನ್',
    message: 'ಸಂದೇಶ',
    send: 'ಕಳುಹಿಸಿ',
    cancel: 'ರದ್ದುಮಾಡಿ',
    save: 'ಉಳಿಸಿ',
    edit: 'ಸಂಪಾದಿಸಿ',
    delete: 'ಅಳಿಸಿ',
    view: 'ವೀಕ್ಷಿಸಿ',
    export: 'ರಫ್ತು',
    import: 'ಆಮದು',
    search: 'ಹುಡುಕಿ',
    filter: 'ಫಿಲ್ಟರ್',
    sort: 'ವಿಂಗಡಿಸಿ',
    loading: 'ಲೋಡ್ ಆಗುತ್ತಿದೆ...',
    error: 'ದೋಷ',
    success: 'ಯಶಸ್ಸು',
    warning: 'ಎಚ್ಚರಿಕೆ',
    info: 'ಮಾಹಿತಿ'
  }
};

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};

interface LanguageProviderProps {
  children: ReactNode;
}

export const LanguageProvider: React.FC<LanguageProviderProps> = ({ children }) => {
  const [language, setLanguage] = useState<Language>(() => {
    const saved = localStorage.getItem('language') as Language;
    return saved || 'en';
  });

  const handleSetLanguage = (lang: Language) => {
    setLanguage(lang);
    localStorage.setItem('language', lang);
  };

  const t = (key: string): string => {
    return translations[language][key as keyof typeof translations['en']] || key;
  };

  return (
    <LanguageContext.Provider value={{ 
      language, 
      setLanguage: handleSetLanguage, 
      translations,
      t 
    }}>
      {children}
    </LanguageContext.Provider>
  );
};
