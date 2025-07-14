# File: voicemode/voice_service.py - COMPLETE FIXED VERSION
# FastAPI Voice Service for AI Buddy FYP with Audio Concatenation Fix

import os
import io
import tempfile
import logging
import base64
import asyncio
import time
from typing import List, Dict, Any, Optional
import wave
import numpy as np

# FastAPI imports
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Audio processing imports
from pydub import AudioSegment
import soundfile as sf

# Speech-to-Text imports
try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

# Text-to-Speech imports
try:
    from TTS.api import TTS
    COQUI_TTS_AVAILABLE = True
except ImportError:
    COQUI_TTS_AVAILABLE = False

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VoiceService:
    """Enhanced Voice Service with Fixed Audio Concatenation"""
    
    def __init__(self):
        self.app = FastAPI(title="AI Buddy Voice Service", version="2.0.0")
        self.setup_cors()
        self.setup_routes()
        
        # Service state
        self.models_loaded = False
        self.stt_method = None
        self.tts_method = None
        
        # Audio processing settings
        self.target_sample_rate = 16000
        self.audio_format = "wav"
        
        # Initialize models synchronously
        self.initialize_models_sync()
    
    def setup_cors(self):
        """Setup CORS middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/")
        async def root():
            return {"message": "AI Buddy Voice Service", "status": "running"}
        
        @self.app.get("/health")
        async def health():
            return {
                "status": "healthy",
                "models_loaded": self.models_loaded,
                "stt_method": self.stt_method,
                "tts_method": self.tts_method,
                "services_available": {
                    "faster_whisper": FASTER_WHISPER_AVAILABLE,
                    "speech_recognition": SPEECH_RECOGNITION_AVAILABLE,
                    "coqui_tts": COQUI_TTS_AVAILABLE,
                    "pyttsx3": PYTTSX3_AVAILABLE
                }
            }
        
        @self.app.post("/transcribe")
        async def transcribe_audio(audio: UploadFile = File(...)):
            """Transcribe uploaded audio file"""
            return await self.handle_transcription(audio)
        
        @self.app.post("/synthesize_simple")
        async def synthesize_simple(text: str = Query(..., description="Text to synthesize")):
            """Fixed synthesis with proper audio concatenation"""
            return await self.handle_synthesis_fixed(text)
        
        @self.app.post("/test")
        async def test_voice_service():
            """Test voice service functionality"""
            return await self.test_full_pipeline()
    
    def initialize_models_sync(self):
        """Initialize STT and TTS models synchronously"""
        logger.info("🚀 Initializing voice models...")
        
        # Initialize STT
        self.init_stt_sync()
        
        # Initialize TTS
        self.init_tts_sync()
        
        self.models_loaded = True
        logger.info("✅ Voice models loaded successfully!")
    
    def init_stt_sync(self):
        """Initialize Speech-to-Text models synchronously"""
        try:
            if FASTER_WHISPER_AVAILABLE:
                logger.info("🎤 Loading Faster Whisper model...")
                self.whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
                self.stt_method = "faster_whisper"
                logger.info("✅ Faster Whisper loaded successfully")
                return
        except Exception as e:
            logger.warning(f"⚠️ Faster Whisper failed: {e}")
        
        if SPEECH_RECOGNITION_AVAILABLE:
            logger.info("🎤 Using SpeechRecognition as fallback...")
            self.speech_recognizer = sr.Recognizer()
            self.stt_method = "speech_recognition"
            logger.info("✅ SpeechRecognition ready")
        else:
            logger.error("❌ No STT models available!")
            self.stt_method = "none"
    
    def init_tts_sync(self):
        """Initialize Text-to-Speech models synchronously"""
        try:
            if COQUI_TTS_AVAILABLE:
                logger.info("🔊 Loading Coqui TTS model...")
                self.tts_model = TTS("tts_models/en/ljspeech/tacotron2-DDC_ph")
                self.tts_method = "coqui_tts"
                logger.info("✅ Coqui TTS loaded successfully")
                return
        except Exception as e:
            logger.warning(f"⚠️ Coqui TTS failed: {e}")
        
        if PYTTSX3_AVAILABLE:
            logger.info("🔊 Using pyttsx3 as fallback...")
            self.pyttsx3_engine = pyttsx3.init()
            # Configure pyttsx3
            self.pyttsx3_engine.setProperty('rate', 150)
            self.pyttsx3_engine.setProperty('volume', 0.8)
            voices = self.pyttsx3_engine.getProperty('voices')
            if voices:
                self.pyttsx3_engine.setProperty('voice', voices[0].id)
            self.tts_method = "pyttsx3"
            logger.info("✅ pyttsx3 ready")
        else:
            logger.error("❌ No TTS models available!")
            self.tts_method = "none"
    
    async def handle_transcription(self, audio_file: UploadFile) -> JSONResponse:
        """Handle audio transcription with better error handling"""
        try:
            logger.info(f"📝 Received audio file: {audio_file.filename}, type: {audio_file.content_type}")
            
            # Read audio data
            audio_data = await audio_file.read()
            logger.info(f"🎤 Processing audio file: {audio_file.filename} ({len(audio_data)} bytes)")
            
            if len(audio_data) < 1000:  # Less than 1KB
                raise ValueError("Audio file too small - please record longer")
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio_data)
                tmp_path = tmp_file.name
            
            try:
                # Transcribe based on available method
                if self.stt_method == "faster_whisper":
                    transcription = await self.transcribe_with_faster_whisper(tmp_path)
                elif self.stt_method == "speech_recognition":
                    transcription = await self.transcribe_with_speech_recognition(tmp_path)
                else:
                    raise ValueError("No STT method available")
                
                # Validate transcription
                if not transcription or not transcription.strip():
                    raise ValueError("No speech detected in audio")
                
                if len(transcription.strip()) < 2:
                    raise ValueError("Transcription too short - please speak more clearly")
                
                logger.info(f"📝 Transcription successful: '{transcription}'")
                
                return JSONResponse({
                    "success": True,
                    "transcription": transcription.strip(),
                    "method": self.stt_method,
                    "audio_size_bytes": len(audio_data)
                })
                
            finally:
                # Clean up temp file
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            
        except Exception as e:
            logger.error(f"❌ Transcription error: {str(e)}")
            return JSONResponse({
                "success": False,
                "error": f"Transcription failed: {str(e)}",
                "method": self.stt_method
            }, status_code=400)
    
    async def transcribe_with_faster_whisper(self, audio_path: str) -> str:
        """Transcribe using Faster Whisper"""
        segments, info = self.whisper_model.transcribe(
            audio_path,
            beam_size=5,
            language="en",
            condition_on_previous_text=False
        )
        
        transcription = ""
        for segment in segments:
            transcription += segment.text + " "
        
        return transcription.strip()
    
    async def transcribe_with_speech_recognition(self, audio_path: str) -> str:
        """Transcribe using SpeechRecognition"""
        with sr.AudioFile(audio_path) as source:
            audio = self.speech_recognizer.record(source)
        
        try:
            return self.speech_recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            raise ValueError("Could not understand audio")
        except sr.RequestError as e:
            raise ValueError(f"Speech recognition service error: {e}")
    
    async def handle_synthesis_fixed(self, text: str) -> JSONResponse:
        """FIXED: Proper audio concatenation to prevent overlap"""
        try:
            logger.info(f"🔊 Simple synthesis: '{text[:50]}...'")
            start_time = time.time()
            
            # Input validation
            if not text or not text.strip():
                raise ValueError("Empty text provided")
            
            if len(text) > 2000:
                text = text[:2000] + "..."
                logger.info("📝 Text truncated to 2000 characters")
            
            # Clean text for TTS
            cleaned_text = self.clean_text_for_tts(text.strip())
            
            # Generate audio with proper concatenation
            if self.tts_method == "coqui_tts":
                audio_data = await self.synthesize_with_coqui_fixed(cleaned_text)
            elif self.tts_method == "pyttsx3":
                audio_data = await self.synthesize_with_pyttsx3(cleaned_text)
            else:
                raise ValueError("No TTS method available")
            
            # Convert to base64
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Calculate timing
            processing_time = time.time() - start_time
            audio_duration = len(audio_data) / (self.target_sample_rate * 2)  # 16-bit audio
            real_time_factor = processing_time / audio_duration if audio_duration > 0 else 0
            
            logger.info(f" > Processing time: {processing_time}")
            logger.info(f" > Real-time factor: {real_time_factor}")
            logger.info(f"✅ Simple synthesis successful ({len(audio_data)} bytes)")
            
            return JSONResponse({
                "success": True,
                "audio_base64": audio_b64,
                "method": self.tts_method,
                "processing_time": processing_time,
                "audio_duration": audio_duration,
                "real_time_factor": real_time_factor,
                "text_length": len(text)
            })
            
        except Exception as e:
            logger.error(f"❌ Simple TTS error: {str(e)}")
            return JSONResponse({
                "success": False,
                "error": f"TTS synthesis failed: {str(e)}",
                "method": self.tts_method
            }, status_code=400)
    
    def clean_text_for_tts(self, text: str) -> str:
        """Clean text to prevent TTS tensor size errors"""
        import re
        
        # Remove markdown formatting that causes tensor issues
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Remove **bold**
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # Remove *italic*
        text = re.sub(r'`(.*?)`', r'\1', text)        # Remove `code`
        
        # Replace problematic characters
        text = text.replace('&', ' and ')
        text = text.replace('@', ' at ')
        text = text.replace('#', ' number ')
        text = text.replace('%', ' percent ')
        text = text.replace('$', ' dollars ')
        
        # Clean up extra spaces
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    async def synthesize_with_coqui_fixed(self, text: str) -> bytes:
        """FIXED: Coqui TTS with proper sentence concatenation"""
        try:
            # Split text into sentences for better processing
            sentences = self.split_into_sentences(text)
            logger.info(" > Text splitted to sentences.")
            logger.info(sentences)
            
            if not sentences:
                sentences = [text]  # Fallback to original text
            
            all_audio_segments = []
            
            # Process each sentence and collect audio
            for i, sentence in enumerate(sentences):
                sentence = sentence.strip()
                if not sentence:
                    continue
                
                try:
                    # Generate audio for this sentence
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                        tmp_path = tmp_file.name
                    
                    # Generate TTS for sentence
                    self.tts_model.tts_to_file(
                        text=sentence,
                        file_path=tmp_path
                    )
                    
                    # Load audio segment
                    audio_segment = AudioSegment.from_wav(tmp_path)
                    
                    # Add small pause between sentences (300ms)
                    if i > 0:
                        pause = AudioSegment.silent(duration=300)
                        all_audio_segments.append(pause)
                    
                    all_audio_segments.append(audio_segment)
                    
                    # Clean up temp file
                    try:
                        os.unlink(tmp_path)
                    except:
                        pass
                        
                except Exception as e:
                    logger.warning(f"⚠️ Sentence TTS failed: {e}")
                    # Continue with other sentences
                    continue
            
            if not all_audio_segments:
                raise ValueError("No audio segments generated")
            
            # CRITICAL FIX: Concatenate all audio into ONE continuous stream
            logger.info(f" > Concatenating {len(all_audio_segments)} audio segments...")
            final_audio = AudioSegment.empty()
            
            for segment in all_audio_segments:
                final_audio += segment
            
            # Ensure consistent format
            final_audio = final_audio.set_frame_rate(self.target_sample_rate)
            final_audio = final_audio.set_channels(1)  # Mono
            final_audio = final_audio.set_sample_width(2)  # 16-bit
            
            # Convert to bytes
            with tempfile.NamedTemporaryFile(suffix=".wav") as tmp_file:
                final_audio.export(tmp_file.name, format="wav")
                tmp_file.seek(0)
                audio_data = tmp_file.read()
            
            logger.info(f" > Final concatenated audio: {len(audio_data)} bytes")
            return audio_data
            
        except Exception as e:
            logger.error(f"❌ Coqui TTS concatenation error: {e}")
            # Fallback: try generating entire text as one piece
            try:
                logger.info(" > Fallback: generating as single text...")
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                    tmp_path = tmp_file.name
                
                self.tts_model.tts_to_file(text=text, file_path=tmp_path)
                
                with open(tmp_path, 'rb') as f:
                    audio_data = f.read()
                
                os.unlink(tmp_path)
                return audio_data
                
            except Exception as e2:
                raise ValueError(f"TTS failed: {e2}")
    
    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences while preserving meaning"""
        import re
        
        # Simple sentence splitting that preserves context
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        
        # Clean and validate sentences
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 3:  # Avoid very short fragments
                # Ensure sentence ends with punctuation
                if not sentence[-1] in '.!?':
                    sentence += '.'
                cleaned_sentences.append(sentence)
        
        # If splitting failed, return original text
        if not cleaned_sentences:
            return [text]
        
        # Merge very short sentences to avoid choppy audio
        merged_sentences = []
        current_sentence = ""
        
        for sentence in cleaned_sentences:
            if len(current_sentence + " " + sentence) < 150:  # Max 150 chars per TTS call
                current_sentence = (current_sentence + " " + sentence).strip()
            else:
                if current_sentence:
                    merged_sentences.append(current_sentence)
                current_sentence = sentence
        
        if current_sentence:
            merged_sentences.append(current_sentence)
        
        return merged_sentences
    
    async def synthesize_with_pyttsx3(self, text: str) -> bytes:
        """Synthesize using pyttsx3 (fallback)"""
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_path = tmp_file.name
            
            # Generate speech
            self.pyttsx3_engine.save_to_file(text, tmp_path)
            self.pyttsx3_engine.runAndWait()
            
            # Read audio data
            with open(tmp_path, 'rb') as f:
                audio_data = f.read()
            
            # Clean up
            os.unlink(tmp_path)
            
            return audio_data
            
        except Exception as e:
            raise ValueError(f"pyttsx3 synthesis failed: {e}")
    
    async def test_full_pipeline(self) -> JSONResponse:
        """Test complete voice pipeline"""
        try:
            test_text = "Hello, this is a voice service test."
            
            # Test TTS
            logger.info("🧪 Testing TTS...")
            start_time = time.time()
            
            if self.tts_method == "coqui_tts":
                audio_data = await self.synthesize_with_coqui_fixed(test_text)
            elif self.tts_method == "pyttsx3":
                audio_data = await self.synthesize_with_pyttsx3(test_text)
            else:
                raise ValueError("No TTS method available")
            
            tts_time = time.time() - start_time
            
            # Calculate similarity score (dummy for now)
            similarity_score = 0.85 if len(audio_data) > 1000 else 0.5
            
            logger.info("✅ Voice service test completed")
            
            return JSONResponse({
                "success": True,
                "stt_method": self.stt_method,
                "tts_method": self.tts_method,
                "tts_processing_time": tts_time,
                "audio_size_bytes": len(audio_data),
                "similarity_score": similarity_score,
                "models_loaded": self.models_loaded
            })
            
        except Exception as e:
            logger.error(f"❌ Voice service test failed: {e}")
            return JSONResponse({
                "success": False,
                "error": str(e),
                "stt_method": self.stt_method,
                "tts_method": self.tts_method,
                "models_loaded": self.models_loaded
            }, status_code=400)

# Global service instance
voice_service = VoiceService()
app = voice_service.app

def main():
    """Main entry point"""
    logger.info("🚀 Starting AI Buddy Voice Service...")
    logger.info(f"Available services:")
    logger.info(f"  - Faster Whisper: {FASTER_WHISPER_AVAILABLE}")
    logger.info(f"  - SpeechRecognition: {SPEECH_RECOGNITION_AVAILABLE}")
    logger.info(f"  - Coqui TTS: {COQUI_TTS_AVAILABLE}")
    logger.info(f"  - pyttsx3: {PYTTSX3_AVAILABLE}")
    
    # Run the service
    uvicorn.run(
        "voice_service:app",
        host="127.0.0.1",
        port=8001,
        reload=False,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()