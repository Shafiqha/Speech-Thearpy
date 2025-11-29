#!/usr/bin/env python3
"""
Feedback Reader - Converts text feedback to natural speech

Reads out assessment feedback in a human-like manner.
"""

import os
import re
from pathlib import Path
import argparse

try:
    from .simple_tts import ReliableTTS
except ImportError:
    from simple_tts import ReliableTTS


class FeedbackReader:
    """Converts feedback text to natural speech."""
    
    def __init__(self):
        self.tts = ReliableTTS()
    
    def clean_and_humanize_text(self, text: str) -> str:
        """Convert technical feedback text to natural speech."""
        
        # Remove emoji and special characters
        text = re.sub(r'[📊🎤🔍🏥🎯💡✅⚠️❌➕➖🔄📝🎵📚]', '', text)
        
        # Replace technical terms with natural language
        replacements = {
            'WAB-AQ Score': 'Western Aphasia Battery score',
            'WAB-AQ': 'Western Aphasia Battery',
            'COMPREHENSIVE SPEECH ANALYSIS RESULTS': 'Here are your speech analysis results',
            'SPEECH TRANSCRIPTION': 'First, let me tell you what I heard you say',
            'PRONUNCIATION ERROR ANALYSIS': 'Now, let me analyze your pronunciation errors',
            'SPEECH SEVERITY ASSESSMENT': 'Here is your speech severity assessment',
            'CORRECTIVE FEEDBACK & PRACTICE': 'Finally, here are some suggestions to help you improve',
            'Similarity Score': 'Your pronunciation similarity score is',
            'Error Type': 'The main type of error was',
            'Detected Errors': 'I detected the following errors',
            'Specific Feedback': 'Here is some specific feedback for you',
            'Severity Level': 'Your speech severity level is',
            'Confidence': 'I am',
            'Practice Suggestions': 'Here are some practice suggestions',
            'Target Text': 'You were supposed to say',
            'What You Said': 'But I heard you say',
            'Perfect match!': 'Excellent! You said it perfectly!',
            'Pronunciation differences detected': 'I noticed some differences in your pronunciation',
            'Could not transcribe speech': 'I had trouble understanding what you said',
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Clean up formatting
        text = re.sub(r'=+', '', text)  # Remove equal signs
        text = re.sub(r'-+', '', text)  # Remove dashes
        text = re.sub(r'•', '', text)   # Remove bullet points
        text = re.sub(r'\n+', '. ', text)  # Replace newlines with periods
        text = re.sub(r'\s+', ' ', text)   # Clean up multiple spaces
        
        # Add natural pauses
        text = text.replace(': ', '. ')
        text = text.replace('  💡 ', '. Additionally, ')
        text = text.replace('📝 ', 'You should ')
        
        # Make percentages more natural
        text = re.sub(r'(\d+\.\d+)%', r'\1 percent', text)
        text = re.sub(r'(\d+)%', r'\1 percent', text)
        
        # Make scores more natural
        text = re.sub(r'(\d+\.\d+)/100', r'\1 out of 100', text)
        
        # Clean up and add natural flow
        sentences = text.split('. ')
        cleaned_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 3:
                # Add natural connectors
                if 'You said' in sentence and 'instead of' in sentence:
                    sentence = sentence.replace('You said', 'I noticed you said')
                elif 'You missed' in sentence:
                    sentence = sentence.replace('You missed', 'It seems you missed')
                elif 'You added' in sentence:
                    sentence = sentence.replace('You added', 'I heard you add')
                
                cleaned_sentences.append(sentence)
        
        return '. '.join(cleaned_sentences) + '.'
    
    def create_natural_feedback_speech(self, feedback_text: str) -> str:
        """Create a natural, encouraging speech version of feedback."""
        
        # Clean the text
        clean_text = self.clean_and_humanize_text(feedback_text)
        
        # Add encouraging introduction
        intro = "Hello! I've analyzed your speech, and here's what I found. "
        
        # Add encouraging conclusion
        conclusion = " Remember, practice makes perfect, and every attempt helps you improve. Keep up the good work!"
        
        # Combine everything
        full_speech = intro + clean_text + conclusion
        
        # Final cleanup
        full_speech = re.sub(r'\.\s*\.', '.', full_speech)  # Remove double periods
        full_speech = re.sub(r'\s+', ' ', full_speech)      # Clean spaces
        
        return full_speech
    
    def read_feedback(self, feedback_text: str, output_path: str = "temp/feedback_speech.wav") -> bool:
        """Convert feedback text to speech and save as audio."""
        
        try:
            print("🔄 Converting feedback to natural speech...")
            
            # Create natural speech version
            speech_text = self.create_natural_feedback_speech(feedback_text)
            
            print(f"📝 Speech text preview:")
            print(f"   {speech_text[:100]}...")
            
            # Generate speech
            print("🎤 Generating speech audio...")
            audio = self.tts.synthesize(speech_text, language="en", save_path=output_path)
            
            if audio is not None:
                print(f"✅ Feedback speech saved to: {output_path}")
                print(f"🔊 You can now listen to your personalized feedback!")
                return True
            else:
                print("❌ Failed to generate speech")
                return False
                
        except Exception as e:
            print(f"❌ Error generating feedback speech: {e}")
            return False
    
    def read_custom_text(self, text: str, output_path: str = "temp/custom_speech.wav") -> bool:
        """Read any custom text aloud."""
        
        try:
            print(f"🔄 Converting text to speech...")
            print(f"📝 Text: {text[:100]}{'...' if len(text) > 100 else ''}")
            
            # Clean and naturalize
            natural_text = self.clean_and_humanize_text(text)
            
            # Generate speech
            audio = self.tts.synthesize(natural_text, language="en", save_path=output_path)
            
            if audio is not None:
                print(f"✅ Speech saved to: {output_path}")
                return True
            else:
                print("❌ Failed to generate speech")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Convert feedback text to natural speech")
    parser.add_argument('--text', '-t', help='Text to convert to speech')
    parser.add_argument('--file', '-f', help='Text file to read')
    parser.add_argument('--output', '-o', default='temp/feedback_speech.wav', 
                       help='Output audio file path')
    
    args = parser.parse_args()
    
    reader = FeedbackReader()
    
    if args.text:
        # Read provided text
        success = reader.read_custom_text(args.text, args.output)
        
    elif args.file:
        # Read from file
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                text = f.read()
            success = reader.read_feedback(text, args.output)
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return 1
            
    else:
        # Interactive mode
        print("🎤 FEEDBACK READER - Interactive Mode")
        print("="*50)
        print("Enter your feedback text (or 'quit' to exit):")
        print("You can paste multiple lines - press Enter twice when done.")
        
        while True:
            try:
                print("\n📝 Enter feedback text:")
                lines = []
                while True:
                    line = input()
                    if line.strip() == '':
                        break
                    if line.lower().strip() in ['quit', 'exit', 'q']:
                        print("👋 Goodbye!")
                        return 0
                    lines.append(line)
                
                if not lines:
                    continue
                
                text = '\n'.join(lines)
                
                # Ask for output filename
                output = input(f"\n💾 Output filename (default: {args.output}): ").strip()
                if not output:
                    output = args.output
                
                # Generate speech
                success = reader.read_feedback(text, output)
                
                if success:
                    print(f"\n🎉 Success! Your feedback has been converted to speech.")
                    print(f"🔊 Play the file: {output}")
                else:
                    print(f"\n❌ Failed to generate speech.")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    return 0


if __name__ == "__main__":
    exit(main())
