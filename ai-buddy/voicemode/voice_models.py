# File: voicemode/voice_models.py - Voice Processing Models

import os
import tempfile
import torch
from typing import Optional

class VoiceProcessor:
    """Voice processing with Whisper STT and Coqui TTS"""
    
    def __init__(self):
        self.models_ready = False
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.stt_method = None
        self.tts_method = None
        
        print(f"🔧 Initializing voice models on device: {self.device}")
        self._init_models()
    
    def _init_models(self):
        """Initialize STT and TTS models with fallbacks"""
        # Initialize Speech-to-Text
        self._init_stt()
        
        # Initialize Text-to-Speech
        self._init_tts()
        
        # Check if at least one method worked for each
        self.models_ready = (
            hasattr(self, 'whisper_model') or hasattr(self, 'recognizer')
        ) and (
            hasattr(self, 'tts_model') or hasattr(self, 'tts_engine')
        )
        
        if self.models_ready:
            print("✅ Voice models initialized successfully!")
            print(f"📝 STT Method: {self.stt_method}")
            print(f"🔊 TTS Method: {self.tts_method}")
        else:
            print("❌ Failed to initialize voice models")
    
    def _init_stt(self):
        """Initialize Speech-to-Text models"""
        # Try faster-whisper first (best quality)
        try:
            from faster_whisper import WhisperModel
            print("🎤 Loading Whisper model...")
            
            # Use base model for FYP (good balance of speed/quality)
            self.whisper_model = WhisperModel(
                "base", 
                device=self.device,
                compute_type="float16" if self.device == 'cuda' else "int8"
            )
            self.stt_method = "faster_whisper"
            print("✅ Faster-Whisper loaded successfully")
            return
            
        except Exception as e:
            print(f"⚠️ Faster-Whisper failed: {e}")
        
        # Fallback to SpeechRecognition
        try:
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = 300  # Adjust for better recognition
            self.recognizer.dynamic_energy_threshold = True
            self.stt_method = "speech_recognition"
            print("✅ SpeechRecognition loaded as fallback")
            
        except Exception as e:
            print(f"❌ SpeechRecognition fallback failed: {e}")
    
    def _init_tts(self):
        """Initialize Text-to-Speech models"""
        # Try Coqui TTS first (best quality)
        try:
            from TTS.api import TTS
            print("🔊 Loading TTS model...")
            
            # Use a fast, lightweight model for FYP
            model_name = "tts_models/en/ljspeech/tacotron2-DDC"
            self.tts_model = TTS(model_name, progress_bar=False)
            
            # Move to device if GPU available
            if self.device == 'cuda':
                self.tts_model = self.tts_model.to(self.device)
            
            self.tts_method = "coqui_tts"
            print("✅ Coqui TTS loaded successfully")
            return
            
        except Exception as e:
            print(f"⚠️ Coqui TTS failed: {e}")
        
        # Fallback to pyttsx3
        try:
            import pyttsx3
            self.tts_engine = pyttsx3.init()
            
            # Configure voice settings
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # Try to use a female voice if available
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
            
            # Set speech rate and volume
            self.tts_engine.setProperty('rate', 150)  # Speed of speech
            self.tts_engine.setProperty('volume', 0.9)  # Volume level
            
            self.tts_method = "pyttsx3"
            print("✅ pyttsx3 loaded as fallback")
            
        except Exception as e:
            print(f"❌ pyttsx3 fallback failed: {e}")
    
    def transcribe(self, audio_path: str) -> str:
        """
        Transcribe audio file to text
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text or empty string if failed
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        try:
            if self.stt_method == "faster_whisper" and hasattr(self, 'whisper_model'):
                return self._transcribe_whisper(audio_path)
            elif self.stt_method == "speech_recognition" and hasattr(self, 'recognizer'):
                return self._transcribe_speech_recognition(audio_path)
            else:
                raise Exception("No STT method available")
                
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            raise e
    
    def _transcribe_whisper(self, audio_path: str) -> str:
        """Transcribe using faster-whisper"""
        segments, info = self.whisper_model.transcribe(
            audio_path,
            beam_size=5,
            language="en",  # Force English for consistency
            condition_on_previous_text=False
        )
        
        # Combine all segments
        transcription = " ".join(segment.text for segment in segments).strip()
        
        # Clean up transcription
        transcription = self._clean_transcription(transcription)
        
        return transcription
    
    def _transcribe_speech_recognition(self, audio_path: str) -> str:
        """Transcribe using SpeechRecognition (Google)"""
        import speech_recognition as sr
        
        with sr.AudioFile(audio_path) as source:
            # Adjust for ambient noise
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            # Record the audio
            audio = self.recognizer.record(source)
        
        # Try Google Speech Recognition
        try:
            transcription = self.recognizer.recognize_google(audio)
            return self._clean_transcription(transcription)
        except sr.UnknownValueError:
            return "Could not understand audio"
        except sr.RequestError:
            # Fallback to offline recognition if available
            try:
                transcription = self.recognizer.recognize_sphinx(audio)
                return self._clean_transcription(transcription)
            except:
                return "Speech recognition service unavailable"
    
    def _clean_transcription(self, text: str) -> str:
        """Clean and normalize transcription"""
        if not text:
            return ""
        
        # Basic cleaning
        text = text.strip()
        
        # Remove common transcription artifacts
        text = text.replace("  ", " ")  # Double spaces
        
        # Capitalize first letter
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
        
        # Add period if missing
        if text and text[-1] not in '.!?':
            text += "."
        
        return text
    
    def synthesize(self, text: str) -> str:
        """
        Convert text to speech and return audio file path
        
        Args:
            text: Text to convert to speech
            
        Returns:
            Path to generated audio file
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        text = text.strip()
        
        # Limit text length for performance
        if len(text) > 2000:
            text = text[:2000] + "..."
        
        try:
            if self.tts_method == "coqui_tts" and hasattr(self, 'tts_model'):
                return self._synthesize_coqui(text)
            elif self.tts_method == "pyttsx3" and hasattr(self, 'tts_engine'):
                return self._synthesize_pyttsx3(text)
            else:
                raise Exception("No TTS method available")
                
        except Exception as e:
            print(f"❌ TTS error: {e}")
            raise e
    
    def _synthesize_coqui(self, text: str) -> str:
        """Synthesize using Coqui TTS"""
        # Create temporary file for output
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            output_path = tmp_file.name
        
        # Generate speech
        self.tts_model.tts_to_file(
            text=text,
            file_path=output_path
        )
        
        return output_path
    
    def _synthesize_pyttsx3(self, text: str) -> str:
        """Synthesize using pyttsx3"""
        # Create temporary file for output
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            output_path = tmp_file.name
        
        # Generate speech
        self.tts_engine.save_to_file(text, output_path)
        self.tts_engine.runAndWait()
        
        return output_path
    
    def test_pipeline(self) -> dict:
        """Test the complete voice pipeline"""
        try:
            test_text = "This is a test of the voice processing system."
            
            # Test TTS
            audio_path = self.synthesize(test_text)
            
            # Test STT
            transcription = self.transcribe(audio_path)
            
            # Clean up
            os.unlink(audio_path)
            
            return {
                "success": True,
                "original_text": test_text,
                "transcription": transcription,
                "stt_method": self.stt_method,
                "tts_method": self.tts_method
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stt_method": self.stt_method,
                "tts_method": self.tts_method
            }

# Test function for standalone testing
if __name__ == "__main__":
    print("🧪 Testing Voice Processor...")
    
    processor = VoiceProcessor()
    
    if processor.models_ready:
        print("✅ Models loaded successfully!")
        
        # Test the pipeline
        result = processor.test_pipeline()
        print("\n🔄 Pipeline Test Results:")
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Original: {result['original_text']}")
            print(f"Transcribed: {result['transcription']}")
        else:
            print(f"Error: {result['error']}")
    else:
        print("❌ Failed to load models")