# File: frontend/components/quiz_display.py - Updated for new voice interface

import streamlit as st
from typing import Dict, List, Any, Optional
from backend.services import QuizService, ChatService, SavedQuizService
from backend.utils import TextProcessor

# Import new voice interface
try:
    from .voice_interface import VoiceInterface
    VOICE_INTERFACE_AVAILABLE = True
except ImportError:
    VOICE_INTERFACE_AVAILABLE = False

class QuizDisplay:
    """Quiz display and interaction component with updated Voice Mode"""
    
    def __init__(self):
        self.quiz_service = QuizService()
        self.chat_service = ChatService()
        self.saved_quiz_service = SavedQuizService()
        self.text_processor = TextProcessor()
        
        # Voice integration - Updated for new interface
        if VOICE_INTERFACE_AVAILABLE:
            try:
                self.voice_interface = VoiceInterface()
                self.voice_available = (
                    self.voice_interface.voice_available and 
                    self.voice_interface.audio_recorder_available
                )
            except Exception as e:
                print(f"Voice interface error: {e}")
                self.voice_interface = None
                self.voice_available = False
        else:
            self.voice_interface = None
            self.voice_available = False
    
    def show_quiz_generator(self, user_id: str, pdf_id: str, pdf_name: str):
        """Show quiz generation interface"""
        try:
            st.subheader(f"📝 Generate Quiz from: {pdf_name}")
            
            # Clear any existing quiz data
            self._clear_existing_quiz_data()
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Quiz type selection
                quiz_type = st.selectbox(
                    "Select Quiz Type:", 
                    ["MCQ", "Open-ended"], 
                    index=0,
                    key="quiz_type_select_fixed"
                )
                
                # Number of questions - Fixed integer handling
                num_questions_raw = st.slider(
                    "Number of Questions:", 
                    min_value=1, 
                    max_value=10, 
                    value=3,
                    step=1,
                    key="num_questions_slider_fixed"
                )
                
                # Force to integer immediately
                num_questions = int(num_questions_raw) if num_questions_raw is not None else 3
            
            with col2:
                # Difficulty selection
                difficulty = st.selectbox(
                    "Difficulty:", 
                    ["Easy", "Medium", "Hard"], 
                    index=1,
                    key="difficulty_select_fixed"
                )
                
                # Topic focus
                topic_focus = st.text_input(
                    "Focus on specific topic (optional):", 
                    value="",
                    key="topic_focus_input_fixed"
                )
            
            # Generate button
            if st.button("🎯 Generate Quiz", key="generate_quiz_btn_fixed", type="primary"):
                
                if not user_id or not pdf_id:
                    st.error("Missing user or PDF information.")
                    return
                
                # Explicit type conversion
                user_id_str = str(user_id)
                pdf_id_str = str(pdf_id) 
                quiz_type_str = str(quiz_type)
                difficulty_str = str(difficulty)
                topic_focus_str = str(topic_focus) if topic_focus else ""
                num_questions_int = int(num_questions)
                
                st.info(f"🚀 Generating {quiz_type_str} quiz with {num_questions_int} questions...")
                
                with st.spinner("🎲 Creating your quiz..."):
                    try:
                        # Call service with explicit parameters
                        result = self.quiz_service.generate_quiz(
                            user_id_str,
                            pdf_id_str,
                            quiz_type_str,
                            num_questions_int,
                            difficulty_str,
                            topic_focus_str
                        )
                        
                        if result.success:
                            # Parse questions
                            parse_result = self.quiz_service.parse_quiz_questions(
                                result.data['content'], quiz_type_str
                            )
                            if parse_result.success:
                                # Store in session state
                                st.session_state.current_quiz = result.data
                                st.session_state.quiz_questions = parse_result.data
                                st.session_state.quiz_answers = {}
                                st.session_state.quiz_completed = False
                                st.session_state.quiz_user_id = user_id_str
                                st.session_state.quiz_pdf_id = pdf_id_str
                                st.session_state.quiz_saved = False
                                st.session_state.feedback_shown = False
                                st.session_state.current_quiz['quiz_type'] = quiz_type_str
                                st.session_state.current_quiz['difficulty'] = difficulty_str
                                st.session_state.current_quiz['topic_focus'] = topic_focus_str
                                
                                # Initialize chatbot state
                                self._init_chatbot_state(quiz_type_str)
                                
                                st.success("✅ Quiz generated successfully!")
                                st.balloons()
                                st.rerun()
                            else:
                                st.error(f"Error parsing quiz questions: {parse_result.message}")
                        else:
                            st.error(f"Error generating quiz: {result.message}")
                            
                    except Exception as e:
                        st.error(f"Exception in quiz generation: {str(e)}")
                        with st.expander("🐛 Error Details"):
                            import traceback
                            st.code(traceback.format_exc())
                            
        except Exception as e:
            st.error(f"Error in quiz generator interface: {str(e)}")
            with st.expander("🐛 Error Details"):
                import traceback
                st.code(traceback.format_exc())
    
    def _clear_existing_quiz_data(self):
        """Clear all existing quiz-related session state"""
        keys_to_clear = []
        for key in list(st.session_state.keys()):
            if any(prefix in key for prefix in [
                'current_quiz', 'quiz_questions', 'quiz_answers', 'quiz_completed',
                'quiz_chatbot_', 'open_quiz_chatbot_', 'quiz_user_id', 'quiz_pdf_id',
                'quiz_feedback', 'quiz_score_data', 'feedback_shown', 'quiz_saved'
            ]):
                keys_to_clear.append(key)
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
    
    def _init_chatbot_state(self, quiz_type: str):
        """Initialize chatbot state"""
        chatbot_key = 'quiz_chatbot_messages' if quiz_type == 'MCQ' else 'open_quiz_chatbot_messages'
        chatbot_open_key = 'quiz_chatbot_open' if quiz_type == 'MCQ' else 'open_quiz_chatbot_open'
        if chatbot_key not in st.session_state:
            st.session_state[chatbot_key] = []
        if chatbot_open_key not in st.session_state:
            st.session_state[chatbot_open_key] = False
    
    def display_quiz(self):
        """Main display method - handles different quiz states"""
        if not self._has_active_quiz():
            return
        
        quiz_data = st.session_state.current_quiz
        questions = st.session_state.quiz_questions
        quiz_type = quiz_data['type']
        
        # Check if quiz is completed and feedback has been shown
        if st.session_state.get('quiz_completed', False):
            if st.session_state.get('feedback_shown', False):
                self._show_quiz_with_feedback_and_options(questions, quiz_type)
            else:
                self._show_quiz_completion_initial(questions, quiz_type)
            return
        
        # Show active quiz
        if quiz_type == "MCQ":
            self._display_mcq_quiz(questions)
        else:
            self._display_open_ended_quiz(questions)
    
    def _show_quiz_completion_initial(self, questions: List[Dict], quiz_type: str):
        """Show initial completion screen with Get Feedback button"""
        st.success("🎉 Quiz Completed!")
        
        if quiz_type == "MCQ":
            self._show_quiz_management_options()
        else:
            if st.button("✅ Get Feedback", key="get_feedback_btn", type="primary", use_container_width=True):
                self._generate_open_ended_feedback(questions)
    
    def _show_quiz_with_feedback_and_options(self, questions: List[Dict], quiz_type: str):
        """Show completed quiz with feedback and management options"""
        st.success("🎉 Quiz Completed!")
        
        # AI Tutor toggle button at the top
        col1, col2 = st.columns([10, 1])
        with col1:
            st.subheader("📊 Quiz Results & Feedback")
        with col2:
            chatbot_open_key = 'quiz_chatbot_open' if quiz_type == 'MCQ' else 'open_quiz_chatbot_open'
            if st.button("🦉", help="Ask AI Tutor about results", key="feedback_chatbot_toggle"):
                st.session_state[chatbot_open_key] = not st.session_state.get(chatbot_open_key, False)
        
        # Layout: feedback + optional AI tutor
        if st.session_state.get(chatbot_open_key, False):
            feedback_col, chat_col = st.columns([3, 2])
        else:
            feedback_col = st.container()
            chat_col = None
        
        with feedback_col:
            if quiz_type == "MCQ":
                self._display_mcq_results_and_explanations(questions)
            else:
                self._display_open_ended_feedback(questions)
            
            # Show management options
            st.markdown("---")
            st.markdown("### What would you like to do next?")
            self._show_quiz_management_options()
        
        # Show AI Tutor in right column if open
        if chat_col and st.session_state.get(chatbot_open_key, False):
            with chat_col:
                self._render_feedback_chatbot(questions, quiz_type)
    
    def _display_mcq_quiz(self, questions: List[Dict]):
        """Display MCQ quiz with AI tutor integration"""
        if not questions:
            st.error("No questions could be parsed from the quiz.")
            return
            
        if 'quiz_chatbot_open' not in st.session_state:
            st.session_state.quiz_chatbot_open = False
        if 'quiz_chatbot_messages' not in st.session_state:
            st.session_state.quiz_chatbot_messages = []
        
        col1, col2 = st.columns([10, 1])
        with col1:
            st.subheader(f"📝 MCQ Quiz ({len(questions)} Questions)")
        with col2:
            if st.button("🦉", help="Ask AI Tutor for help", key="quiz_chatbot_toggle"):
                st.session_state.quiz_chatbot_open = not st.session_state.quiz_chatbot_open
        
        if st.session_state.quiz_chatbot_open:
            quiz_col, chat_col = st.columns([3, 2])
        else:
            quiz_col = st.container()
            chat_col = None
        
        with quiz_col:
            self._render_mcq_questions(questions)
        
        if st.session_state.quiz_chatbot_open and chat_col:
            with chat_col:
                self._render_quiz_chatbot(questions, "MCQ")
        
        if st.session_state.quiz_answers:
            st.markdown("---")
            if st.button("✅ Check Answers", key="check_answers_btn", type="primary", use_container_width=True):
                self._check_mcq_answers(questions)
    
    def _display_open_ended_quiz(self, questions: List[Dict]):
        """Display open-ended quiz with AI tutor integration"""
        if not questions:
            st.error("No questions could be parsed from the quiz.")
            return
            
        if 'open_quiz_chatbot_open' not in st.session_state:
            st.session_state.open_quiz_chatbot_open = False
        if 'open_quiz_chatbot_messages' not in st.session_state:
            st.session_state.open_quiz_chatbot_messages = []
        
        col1, col2 = st.columns([10, 1])
        with col1:
            st.subheader(f"📝 Open-ended Quiz ({len(questions)} Questions)")
        with col2:
            if st.button("🦉", help="Ask AI Tutor for help", key="open_quiz_chatbot_toggle"):
                st.session_state.open_quiz_chatbot_open = not st.session_state.open_quiz_chatbot_open
        
        if st.session_state.open_quiz_chatbot_open:
            quiz_col, chat_col = st.columns([3, 2])
        else:
            quiz_col = st.container()
            chat_col = None
        
        with quiz_col:
            self._render_open_ended_questions(questions)
        
        if st.session_state.open_quiz_chatbot_open and chat_col:
            with chat_col:
                self._render_quiz_chatbot(questions, "Open-ended")
        
        if st.session_state.quiz_answers:
            st.markdown("---")
            if st.button("✅ Get Feedback", key="get_feedback_btn_open", type="primary", use_container_width=True):
                self._generate_open_ended_feedback(questions)
    
    def _render_mcq_questions(self, questions: List[Dict]):
        """Render MCQ questions"""
        for q in questions:
            st.markdown("---")
            st.markdown(f"**Question {q['number']}:** {q['question']}")
            options_display = [f"{letter}) {text}" for letter, text in q['options'].items()]
            selected = st.radio(
                f"Select your answer for Question {q['number']}:",
                options_display,
                key=f"mcq_q{q['number']}",
                index=None
            )
            if selected:
                st.session_state.quiz_answers[q['number']] = selected[0]
    
    def _render_open_ended_questions(self, questions: List[Dict]):
        """Render open-ended questions"""
        for q in questions:
            st.markdown("---")
            st.markdown(f"### Question {q['number']}")
            st.markdown(f"**{q['question']}**")
            answer = st.text_area(
                f"Your answer:",
                key=f"open_q{q['number']}",
                height=150,
                placeholder="Write your detailed answer here..."
            )
            if answer.strip():
                st.session_state.quiz_answers[q['number']] = answer.strip()
    
    def _render_quiz_chatbot(self, questions: List[Dict], quiz_type: str):
        """Render quiz chatbot with new voice interface integration"""
        
        # Header with voice mode toggle
        col1, col2 = st.columns([8, 2])
        with col1:
            st.markdown("### 🦉 AI Tutor")
            st.markdown("*Ask me about the quiz content or get help!*")
        
        with col2:
            # Voice mode toggle - Updated for new interface
            if self.voice_interface and self.voice_available:
                voice_icon = "⌨️" if st.session_state.get('voice_mode_active', False) else "🎤"
                help_text = "Switch to Text" if st.session_state.get('voice_mode_active', False) else "Voice Mode"
                
                if st.button(voice_icon, help=help_text, key="voice_mode_btn"):
                    st.session_state.voice_mode_active = not st.session_state.get('voice_mode_active', False)
                    st.rerun()
            else:
                st.button("🎤", disabled=True, help="Voice service unavailable")
        
        message_key = 'quiz_chatbot_messages' if quiz_type == 'MCQ' else 'open_quiz_chatbot_messages'
        
        # Show voice mode or text mode
        if st.session_state.get('voice_mode_active', False) and self.voice_available:
            self._render_voice_interface(questions, quiz_type, message_key)
        else:
            self._render_text_chat_interface(questions, quiz_type, message_key)
    
    def _render_voice_interface(self, questions: List[Dict], quiz_type: str, message_key: str):
        """Render voice interface with quiz context"""
        
        if not self.voice_interface:
            st.error("❌ Voice interface not available")
            st.session_state.voice_mode_active = False
            st.rerun()
            return
        
        # Create quiz context for voice interface
        quiz_context = self._create_quiz_context_for_voice(questions, quiz_type)
        
        # Define callback for voice messages
        def handle_voice_message(user_text: str) -> str:
            """Handle voice input and return AI response"""
            try:
                result = self.chat_service.chat_with_pdf(
                    st.session_state.quiz_user_id,
                    st.session_state.quiz_pdf_id,
                    user_text,
                    "Tutor"
                )
                
                if result.success:
                    # Also add to text chat for continuity
                    st.session_state[message_key].extend([
                        {"role": "user", "content": f"🎤 {user_text}"},
                        {"role": "assistant", "content": result.data['response']}
                    ])
                    return result.data['response']
                else:
                    return "I'm sorry, I couldn't process that. Please try text mode."
                    
            except Exception as e:
                return f"Voice error: {str(e)[:50]}. Please try text mode."
        
        # Use VoiceInterface component with quiz context
        conversation_key = f"voice_quiz_{quiz_type.lower()}"
        container_key = f"quiz_voice_{quiz_type.lower()}"
        
        try:
            exit_voice = self.voice_interface.render_voice_chat(
                message_callback=handle_voice_message,
                conversation_key=conversation_key,
                container_key=container_key,
                quiz_context=quiz_context
            )
            
            if exit_voice:
                st.session_state.voice_mode_active = False
                st.rerun()
                
        except Exception as e:
            st.error(f"Voice interface error: {str(e)}")
            st.session_state.voice_mode_active = False
            st.rerun()
    
    def _create_quiz_context_for_voice(self, questions: List[Dict], quiz_type: str) -> Dict:
        """Create context dictionary for voice interface"""
        answered_count = len(st.session_state.quiz_answers)
        total_count = len(questions)
        
        # Get current question if available
        current_question = None
        if answered_count < total_count:
            current_q_num = answered_count + 1
            for q in questions:
                if q.get('number') == current_q_num:
                    current_question = q.get('question', '')
                    break
        
        return {
            'quiz_type': quiz_type,
            'progress': f"{answered_count}/{total_count}",
            'current_question': current_question,
            'status': 'completed' if st.session_state.get('quiz_completed', False) else 'active',
            'difficulty': st.session_state.current_quiz.get('difficulty', 'Medium')
        }
    
    def _render_text_chat_interface(self, questions: List[Dict], quiz_type: str, message_key: str):
        """Original text chat interface"""
        # Display messages
        if st.session_state[message_key]:
            for message in st.session_state[message_key]:
                if message["role"] == "user":
                    st.markdown(f"**You:** {message['content']}")
                else:
                    st.markdown(f"**🦉 Tutor:** {message['content']}")
            st.markdown("---")
        else:
            st.info("👋 Hi! I'm your AI tutor. Ask me about any question or concept!")
        
        # Chat input
        chat_input = st.text_input("Ask your question:", key=f"{quiz_type.lower()}_quiz_chat_input")
        col1, col2 = st.columns([3, 1])
        with col1:
            send_chat = st.button("Send", key=f"send_{quiz_type.lower()}_quiz_chat", type="primary")
        with col2:
            if st.button("Clear", key=f"clear_{quiz_type.lower()}_quiz_chat"):
                st.session_state[message_key] = []
                st.rerun()
        
        if send_chat and chat_input.strip():
            self._handle_quiz_chat_message(chat_input.strip(), questions, quiz_type, message_key)
        
        self._render_quick_help_buttons(questions, quiz_type, message_key)
    
    def _handle_quiz_chat_message(self, message: str, questions: List[Dict], quiz_type: str, message_key: str):
        """Handle quiz chat message with smart prompting"""
        st.session_state[message_key].append({"role": "user", "content": message})
        
        with st.spinner("🤔 Thinking..."):
            # Check if asking for direct answers
            is_asking_for_answer = self._is_asking_for_direct_answer(message)
            quiz_completed = st.session_state.get('quiz_completed', False)
            
            if is_asking_for_answer and not quiz_completed:
                # Guide without revealing answers
                smart_prompt = f"""
                The student is taking a quiz and asked: "{message}"
                
                IMPORTANT: Do NOT reveal correct letter answers (A, B, C, D) since the quiz is not complete.
                Instead, give conceptual hints that help them think through the problem.
                
                Give guidance like: "Think about the main purpose of..." or "Consider which option focuses on..."
                """
            else:
                smart_prompt = message
            
            result = self.chat_service.chat_with_pdf(
                st.session_state.quiz_user_id,
                st.session_state.quiz_pdf_id,
                smart_prompt,
                "Tutor"
            )
            response = result.data['response'] if result.success else "I'm sorry, I couldn't generate a response. Please try again."
        
        st.session_state[message_key].append({"role": "assistant", "content": response})
        st.rerun()
    
    def _render_quick_help_buttons(self, questions: List[Dict], quiz_type: str, message_key: str):
        """Render quick help buttons"""
        st.markdown("**Quick Help:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if quiz_type == "MCQ":
                if st.button("💡 Explain Topic", key="quiz_explain_topic", use_container_width=True):
                    self._handle_quick_help("explain_topic", questions, message_key)
            else:
                if st.button("💭 Brainstorm", key="open_quiz_brainstorm", use_container_width=True):
                    self._handle_quick_help("brainstorm", questions, message_key)
        
        with col2:
            if st.button("❓ Hint", key=f"{quiz_type.lower()}_quiz_hint", use_container_width=True):
                self._handle_quick_help("hint", questions, message_key)
    
    def _handle_quick_help(self, help_type: str, questions: List[Dict], message_key: str):
        """Handle quick help button clicks"""
        quiz_completed = st.session_state.get('quiz_completed', False)
        
        if help_type == "hint" and st.session_state.quiz_answers:
            last_q_num = max(st.session_state.quiz_answers.keys())
            last_question = next(q for q in questions if q['number'] == last_q_num)
            
            if quiz_completed:
                hint_request = f"Explain why the correct answer is right for: {last_question['question']}"
                user_message = f"Explain Question {last_q_num}"
            else:
                hint_request = f"Give me a conceptual hint for this question without revealing the letter answer: {last_question['question']}"
                user_message = f"Hint for Question {last_q_num}"
                
        elif help_type == "explain_topic":
            explain_request = "Can you explain the main topic or concept that this quiz is focusing on?"
            user_message = "Explain main topic"
            hint_request = explain_request
            
        elif help_type == "brainstorm" and questions:
            first_question = questions[0]['question']
            hint_request = f"Help me brainstorm ideas for this question without giving away the answer: {first_question}"
            user_message = "Help me brainstorm ideas"
        else:
            return
        
        # Add user message
        st.session_state[message_key].append({"role": "user", "content": user_message})
        
        # Generate response
        with st.spinner("🤔 Generating response..."):
            result = self.chat_service.chat_with_pdf(
                st.session_state.quiz_user_id,
                st.session_state.quiz_pdf_id,
                hint_request,
                "Tutor"
            )
            response = result.data['response'] if result.success else "I couldn't generate a response. Please try again."
        
        # Add AI response
        st.session_state[message_key].append({"role": "assistant", "content": response})
        st.rerun()
    
    def _is_asking_for_direct_answer(self, question: str) -> bool:
        """Detect if student is asking for a direct answer"""
        question_lower = question.lower()
        
        direct_answer_patterns = [
            r'\bis\s+[a-d]\s+correct',
            r'\bwhat.*answer',
            r'\bwhich.*correct', 
            r'\bwhat.*right',
            r'\btell me.*answer',
            r'\bwhat.*letter',
            r'\bshould i choose'
        ]
        
        import re
        for pattern in direct_answer_patterns:
            if re.search(pattern, question_lower):
                return True
        
        return False
    
    def _generate_open_ended_feedback(self, questions: List[Dict]):
        """Generate feedback for open-ended quiz"""
        if not st.session_state.quiz_answers:
            st.warning("Please answer at least one question!")
            return
        
        # Generate and store feedback
        feedback_data = {}
        
        with st.spinner("🤔 Generating detailed feedback..."):
            for q_num, answer in st.session_state.quiz_answers.items():
                question_text = next(q['question'] for q in questions if q['number'] == q_num)
                
                result = self.chat_service.chat_with_pdf(
                    st.session_state.quiz_user_id,
                    st.session_state.quiz_pdf_id,
                    f"Evaluate this answer for '{question_text}': {answer}",
                    "Quiz Me"
                )
                
                if result.success:
                    feedback_data[q_num] = {
                        'question': question_text,
                        'answer': answer,
                        'feedback': result.data['response']
                    }
                else:
                    feedback_data[q_num] = {
                        'question': question_text,
                        'answer': answer,
                        'feedback': "Could not generate feedback for this question."
                    }
        
        # Store feedback in session state
        st.session_state.quiz_feedback = feedback_data
        st.session_state.feedback_shown = True
        st.rerun()
    
    def _display_mcq_results_and_explanations(self, questions: List[Dict]):
        """Display MCQ results with explanations"""
        # Show score summary
        if hasattr(st.session_state, 'quiz_score_data'):
            st.markdown(st.session_state.quiz_score_data.get('feedback', ''))
        
        # Show original quiz with answers for reference
        st.markdown("---")
        st.subheader("📝 Your Quiz & Answers")
        self._display_completed_mcq_questions(questions)
        
        # Show automatic AI explanations for wrong answers
        self._show_wrong_answer_explanations(questions, st.session_state.quiz_answers)
    
    def _display_completed_mcq_questions(self, questions: List[Dict]):
        """Display completed MCQ questions with user answers"""
        for q in questions:
            q_num = q['number']
            user_answer = st.session_state.quiz_answers.get(q_num, "Not answered")
            correct_answer = q['correct_answer']
            is_correct = user_answer == correct_answer
            
            # Question
            st.markdown(f"**Question {q_num}:** {q['question']}")
            
            # Show all options with indicators
            for letter, text in q['options'].items():
                if letter == user_answer:
                    if is_correct:
                        st.markdown(f"✅ **{letter}) {text}** ← Your answer (Correct!)")
                    else:
                        st.markdown(f"❌ **{letter}) {text}** ← Your answer (Incorrect)")
                elif letter == correct_answer and not is_correct:
                    st.markdown(f"✅ {letter}) {text} ← Correct answer")
                else:
                    st.markdown(f"⚪ {letter}) {text}")
            
            st.markdown("---")
    
    def _display_open_ended_feedback(self, questions: List[Dict]):
        """Display stored open-ended feedback"""
        feedback_data = st.session_state.get('quiz_feedback', {})
        
        # Show original quiz for reference
        st.markdown("### 📝 Your Quiz & Answers")
        self._display_completed_open_ended_questions(questions)
        
        # Show AI feedback
        st.markdown("---")
        st.markdown("### 🦉 AI Feedback & Explanations")
        
        for q_num in sorted(feedback_data.keys()):
            feedback = feedback_data[q_num]
            
            with st.expander(f"🦉 AI Feedback for Question {q_num}", expanded=True):
                st.markdown("**AI Evaluation:**")
                st.write(feedback['feedback'])
    
    def _display_completed_open_ended_questions(self, questions: List[Dict]):
        """Display completed open-ended questions with answers"""
        for q in questions:
            q_num = q['number']
            user_answer = st.session_state.quiz_answers.get(q_num, "Not answered")
            
            # Question
            st.markdown(f"**Question {q_num}:** {q['question']}")
            
            # User's answer
            st.markdown("**Your Answer:**")
            if user_answer != "Not answered":
                st.info(user_answer)
            else:
                st.warning("No answer provided")
            
            st.markdown("---")
    
    def _show_wrong_answer_explanations(self, questions: List[Dict], user_answers: Dict):
        """Show AI explanations for wrong answers"""
        wrong_questions = []
        
        for q in questions:
            q_num = q['number']
            correct_answer = q['correct_answer']
            user_answer = user_answers.get(q_num, "Not answered")
            
            if user_answer != correct_answer and user_answer != "Not answered":
                wrong_questions.append(q)
        
        if wrong_questions:
            st.markdown("---")
            st.subheader("🦉 AI Tutor Explanations for Incorrect Answers")
            
            for q in wrong_questions:
                q_num = q['number']
                correct_answer = q['correct_answer']
                user_answer = user_answers.get(q_num)
                
                with st.expander(f"🦉 Explanation for Question {q_num}", expanded=False):
                    with st.spinner("Generating explanation..."):
                        explanation_request = f"""Explain why '{correct_answer}) {q['options'].get(correct_answer, 'N/A')}' is the correct answer for: {q['question']}. 
                        The student chose '{user_answer}) {q['options'].get(user_answer, 'N/A')}'. 
                        Please explain the concept and why the student's choice was incorrect."""
                        
                        result = self.chat_service.chat_with_pdf(
                            st.session_state.quiz_user_id,
                            st.session_state.quiz_pdf_id,
                            explanation_request,
                            "Explain"
                        )
                        
                        if result.success:
                            st.write(result.data['response'])
                        else:
                            st.error("Could not generate explanation for this question.")
    
    def _show_quiz_management_options(self):
        """Show quiz management options"""
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Retake Quiz", key="retake_quiz_btn", type="primary", use_container_width=True):
                self._retake_quiz()
        
        with col2:
            if st.button("🆕 Generate New Quiz", key="new_quiz_btn", use_container_width=True):
                self._generate_new_quiz()
    
    def _retake_quiz(self):
        """Clear answers and feedback but keep questions"""
        st.session_state.quiz_answers = {}
        st.session_state.quiz_completed = False
        st.session_state.feedback_shown = False
        
        # Clear feedback data
        if 'quiz_feedback' in st.session_state:
            del st.session_state.quiz_feedback
        if 'quiz_score_data' in st.session_state:
            del st.session_state.quiz_score_data
        
        # Clear chatbot messages
        quiz_type = st.session_state.current_quiz['type']
        chatbot_key = 'quiz_chatbot_messages' if quiz_type == 'MCQ' else 'open_quiz_chatbot_messages'
        st.session_state[chatbot_key] = []
        
        st.info("🔄 Quiz reset! You can retake it now.")
        st.rerun()
    
    def _generate_new_quiz(self):
        """Clear everything and go back to quiz generation"""
        self._clear_existing_quiz_data()
        st.info("🆕 Ready to generate a new quiz!")
        st.rerun()
    
    def _check_mcq_answers(self, questions: List[Dict]):
        """Check MCQ answers and show results"""
        if not st.session_state.quiz_answers:
            st.warning("Please answer at least one question!")
            return
        
        correct_count = 0
        total_questions = len(questions)
        feedback_lines = []
        
        for q in questions:
            q_num = q['number']
            correct_answer = q['correct_answer']
            user_answer = st.session_state.quiz_answers.get(q_num, "Not answered")
            
            if user_answer == correct_answer:
                correct_count += 1
                feedback_lines.append(f"✅ **Question {q_num}**: Correct! ({correct_answer})")
            else:
                feedback_lines.append(f"❌ **Question {q_num}**: Wrong. You answered {user_answer}, correct answer is {correct_answer}")
                correct_option_text = q['options'].get(correct_answer, 'N/A')
                feedback_lines.append(f"   *{correct_option_text}*")
        
        score = f"**Score: {correct_count}/{total_questions} ({correct_count/total_questions*100:.1f}%)**"
        feedback = score + "\n\n" + "\n\n".join(feedback_lines)
        
        # Store results for later display
        st.session_state.quiz_score_data = {
            'correct_count': correct_count,
            'total_questions': total_questions,
            'percentage': correct_count/total_questions*100,
            'feedback': feedback
        }
        
        st.session_state.quiz_completed = True
        st.session_state.feedback_shown = True
        st.rerun()
    
    def _render_feedback_chatbot(self, questions: List[Dict], quiz_type: str):
        """Render AI tutor during feedback phase"""
        st.markdown("### 🦉 AI Tutor")
        st.markdown("*Ask me about your results or get explanations!*")
        
        message_key = 'quiz_chatbot_messages' if quiz_type == 'MCQ' else 'open_quiz_chatbot_messages'
        
        # Display messages
        if st.session_state[message_key]:
            for message in st.session_state[message_key]:
                if message["role"] == "user":
                    st.markdown(f"**You:** {message['content']}")
                else:
                    st.markdown(f"**🦉 Tutor:** {message['content']}")
                st.markdown("---")
        else:
            st.info("👋 Ask me about your quiz results or any concepts you'd like to understand better!")
        
        # Chat input
        chat_input = st.text_input(
            "Ask about your results:",
            key=f"feedback_{quiz_type.lower()}_chat_input",
            placeholder="e.g., 'Why did I get question 2 wrong?' or 'Explain this concept further'"
        )
        
        col1, col2 = st.columns([3, 1])
        with col1:
            send_chat = st.button("Send", key=f"send_feedback_{quiz_type.lower()}_chat", type="primary")
        with col2:
            if st.button("Clear", key=f"clear_feedback_{quiz_type.lower()}_chat"):
                st.session_state[message_key] = []
                st.rerun()
        
        if send_chat and chat_input.strip():
            self._handle_feedback_chat_message(chat_input.strip(), questions, quiz_type, message_key)
    
    def _handle_feedback_chat_message(self, message: str, questions: List[Dict], quiz_type: str, message_key: str):
        """Handle chat messages during feedback phase"""
        st.session_state[message_key].append({"role": "user", "content": message})
        
        with st.spinner("🤔 Thinking..."):
            result = self.chat_service.chat_with_pdf(
                st.session_state.quiz_user_id,
                st.session_state.quiz_pdf_id,
                message,
                "Tutor"
            )
            
            response = result.data['response'] if result.success else "I'm sorry, I couldn't generate a response. Please try again."
        
        st.session_state[message_key].append({"role": "assistant", "content": response})
        st.rerun()
    
    def _has_active_quiz(self) -> bool:
        """Check if there's an active quiz in session"""
        return (
            'current_quiz' in st.session_state and
            'quiz_questions' in st.session_state and
            st.session_state.current_quiz and
            st.session_state.quiz_questions
        )
    
    def get_quiz_status(self) -> Dict[str, Any]:
        """Get current quiz status for display"""
        if not self._has_active_quiz():
            return {'status': 'none'}
        
        quiz_data = st.session_state.current_quiz
        questions = st.session_state.quiz_questions
        answers = st.session_state.get('quiz_answers', {})
        
        return {
            'status': 'active',
            'type': quiz_data.get('type', 'MCQ'),
            'total_questions': len(questions),
            'answered_questions': len(answers),
            'difficulty': quiz_data.get('difficulty', 'Medium'),
            'topic_focus': quiz_data.get('topic_focus', ''),
            'completed': st.session_state.get('quiz_completed', False),
            'feedback_shown': st.session_state.get('feedback_shown', False),
            'voice_available': self.voice_available
        }