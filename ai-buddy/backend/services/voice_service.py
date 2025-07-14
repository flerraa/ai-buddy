# File: backend/services/voice_service.py - HTTP-based Voice Service

from typing import Dict, List, Any, Optional
import requests
import logging
import re
from .base import BaseService, ServiceResponse
from .chat import ChatService
from ..config import settings
from ..utils import TextProcessor

logger = logging.getLogger(__name__)

class VoiceService(BaseService):
    """Voice-specific AI service for quiz interactions using HTTP calls to voicemode"""
    
    def __init__(self):
        # Use base collection (not storing voice data in DB)
        super().__init__("voice_interactions")  
        self.chat_service = ChatService()
        self.text_processor = TextProcessor()
        self.voice_service_url = settings.VOICE_SERVICE_URL
        self._voice_available = None  # Cache availability check
    
    def check_voice_service_available(self) -> bool:
        """Check if voicemode service is running and ready"""
        if self._voice_available is not None:
            return self._voice_available  # Use cached result
        
        try:
            response = requests.get(
                f"{self.voice_service_url}/health", 
                timeout=3
            )
            if response.status_code == 200:
                data = response.json()
                self._voice_available = data.get("models_loaded", False)
                self.log_info(f"Voice service available: {self._voice_available}")
                return self._voice_available
        except Exception as e:
            self.log_warning(f"Voice service not available: {e}")
        
        self._voice_available = False
        return False
    
    def get_voice_response(self, 
                          user_text: str, 
                          user_id: str, 
                          pdf_id: str,
                          quiz_questions: List[Dict], 
                          quiz_type: str,
                          quiz_answers: Dict,
                          quiz_completed: bool) -> ServiceResponse:
        """
        Generate SHORT voice response for quiz interactions
        
        Args:
            user_text: What user said via voice
            user_id: Current user ID
            pdf_id: Current PDF ID
            quiz_questions: List of quiz questions
            quiz_type: "MCQ" or "Open-ended"
            quiz_answers: Current user answers
            quiz_completed: Whether quiz is finished
            
        Returns:
            ServiceResponse with short voice response (20-30 words)
        """
        try:
            # Check if voice service is available
            if not self.check_voice_service_available():
                return ServiceResponse.error_response(
                    "Voice service not available", 
                    {"fallback_text": "Voice service is not running. Please start voicemode service."}
                )
            
            # Create minimal context (no conversation history for voice)
            quiz_context = self._create_minimal_quiz_context(
                quiz_questions, quiz_type, quiz_answers, quiz_completed
            )
            
            # Check if asking for direct answers
            is_asking_for_answer = self._is_asking_for_direct_answer(user_text)
            
            # Generate appropriate prompt based on context
            if is_asking_for_answer and not quiz_completed:
                # Guide without revealing answers - VOICE OPTIMIZED
                prompt = f"""
                Student asked via voice: "{user_text}"
                
                VOICE RESPONSE RULES:
                - Keep under 25 words
                - Sound natural when spoken aloud
                - Give conceptual hints only, no direct answers
                - Be encouraging and conversational
                - No formatting or bullet points
                
                Quiz context: {quiz_context}
                
                Give a SHORT spoken hint that helps them think without revealing the answer.
                """
            else:
                # Normal tutoring - VOICE OPTIMIZED  
                prompt = f"""
                Student asked via voice: "{user_text}"
                
                VOICE RESPONSE RULES:
                - Keep under 30 words
                - Sound natural and conversational when spoken
                - Be helpful and encouraging
                - No bullet points, formatting, or technical language
                - Speak as if talking to a friend
                
                Quiz context: {quiz_context}
                
                Give a SHORT conversational response as if speaking to them directly.
                """
            
            # Get response from chat service
            result = self.chat_service.chat_with_pdf(
                user_id, pdf_id, prompt, "Tutor"
            )
            
            if result.success:
                raw_response = result.data['response']
                # Clean and optimize for voice
                voice_response = self._optimize_for_voice(raw_response)
                word_count = len(voice_response.split())
                
                self.log_info(f"Voice response generated: {word_count} words")
                
                return ServiceResponse.success_response(
                    "Voice response generated", 
                    {
                        "response": voice_response, 
                        "word_count": word_count,
                        "voice_ready": True
                    }
                )
            else:
                # Fallback response
                fallback = "I'm not sure about that. Can you try asking differently?"
                return ServiceResponse.success_response(
                    "Fallback response", 
                    {
                        "response": fallback, 
                        "word_count": len(fallback.split()),
                        "voice_ready": True
                    }
                )
                
        except Exception as e:
            self.log_error("Error generating voice response", e)
            # Always provide a response for voice
            error_response = "Sorry, I had trouble with that question."
            return ServiceResponse.success_response(
                "Error fallback", 
                {
                    "response": error_response, 
                    "word_count": len(error_response.split()),
                    "voice_ready": True
                }
            )
    
    def transcribe_audio_via_voicemode(self, audio_file) -> ServiceResponse:
        """
        Transcribe audio using voicemode service
        
        Args:
            audio_file: Audio file object (BytesIO or similar)
            
        Returns:
            ServiceResponse with transcription result
        """
        try:
            if not self.check_voice_service_available():
                return ServiceResponse.error_response("Voice service not available")
            
            # Prepare file for upload
            files = {"audio": ("recording.wav", audio_file, "audio/wav")}
            
            # Call voicemode transcription endpoint
            response = requests.post(
                f"{self.voice_service_url}/transcribe",
                files=files,
                timeout=30  # Give enough time for transcription
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    transcription = data.get("transcription", "").strip()
                    self.log_info(f"Transcription successful: {transcription[:50]}...")
                    
                    return ServiceResponse.success_response(
                        "Transcription successful",
                        {
                            "transcription": transcription,
                            "method": data.get("method", "unknown"),
                            "audio_size": data.get("audio_size_bytes", 0)
                        }
                    )
                else:
                    error_msg = data.get("error", "Unknown transcription error")
                    self.log_error(f"Transcription failed: {error_msg}")
                    return ServiceResponse.error_response(f"Transcription failed: {error_msg}")
            else:
                self.log_error(f"Voice service HTTP error: {response.status_code}")
                return ServiceResponse.error_response(f"Voice service error: HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            self.log_error("Voice service timeout during transcription")
            return ServiceResponse.error_response("Voice service timeout - try shorter audio")
        except requests.exceptions.ConnectionError:
            self.log_error("Cannot connect to voice service")
            return ServiceResponse.error_response("Voice service not reachable")
        except Exception as e:
            self.log_error("Error in voice transcription", e)
            return ServiceResponse.error_response(f"Transcription error: {str(e)}")
    
    def synthesize_speech_via_voicemode(self, text: str) -> ServiceResponse:
        """
        Convert text to speech using voicemode service
        
        Args:
            text: Text to convert to speech
            
        Returns:
            ServiceResponse with audio data (base64) or error
        """
        try:
            if not self.check_voice_service_available():
                return ServiceResponse.error_response("Voice service not available")
            
            # Limit text length for voice
            if len(text) > 200:
                text = text[:200] + "..."
            
            # Call voicemode synthesis endpoint
            response = requests.post(
                f"{self.voice_service_url}/synthesize_simple",
                params={"text": text},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    audio_b64 = data.get("audio_base64", "")
                    self.log_info(f"Speech synthesis successful: {len(text)} chars")
                    
                    return ServiceResponse.success_response(
                        "Speech synthesis successful",
                        {
                            "audio_base64": audio_b64,
                            "method": data.get("method", "unknown"),
                            "text_length": len(text),
                            "audio_size": data.get("audio_size_bytes", 0)
                        }
                    )
                else:
                    error_msg = data.get("error", "Unknown synthesis error")
                    self.log_error(f"Speech synthesis failed: {error_msg}")
                    return ServiceResponse.error_response(f"Speech synthesis failed: {error_msg}")
            else:
                self.log_error(f"Voice service HTTP error: {response.status_code}")
                return ServiceResponse.error_response(f"Voice service error: HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            self.log_error("Voice service timeout during synthesis")
            return ServiceResponse.error_response("Voice service timeout")
        except requests.exceptions.ConnectionError:
            self.log_error("Cannot connect to voice service for synthesis")
            return ServiceResponse.error_response("Voice service not reachable")
        except Exception as e:
            self.log_error("Error in voice synthesis", e)
            return ServiceResponse.error_response(f"Speech synthesis error: {str(e)}")
    
    def test_voice_service(self) -> ServiceResponse:
        """Test the voicemode service pipeline"""
        try:
            if not self.check_voice_service_available():
                return ServiceResponse.error_response("Voice service not available")
            
            # Call voicemode test endpoint
            response = requests.post(
                f"{self.voice_service_url}/test",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_info(f"Voice service test: {data.get('success', False)}")
                
                return ServiceResponse.success_response(
                    "Voice service test completed",
                    {
                        "test_success": data.get("success", False),
                        "similarity_score": data.get("similarity_score", 0),
                        "stt_method": data.get("stt_method", "unknown"),
                        "tts_method": data.get("tts_method", "unknown"),
                        "error": data.get("error") if not data.get("success") else None
                    }
                )
            else:
                return ServiceResponse.error_response(f"Voice service test failed: HTTP {response.status_code}")
                
        except Exception as e:
            self.log_error("Error testing voice service", e)
            return ServiceResponse.error_response(f"Voice test error: {str(e)}")
    
    def _create_minimal_quiz_context(self, 
                                   quiz_questions: List[Dict], 
                                   quiz_type: str,
                                   quiz_answers: Dict,
                                   quiz_completed: bool) -> str:
        """Create minimal context for voice (no conversation history)"""
        context = f"Quiz Type: {quiz_type}, "
        context += f"Total Questions: {len(quiz_questions)}, "
        context += f"Answered: {len(quiz_answers)}, "
        context += f"Completed: {quiz_completed}"
        
        # Add current question if relevant
        if quiz_answers and not quiz_completed and quiz_questions:
            try:
                last_answered = max(quiz_answers.keys())
                if last_answered <= len(quiz_questions):
                    # Find question by number
                    current_q = None
                    for q in quiz_questions:
                        if q.get('number') == last_answered:
                            current_q = q
                            break
                    
                    if current_q:
                        context += f", Current: {current_q['question'][:50]}..."
            except Exception:
                pass  # Skip if can't determine current question
        
        return context
    
    def _is_asking_for_direct_answer(self, user_text: str) -> bool:
        """Detect if student is asking for a direct answer"""
        user_text_lower = user_text.lower()
        
        direct_answer_patterns = [
            r'\bis\s+[a-d]\s+correct',
            r'\bwhat.*answer',
            r'\bwhich.*correct', 
            r'\bwhat.*right',
            r'\btell me.*answer',
            r'\bwhat.*letter',
            r'\bshould i choose',
            r'\bgive me.*answer',
            r'\bwhats.*answer',
            r'\bwhat is.*answer'
        ]
        
        for pattern in direct_answer_patterns:
            if re.search(pattern, user_text_lower):
                return True
        
        return False
    
    def _optimize_for_voice(self, response: str) -> str:
        """Clean and optimize response for voice output - make it SHORT and natural"""
        if not response:
            return "I'm not sure about that."
        
        # Remove markdown and formatting
        response = re.sub(r'\*\*([^*]+)\*\*', r'\1', response)  # Remove **bold**
        response = re.sub(r'\*([^*]+)\*', r'\1', response)      # Remove *italic*
        response = re.sub(r'#{1,6}\s+', '', response)           # Remove headers
        response = re.sub(r'`([^`]+)`', r'\1', response)        # Remove code marks
        response = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', response)  # Remove links
        
        # Remove bullet points and lists
        response = re.sub(r'^\s*[-•*]\s+', '', response, flags=re.MULTILINE)
        response = re.sub(r'^\s*\d+\.\s+', '', response, flags=re.MULTILINE)
        
        # Clean up multiple spaces and newlines
        response = re.sub(r'\n+', ' ', response)
        response = re.sub(r'\s+', ' ', response)
        
        # Split into sentences and take first 2 for voice
        sentences = [s.strip() for s in response.split('.') if s.strip()]
        if len(sentences) > 2:
            response = '. '.join(sentences[:2]) + '.'
        elif sentences:
            response = '. '.join(sentences)
            if not response.endswith('.'):
                response += '.'
        
        # Hard limit for voice - max 30 words
        words = response.split()
        if len(words) > 30:
            response = ' '.join(words[:30]) + '.'
        
        # Make more conversational for voice
        response = response.replace("The answer is", "I think")
        response = response.replace("According to", "Based on")
        response = response.replace("In conclusion", "So")
        response = response.replace("Therefore", "So")
        response = response.replace("However", "But")
        response = response.replace("Nevertheless", "Still")
        
        # Ensure it's not empty
        if not response.strip():
            response = "I'm not sure about that."
        
        return response.strip()
    
    def get_voice_service_status(self) -> Dict[str, Any]:
        """Get detailed status of voice service"""
        try:
            if not self.check_voice_service_available():
                return {
                    "available": False,
                    "url": self.voice_service_url,
                    "error": "Service not reachable"
                }
            
            # Get detailed status from voicemode
            response = requests.get(
                f"{self.voice_service_url}/models/status",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "available": True,
                    "url": self.voice_service_url,
                    "models_ready": data.get("models_ready", False),
                    "stt_method": data.get("stt_method", "unknown"),
                    "tts_method": data.get("tts_method", "unknown"),
                    "device": data.get("device", "unknown"),
                    "whisper_loaded": data.get("whisper_loaded", False),
                    "tts_loaded": data.get("tts_loaded", False)
                }
            else:
                return {
                    "available": False,
                    "url": self.voice_service_url,
                    "error": f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            return {
                "available": False,
                "url": self.voice_service_url,
                "error": str(e)
            }
    
    def clear_voice_cache(self):
        """Clear cached voice availability status"""
        self._voice_available = None
        self.log_info("Voice service availability cache cleared")
    
    def test_voice_optimization(self, test_text: str) -> Dict[str, Any]:
        """Test voice optimization function"""
        try:
            optimized = self._optimize_for_voice(test_text)
            word_count = len(optimized.split())
            
            return {
                "original": test_text,
                "optimized": optimized,
                "original_words": len(test_text.split()),
                "optimized_words": word_count,
                "under_limit": word_count <= 30,
                "voice_service_available": self.check_voice_service_available()
            }
        except Exception as e:
            return {"error": str(e)}