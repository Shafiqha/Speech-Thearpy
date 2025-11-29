"""
Initial Assessment System for Aphasia Severity Determination
"""

import random
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class SeverityLevel(Enum):
    VERY_SEVERE = "very_severe"  # WAB-AQ: 0-25
    SEVERE = "severe"           # WAB-AQ: 26-50
    MODERATE = "moderate"       # WAB-AQ: 51-75
    MILD = "mild"              # WAB-AQ: 76-100

@dataclass
class AssessmentWord:
    word: str
    language: str
    difficulty: str  # "basic", "intermediate", "advanced"
    category: str    # "greeting", "common", "complex"
    expected_wab_range: Tuple[int, int]  # Expected WAB score range for this word

@dataclass
class AssessmentResult:
    word: str
    language: str
    transcription: str
    accuracy: float
    pronunciation_score: float
    estimated_wab: float
    severity_level: SeverityLevel
    confidence: float
    recommendations: List[str]

class InitialAssessment:
    """Manages initial assessment for severity determination"""
    
    def __init__(self):
        self.assessment_words = self._create_assessment_database()
    
    def _create_assessment_database(self) -> Dict[str, List[AssessmentWord]]:
        """Create assessment word database for each language"""
        
        assessment_db = {
            "hi": [
                # Basic level (Very Severe - Severe)
                AssessmentWord("नमस्ते", "hi", "basic", "greeting", (0, 50)),
                AssessmentWord("हाँ", "hi", "basic", "common", (0, 40)),
                AssessmentWord("पानी", "hi", "basic", "common", (10, 60)),
                AssessmentWord("खाना", "hi", "basic", "common", (10, 60)),
                
                # Intermediate level (Severe - Moderate)
                AssessmentWord("धन्यवाद", "hi", "intermediate", "greeting", (30, 70)),
                AssessmentWord("अच्छा", "hi", "intermediate", "common", (25, 65)),
                AssessmentWord("समय", "hi", "intermediate", "common", (35, 75)),
                AssessmentWord("काम", "hi", "intermediate", "common", (30, 70)),
                
                # Advanced level (Moderate - Mild)
                AssessmentWord("स्वास्थ्य", "hi", "advanced", "complex", (50, 90)),
                AssessmentWord("शिक्षा", "hi", "advanced", "complex", (55, 95)),
                AssessmentWord("परिवार", "hi", "advanced", "complex", (45, 85)),
                AssessmentWord("व्यायाम", "hi", "advanced", "complex", (60, 100)),
            ],
            
            "kn": [
                # Basic level (Very Severe - Severe)
                AssessmentWord("ನಮಸ್ಕಾರ", "kn", "basic", "greeting", (0, 50)),
                AssessmentWord("ಹೌದು", "kn", "basic", "common", (0, 40)),
                AssessmentWord("ನೀರು", "kn", "basic", "common", (10, 60)),
                AssessmentWord("ಅನ್ನ", "kn", "basic", "common", (10, 60)),
                
                # Intermediate level (Severe - Moderate)
                AssessmentWord("ಧನ್ಯವಾದ", "kn", "intermediate", "greeting", (30, 70)),
                AssessmentWord("ಒಳ್ಳೆಯದು", "kn", "intermediate", "common", (25, 65)),
                AssessmentWord("ಸಮಯ", "kn", "intermediate", "common", (35, 75)),
                AssessmentWord("ಕೆಲಸ", "kn", "intermediate", "common", (30, 70)),
                
                # Advanced level (Moderate - Mild)
                AssessmentWord("ಆರೋಗ್ಯ", "kn", "advanced", "complex", (50, 90)),
                AssessmentWord("ಶಿಕ್ಷಣ", "kn", "advanced", "complex", (55, 95)),
                AssessmentWord("ಕುಟುಂಬ", "kn", "advanced", "complex", (45, 85)),
                AssessmentWord("ವ್ಯಾಯಾಮ", "kn", "advanced", "complex", (60, 100)),
            ],
            
            "en": [
                # Basic level (Very Severe - Severe)
                AssessmentWord("hello", "en", "basic", "greeting", (0, 50)),
                AssessmentWord("yes", "en", "basic", "common", (0, 40)),
                AssessmentWord("water", "en", "basic", "common", (10, 60)),
                AssessmentWord("food", "en", "basic", "common", (10, 60)),
                
                # Intermediate level (Severe - Moderate)
                AssessmentWord("thank you", "en", "intermediate", "greeting", (30, 70)),
                AssessmentWord("good", "en", "intermediate", "common", (25, 65)),
                AssessmentWord("time", "en", "intermediate", "common", (35, 75)),
                AssessmentWord("work", "en", "intermediate", "common", (30, 70)),
                
                # Advanced level (Moderate - Mild)
                AssessmentWord("health", "en", "advanced", "complex", (50, 90)),
                AssessmentWord("education", "en", "advanced", "complex", (55, 95)),
                AssessmentWord("family", "en", "advanced", "complex", (45, 85)),
                AssessmentWord("exercise", "en", "advanced", "complex", (60, 100)),
            ]
        }
        
        return assessment_db
    
    def get_assessment_word(self, language: str, attempt: int = 1) -> AssessmentWord:
        """
        Get assessment word based on language and attempt number
        
        Args:
            language: Language code (hi, kn, en)
            attempt: Attempt number (1=basic, 2=intermediate, 3=advanced)
        """
        
        if language not in self.assessment_words:
            language = "en"  # fallback
        
        words = self.assessment_words[language]
        
        # Select difficulty based on attempt
        if attempt == 1:
            # Start with basic words
            basic_words = [w for w in words if w.difficulty == "basic"]
            return random.choice(basic_words) if basic_words else words[0]
        elif attempt == 2:
            # Move to intermediate
            intermediate_words = [w for w in words if w.difficulty == "intermediate"]
            return random.choice(intermediate_words) if intermediate_words else words[4]
        else:
            # Advanced words
            advanced_words = [w for w in words if w.difficulty == "advanced"]
            return random.choice(advanced_words) if advanced_words else words[8]
    
    def calculate_severity_from_assessment(
        self, 
        assessment_results: List[Dict], 
        language: str
    ) -> Tuple[SeverityLevel, float, List[str]]:
        """
        Calculate severity level from assessment results
        
        Args:
            assessment_results: List of assessment results
            language: Language code
            
        Returns:
            Tuple of (severity_level, wab_score, recommendations)
        """
        
        if not assessment_results:
            return SeverityLevel.VERY_SEVERE, 0.0, ["Complete initial assessment first"]
        
        # Calculate weighted average based on word difficulty
        total_score = 0
        total_weight = 0
        
        difficulty_weights = {"basic": 1.0, "intermediate": 1.5, "advanced": 2.0}
        
        for result in assessment_results:
            accuracy = result.get('accuracy', 0)
            word = result.get('word', '')
            
            # Find the assessment word to get difficulty
            assessment_word = self._find_assessment_word(word, language)
            if assessment_word:
                weight = difficulty_weights.get(assessment_word.difficulty, 1.0)
                total_score += accuracy * weight
                total_weight += weight
        
        # Calculate average weighted score
        if total_weight > 0:
            avg_score = total_score / total_weight
        else:
            avg_score = 0
        
        # Convert to WAB-AQ scale (0-100)
        estimated_wab = min(100, max(0, avg_score))
        
        # Determine severity level
        if estimated_wab <= 25:
            severity = SeverityLevel.VERY_SEVERE
        elif estimated_wab <= 50:
            severity = SeverityLevel.SEVERE
        elif estimated_wab <= 75:
            severity = SeverityLevel.MODERATE
        else:
            severity = SeverityLevel.MILD
        
        # Generate recommendations
        recommendations = self._generate_recommendations(severity, estimated_wab, assessment_results)
        
        return severity, estimated_wab, recommendations
    
    def _find_assessment_word(self, word: str, language: str) -> Optional[AssessmentWord]:
        """Find assessment word by text and language"""
        
        if language not in self.assessment_words:
            return None
        
        for assessment_word in self.assessment_words[language]:
            if assessment_word.word == word:
                return assessment_word
        
        return None
    
    def _generate_recommendations(
        self, 
        severity: SeverityLevel, 
        wab_score: float, 
        results: List[Dict]
    ) -> List[str]:
        """Generate personalized recommendations based on assessment"""
        
        recommendations = []
        
        if severity == SeverityLevel.VERY_SEVERE:
            recommendations.extend([
                "Start with basic single words and sounds",
                "Focus on familiar greetings and common words",
                "Practice daily with short 10-15 minute sessions",
                "Use visual aids and gestures to support speech"
            ])
        elif severity == SeverityLevel.SEVERE:
            recommendations.extend([
                "Practice basic words and short phrases",
                "Work on clear pronunciation of familiar words",
                "Gradually increase vocabulary with common items",
                "Practice naming everyday objects"
            ])
        elif severity == SeverityLevel.MODERATE:
            recommendations.extend([
                "Focus on sentence formation and fluency",
                "Practice describing pictures and situations",
                "Work on word-finding exercises",
                "Engage in simple conversations"
            ])
        else:  # MILD
            recommendations.extend([
                "Practice complex sentences and narratives",
                "Work on abstract concepts and explanations",
                "Focus on fluency and natural speech patterns",
                "Engage in detailed conversations and storytelling"
            ])
        
        # Add specific recommendations based on accuracy patterns
        if results:
            avg_accuracy = sum(r.get('accuracy', 0) for r in results) / len(results)
            if avg_accuracy < 30:
                recommendations.append("Focus on slower, more deliberate speech")
            elif avg_accuracy < 60:
                recommendations.append("Practice word repetition and rhythm")
            else:
                recommendations.append("Work on speech naturalness and flow")
        
        return recommendations[:4]  # Return top 4 recommendations
    
    def get_practice_difficulty(self, severity: SeverityLevel) -> str:
        """Get recommended practice difficulty based on severity"""
        
        difficulty_map = {
            SeverityLevel.VERY_SEVERE: "easy",
            SeverityLevel.SEVERE: "easy", 
            SeverityLevel.MODERATE: "medium",
            SeverityLevel.MILD: "hard"
        }
        
        return difficulty_map.get(severity, "easy")
    
    def get_session_length(self, severity: SeverityLevel) -> int:
        """Get recommended session length in minutes"""
        
        length_map = {
            SeverityLevel.VERY_SEVERE: 10,
            SeverityLevel.SEVERE: 15,
            SeverityLevel.MODERATE: 20,
            SeverityLevel.MILD: 25
        }
        
        return length_map.get(severity, 15)
    
    def get_words_per_session(self, severity: SeverityLevel) -> int:
        """Get recommended number of words per session"""
        
        words_map = {
            SeverityLevel.VERY_SEVERE: 3,
            SeverityLevel.SEVERE: 5,
            SeverityLevel.MODERATE: 8,
            SeverityLevel.MILD: 10
        }
        
        return words_map.get(severity, 5)

# Global instance
initial_assessment = InitialAssessment()
