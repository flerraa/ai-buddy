# File: frontend/components/voice_interface.py
# ENHANCED: Voice Interface with Better Logical Responses and Audio State Management

import streamlit as st
from typing import Dict, List, Any, Optional, Callable
import requests
import base64
import io
import time
import hashlib

# Audio recorder import with fallback
try:
    from audio_recorder_streamlit import audio_recorder
    AUDIO_RECORDER_AVAILABLE = True
except ImportError:
    AUDIO_RECORDER_AVAILABLE = False

class VoiceInterface:
    """Enhanced Voice Interface - Better Logic + No Auto-Loop Issue"""
    
    def __init__(self, voice_service_url: str = "http://127.0.0.1:8001"):
        self.voice_service_url = voice_service_url
        self.voice_available = self._check_voice_service()
        self.audio_recorder_available = AUDIO_RECORDER_AVAILABLE
    
    def _check_voice_service(self) -> bool:
        """Check if voice service is running"""
        try:
            response = requests.get(f"{self.voice_service_url}/health", timeout=3)
            if response.status_code == 200:
                data = response.json()
                models_loaded = data.get("models_loaded", False)
                return models_loaded
            return False
        except:
            return False
    
    def render_voice_chat(self, 
                         message_callback: Callable[[str], str],
                         conversation_key: str = "voice_conversation",
                         container_key: str = "default",
                         quiz_context: Optional[Dict] = None) -> bool:
        """
        Render complete voice chat interface with FIXED audio loop prevention
        """
        
        # Check prerequisites
        if not self.audio_recorder_available:
            st.error("❌ audio-recorder-streamlit not installed")
            st.code("pip install audio-recorder-streamlit>=0.0.8")
            return False
        
        if not self.voice_available:
            st.warning("⚠️ Voice service not available")
            st.info("💡 Start voice service: `cd voicemode && python voice_service.py`")
            return False
        
        # Initialize session state
        self._init_voice_state(conversation_key, container_key)
        
        # Show quiz context if provided
        if quiz_context:
            self._show_quiz_context(quiz_context, container_key)
        
        # Render the main interface
        return self._render_voice_interface(message_callback, conversation_key, container_key, quiz_context)
    
    def _init_voice_state(self, conversation_key: str, container_key: str):
        """Initialize voice-related session state with audio tracking"""
        if conversation_key not in st.session_state:
            st.session_state[conversation_key] = []
        
        # Voice state keys - CRITICAL: Add audio tracking
        state_keys = {
            f"voice_processing_{container_key}": False,
            f"voice_error_{container_key}": None,
            f"voice_error_time_{container_key}": None,
            f"processed_audio_hashes_{container_key}": set(),  # CRITICAL: Track processed audio
            f"last_audio_hash_{container_key}": None,  # CRITICAL: Last audio hash
        }
        
        for key, default_value in state_keys.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    def _show_quiz_context(self, quiz_context: Dict, container_key: str):
        """Show ENHANCED quiz context with voice commands guide"""
        
        if quiz_context.get('current_question'):
            st.info(f"📝 {quiz_context['current_question']}")
        
        if quiz_context.get('quiz_type') and quiz_context.get('progress'):
            st.caption(f"🎯 {quiz_context['quiz_type']} Quiz • {quiz_context['progress']}")
        
        # Show voice command help instead of buttons
        with st.expander("🎤 Voice Commands You Can Use", expanded=False):
            st.markdown("""
            **Quick Help Commands:**
            - 🗣️ *"Break this down for me"*
            - 🗣️ *"What are the key terms here?"*
            - 🗣️ *"Give me a small hint"*
            - 🗣️ *"What's the approach for this?"*
            - 🗣️ *"What mistakes should I avoid?"*
            - 🗣️ *"Connect this to other topics"*
            - 🗣️ *"Explain this concept"*
            
            **Navigation Commands:**
            - 🗣️ *"How many questions left?"*
            - 🗣️ *"What's my progress?"*
            - 🗣️ *"How am I doing so far?"*
            """)
        
        # Single emergency help button
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("💬 *Just speak naturally - ask me anything about this question!*")
        with col2:
            if st.button("🆘 I'm Stuck", key=f"voice_help_{container_key}"):
                self._speak_response("I'm here to help! You can ask me to break down the question, explain key concepts, give you hints, or walk you through the approach. What would you like help with?")
        
        st.markdown("---")
    
    def _render_voice_interface(self, message_callback: Callable[[str], str],
                               conversation_key: str, container_key: str,
                               quiz_context: Optional[Dict] = None) -> bool:
        """Render the main voice interface with FIXED audio loop prevention"""
        
        # Get state keys
        processing_key = f"voice_processing_{container_key}"
        error_key = f"voice_error_{container_key}"
        error_time_key = f"voice_error_time_{container_key}"
        
        # Check for error auto-reset (5 seconds)
        if (st.session_state[error_time_key] and 
            time.time() - st.session_state[error_time_key] > 5):
            st.session_state[error_key] = None
            st.session_state[error_time_key] = None
            st.rerun()
        
        # Show current status
        self._show_voice_status(container_key)
        
        # Main voice recorder interface - FIXED: No auto-loop
        if not st.session_state[processing_key] and not st.session_state[error_key]:
            self._render_audio_recorder_fixed(message_callback, conversation_key, container_key, quiz_context)
        
        # Show conversation history
        self._show_conversation_history(conversation_key)
        
        # Control buttons
        return self._render_control_buttons(conversation_key, container_key)
    
    def _show_voice_status(self, container_key: str):
        """Show current voice interface status"""
        processing_key = f"voice_processing_{container_key}"
        error_key = f"voice_error_{container_key}"
        
        if st.session_state[error_key]:
            # Show error with expandable details
            error_msg = st.session_state[error_key]
            with st.expander(f"⚠️ {error_msg.split(':')[0]} (click for details)", expanded=False):
                st.error(error_msg)
                st.info("🔄 Auto-resetting in a few seconds...")
                
        elif st.session_state[processing_key]:
            st.info("🌀 Processing your voice...")
            
        else:
            st.success("🎤 Ready for voice input! Click record and speak clearly.")
    
    def _render_audio_recorder_fixed(self, message_callback: Callable[[str], str],
                                    conversation_key: str, container_key: str,
                                    quiz_context: Optional[Dict] = None):
        """FIXED: Audio recorder with proper loop prevention"""
        
        st.markdown("#### 🎤 Voice Recording")
        
        # Audio recorder with configuration
        audio_bytes = audio_recorder(
            text="🎤 Click to Record",
            recording_color="#e74c3c",  # Red recording button
            neutral_color="#3498db",    # Blue ready button
            icon_name="microphone",
            icon_size="2x",
            pause_threshold=1.0,        # 1 second pause detection
            sample_rate=16000,          # Optimal for voice
            key=f"audio_recorder_{container_key}"
        )
        
        # CRITICAL FIX: Check if this audio was already processed
        if audio_bytes:
            # Create hash of audio data to track uniqueness
            audio_hash = hashlib.md5(audio_bytes).hexdigest()
            
            processed_hashes_key = f"processed_audio_hashes_{container_key}"
            last_hash_key = f"last_audio_hash_{container_key}"
            
            # Check if this exact audio was already processed
            if audio_hash not in st.session_state[processed_hashes_key]:
                # NEW AUDIO - Process it
                st.session_state[f"voice_processing_{container_key}"] = True
                st.session_state[processed_hashes_key].add(audio_hash)
                st.session_state[last_hash_key] = audio_hash
                
                # Process the new audio
                self._process_recorded_audio_fixed(
                    audio_bytes, message_callback, conversation_key, 
                    container_key, quiz_context
                )
            else:
                # ALREADY PROCESSED - Show status
                if st.session_state[last_hash_key] == audio_hash:
                    st.info("✅ This recording was already processed. Record new audio to continue.")
                else:
                    st.warning("🔄 This audio was processed earlier. Record new audio to continue.")
    
    def _process_recorded_audio_fixed(self, audio_bytes: bytes, 
                                     message_callback: Callable[[str], str],
                                     conversation_key: str, container_key: str,
                                     quiz_context: Optional[Dict] = None):
        """ENHANCED: Process the recorded audio with better logic"""
        
        processing_key = f"voice_processing_{container_key}"
        error_key = f"voice_error_{container_key}"
        error_time_key = f"voice_error_time_{container_key}"
        
        try:
            # Show audio feedback
            audio_size_kb = len(audio_bytes) / 1024
            if audio_size_kb < 1:
                st.warning("🔇 Very short recording. Speak louder and longer!")
            elif audio_size_kb > 50:
                st.info(f"🔊 Good audio! ({audio_size_kb:.1f}KB)")
            else:
                st.success(f"🔊 Processing audio ({audio_size_kb:.1f}KB)...")
            
            # Step 1: Transcribe audio
            with st.spinner("🤔 Converting speech to text..."):
                transcribed_text = self._transcribe_audio_bytes(audio_bytes)
                
                if not transcribed_text or not transcribed_text.strip():
                    raise Exception("Transcription failed: No speech detected")
            
            st.success(f"🎤 You said: '{transcribed_text}'")
            
            # Step 2: Generate AI response with ENHANCED logic
            with st.spinner("🤖 AI is thinking..."):
                if quiz_context:
                    # ENHANCED: Use better voice message handling
                    ai_response = self._handle_voice_message_enhanced(
                        transcribed_text.strip(), quiz_context, conversation_key
                    )
                else:
                    ai_response = message_callback(transcribed_text.strip())
            
            # Step 3: Store conversation (already done in enhanced handler)
            if not quiz_context:
                st.session_state[conversation_key].extend([
                    {"role": "user", "content": transcribed_text.strip()},
                    {"role": "assistant", "content": ai_response}
                ])
            
            # Step 4: Convert AI response to speech
            with st.spinner("🔊 AI is responding with voice..."):
                self._speak_response(ai_response)
            
            # Step 5: Mark as complete - NO AUTO-RERUN!
            st.session_state[processing_key] = False
            st.success("✅ Voice conversation complete! Record again to continue.")
            st.balloons()
            
        except Exception as e:
            # Handle errors with auto-reset
            error_msg = f"Voice processing failed: {str(e)}"
            st.session_state[error_key] = error_msg
            st.session_state[error_time_key] = time.time()
            st.session_state[processing_key] = False
            
        # CRITICAL FIX: NO st.rerun() here! Let user manually record again.
    
    def _handle_voice_message_enhanced(self, user_text: str, quiz_context: Dict, message_key: str) -> str:
        """ENHANCED: Voice message handling with better logic"""
        
        try:
            # Import here to avoid circular imports
            from backend.services import ChatService
            chat_service = ChatService()
            
            # Detect question type for better response strategy
            question_type = self._classify_voice_question(user_text)
            
            if question_type == "direct_answer_request":
                # Student asking for direct answers
                if not st.session_state.get('quiz_completed', False):
                    enhanced_prompt = f"""
                    The student is asking for a direct answer: "{user_text}"
                    
                    IMPORTANT: Don't give the answer directly since the quiz isn't complete.
                    Instead, guide their thinking:
                    1. What concept is this question testing?
                    2. What should they consider or look for?
                    3. What approach works for this type of question?
                    
                    Be specific to the actual question content, not generic.
                    Keep response under 100 words for voice delivery.
                    """
                else:
                    enhanced_prompt = f"The quiz is complete. Explain why the correct answer is right: {user_text}"
                    
            elif question_type == "concept_explanation":
                enhanced_prompt = f"""
                Student wants concept explanation: "{user_text}"
                
                Provide a clear, specific explanation using:
                1. Content from the PDF
                2. Real examples 
                3. How it relates to the current question
                4. Why this concept matters
                
                Be educational and specific, not generic. Keep under 100 words for voice.
                """
                
            elif question_type == "help_request":
                enhanced_prompt = f"""
                Student needs help: "{user_text}"
                
                Provide step-by-step guidance:
                1. Break down what the question is asking
                2. What information they need to find
                3. How to approach this type of problem
                4. What to look for in the answer choices (if MCQ)
                
                Reference specific PDF content when possible. Keep under 100 words for voice.
                """
            else:
                # General conversation - use enhanced prompting
                enhanced_prompt = self._create_enhanced_quiz_voice_prompt(user_text, quiz_context)
            
            # Get AI response with enhanced prompting
            result = chat_service.chat_with_pdf(
                st.session_state.quiz_user_id,
                st.session_state.quiz_pdf_id,
                enhanced_prompt,
                "Tutor"
            )
            
            if result.success:
                response = result.data['response']
                
                # Post-process response for voice optimization
                optimized_response = self._optimize_for_voice(response)
                
                # Add to text chat for continuity
                st.session_state[message_key].extend([
                    {"role": "user", "content": f"🎤 {user_text}"},
                    {"role": "assistant", "content": optimized_response}
                ])
                
                return optimized_response
            else:
                return "I'm having trouble accessing the PDF content right now. Can you try rephrasing your question?"
                
        except Exception as e:
            return f"Sorry, I encountered an error processing your question. Please try again."
    
    def _classify_voice_question(self, user_text: str) -> str:
        """Classify the type of question for better response strategy"""
        
        user_lower = user_text.lower()
        
        # Direct answer patterns
        direct_patterns = ['what is the answer', 'which option', 'is it a', 'is it b', 'tell me the answer', 'correct answer']
        if any(pattern in user_lower for pattern in direct_patterns):
            return "direct_answer_request"
        
        # Concept explanation patterns  
        concept_patterns = ['explain', 'what does', 'what is', 'how does', 'why is', 'define', 'what means']
        if any(pattern in user_lower for pattern in concept_patterns):
            return "concept_explanation"
        
        # Help request patterns
        help_patterns = ['help', 'stuck', 'don\'t understand', 'confused', 'how to solve', 'hint', 'guide me']
        if any(pattern in user_lower for pattern in help_patterns):
            return "help_request"
        
        return "general"
    
    def _create_enhanced_quiz_voice_prompt(self, user_text: str, quiz_context: Dict) -> str:
        """Create enhanced prompt for more logical, specific responses"""
        
        # Get current question details if available
        current_question = quiz_context.get('current_question', '')
        quiz_type = quiz_context.get('quiz_type', 'Unknown')
        progress = quiz_context.get('progress', 'Unknown')
        difficulty = quiz_context.get('difficulty', 'Medium')
        
        # Build context-rich prompt
        enhanced_prompt = f"""
        CONTEXT: You are an expert AI tutor helping a student with a {quiz_type} quiz.
        
        STUDENT SITUATION:
        - Current Question: "{current_question}"
        - Quiz Progress: {progress}
        - Difficulty Level: {difficulty}
        - Student asked: "{user_text}"
        
        INSTRUCTIONS:
        1. ALWAYS reference the actual PDF content in your response
        2. Be specific - avoid generic advice like "think about key concepts"
        3. If it's an MCQ and quiz isn't complete, give conceptual hints, NOT letter answers
        4. If student is stuck, break down the question into smaller parts
        5. Keep response conversational but educational (under 100 words for voice)
        6. Use examples from the PDF when possible
        
        RESPONSE STYLE: Conversational, encouraging, specific, and directly helpful
        
        Now provide a specific, logical response based on the PDF content:
        """
        
        return enhanced_prompt
    
    def _optimize_for_voice(self, response: str) -> str:
        """Optimize AI response for voice delivery"""
        
        # Remove excessive formatting
        response = response.replace('**', '').replace('*', '')
        
        # Convert bullet points to speech-friendly format
        response = response.replace('•', 'First,').replace('- ', 'Also, ')
        
        # Add natural speech patterns
        if response.startswith('The '):
            response = f"So, {response.lower()}"
        elif response.startswith('This '):
            response = f"Well, {response.lower()}"
        
        # Ensure reasonable length for voice (50-100 words)
        words = response.split()
        if len(words) > 100:
            response = ' '.join(words[:100]) + "... Would you like me to continue explaining?"
        elif len(words) < 15:
            response += " Is there anything specific you'd like me to clarify about this?"
        
        return response
    
    def _transcribe_audio_bytes(self, audio_bytes: bytes) -> Optional[str]:
        """Transcribe audio bytes using voice service"""
        try:
            # Prepare audio file for upload
            audio_file = io.BytesIO(audio_bytes)
            files = {"audio": ("recording.wav", audio_file, "audio/wav")}
            
            response = requests.post(
                f"{self.voice_service_url}/transcribe",
                files=files,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    transcription = data.get("transcription", "").strip()
                    return transcription if transcription else None
                else:
                    raise Exception(f"Transcription service error: {data.get('error', 'Unknown error')}")
            else:
                raise Exception(f"Voice service unavailable (HTTP {response.status_code})")
                
        except requests.exceptions.Timeout:
            raise Exception("Voice processing timed out. Try a shorter recording.")
        except requests.exceptions.ConnectionError:
            raise Exception("Cannot connect to voice service. Is it running?")
        except Exception as e:
            raise Exception(f"Transcription error: {str(e)}")
    
    def _speak_response(self, text: str):
        """Convert text to speech and play - FIXED VERSION"""
        try:
            # Limit text length for voice
            if len(text) > 2000:
                text = text[:2000] + "..."
            
            response = requests.post(
                f"{self.voice_service_url}/synthesize_simple",
                params={"text": text},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    audio_b64 = data.get("audio_base64", "")
                    if audio_b64:
                        audio_bytes = base64.b64decode(audio_b64)
                        
                        # FIXED: Use unique key to prevent audio component conflicts
                        audio_key = f"ai_response_{hash(text[:30])}_{int(time.time())}"
                        
                        # Store in session state to prevent reprocessing
                        if audio_key not in st.session_state:
                            st.session_state[audio_key] = audio_bytes
                        
                        audio_buffer = io.BytesIO(st.session_state[audio_key])
                        
                        # Play audio with autoplay enabled
                        st.audio(audio_buffer, format='audio/wav', autoplay=True)
                        return
            
            # Fallback to text display
            st.info(f"🦉 AI: {text}")
            
        except Exception as e:
            st.warning(f"TTS failed: {str(e)[:50]}...")
            st.info(f"🦉 AI: {text}")
    
    def _show_conversation_history(self, conversation_key: str):
        """Show conversation history"""
        if st.session_state[conversation_key]:
            st.markdown("---")
            st.markdown("**🗣️ Voice Conversation:**")
            
            # Show recent messages (last 4 exchanges)
            recent_messages = st.session_state[conversation_key][-8:]
            for msg in recent_messages:
                if msg["role"] == "user":
                    st.markdown(f"**🎤 You:** {msg['content']}")
                else:
                    st.markdown(f"**🔊 AI:** {msg['content']}")
            
            if len(st.session_state[conversation_key]) > 8:
                st.caption(f"... and {len(st.session_state[conversation_key]) - 8} more messages")
    
    def _render_control_buttons(self, conversation_key: str, container_key: str) -> bool:
        """Render control buttons"""
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🗑️ Clear Chat", key=f"clear_voice_{container_key}", use_container_width=True):
                st.session_state[conversation_key] = []
                # Also clear processed audio hashes
                processed_hashes_key = f"processed_audio_hashes_{container_key}"
                st.session_state[processed_hashes_key] = set()
                st.success("Voice chat cleared!")
                st.rerun()
        
        with col2:
            if st.button("🧪 Test Voice", key=f"test_voice_{container_key}", use_container_width=True):
                self._test_voice_service()
        
        with col3:
            if st.button("❌ Exit Voice", key=f"exit_voice_{container_key}", use_container_width=True):
                # Clean up voice state
                self._cleanup_voice_state(container_key)
                st.success("Exited voice mode!")
                return True  # Signal to exit voice mode
        
        return False
    
    def _cleanup_voice_state(self, container_key: str):
        """Clean up voice-related session state"""
        keys_to_clear = [
            f"voice_processing_{container_key}",
            f"voice_error_{container_key}",
            f"voice_error_time_{container_key}",
            f"processed_audio_hashes_{container_key}",
            f"last_audio_hash_{container_key}"
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
    
    def _test_voice_service(self):
        """Test voice service connectivity"""
        try:
            response = requests.post(f"{self.voice_service_url}/test", timeout=15)
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    st.success("✅ Voice service working perfectly!")
                    with st.expander("🔍 Test Details"):
                        st.write(f"**STT Method:** {data.get('stt_method')}")
                        st.write(f"**TTS Method:** {data.get('tts_method')}")
                        st.write(f"**TTS Time:** {data.get('tts_processing_time', 0):.2f}s")
                        st.write(f"**Audio Size:** {data.get('audio_size_bytes', 0)} bytes")
                        st.write(f"**Score:** {data.get('similarity_score', 0):.1%}")
                else:
                    st.error(f"❌ Voice test failed: {data.get('error')}")
            else:
                st.error("❌ Voice service not responding")
        except Exception as e:
            st.error(f"❌ Cannot reach voice service: {e}")
            st.info("💡 Start voice service: `cd voicemode && python voice_service.py`")
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get voice service status information"""
        return {
            "voice_available": self.voice_available,
            "audio_recorder_available": self.audio_recorder_available,
            "service_url": self.voice_service_url
        }