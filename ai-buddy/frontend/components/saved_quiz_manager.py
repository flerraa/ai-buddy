# File: frontend/components/saved_quiz_manager.py

import streamlit as st
from typing import Dict, List, Any, Optional
from backend.services import SavedQuizService

class SavedQuizManager:
    """Component for managing saved quizzes"""
    
    def __init__(self):
        self.saved_quiz_service = SavedQuizService()
    
    def show_saved_quizzes_interface(self, user_id: str, folder_id: str, folder_name: str):
        """Main interface for saved quizzes"""
        st.subheader(f"📝 Saved Quizzes - {folder_name}")
        
        # Get saved quizzes for this folder
        result = self.saved_quiz_service.get_folder_quizzes(user_id, folder_id)
        
        if result.success and result.data:
            st.markdown(f"### Your saved quizzes ({len(result.data)} total):")
            
            for quiz in result.data:
                self._display_quiz_item(quiz, user_id)
                
        else:
            st.info("📚 No saved quizzes yet! Generate and save some quizzes to see them here.")
            st.markdown("""
            **To create saved quizzes:**
            1. Go to Quiz Generator mode
            2. Generate a quiz from a PDF
            3. Complete the quiz and click "Save Quiz"
            """)
    
    def _display_quiz_item(self, quiz: Dict[str, Any], user_id: str):
        """Display individual quiz item with actions"""
        quiz_id = quiz['id']
        
        # Main quiz display
        col1, col2, col3, col4 = st.columns([4, 2, 1, 1])
        
        with col1:
            if st.button(
                f"📝 {quiz['name']}", 
                key=f"quiz_{quiz_id}",
                use_container_width=True,
                type="primary"
            ):
                self._select_quiz(quiz_id, quiz['name'])
        
        with col2:
            st.caption(f"📄 {quiz['pdf_name']}")
            st.caption(f"📅 {quiz['created_at']}")
        
        with col3:
            if st.button("✏️", key=f"rename_quiz_{quiz_id}", help="Rename quiz"):
                st.session_state.rename_quiz_id = quiz_id
                st.session_state.rename_quiz_name = quiz['name']
                st.rerun()
        
        with col4:
            if st.button("🗑️", key=f"delete_quiz_{quiz_id}", help="Delete quiz"):
                st.session_state.delete_quiz_id = quiz_id
                st.session_state.delete_quiz_name = quiz['name']
                st.rerun()
        
        # Quiz details
        col_detail1, col_detail2, col_detail3 = st.columns(3)
        with col_detail1:
            st.caption(f"📋 {quiz['type']} Quiz")
        with col_detail2:
            st.caption(f"🎯 {quiz['difficulty']}")
        with col_detail3:
            st.caption(f"❓ {quiz['question_count']} questions")
        
        st.markdown("---")
    
    def _select_quiz(self, quiz_id: str, quiz_name: str):
        """Select a quiz and show options"""
        st.session_state.selected_saved_quiz_id = quiz_id
        st.session_state.selected_saved_quiz_name = quiz_name
        st.rerun()
    
    def show_quiz_preview(self, user_id: str):
        """Show quiz preview with action options"""
        quiz_id = st.session_state.get('selected_saved_quiz_id')
        quiz_name = st.session_state.get('selected_saved_quiz_name')
        
        if not quiz_id:
            return
        
        st.subheader(f"📝 {quiz_name}")
        
        # Get quiz details
        result = self.saved_quiz_service.get_quiz_by_id(quiz_id, user_id)
        
        if not result.success:
            st.error(result.message)
            return
        
        quiz_data = result.data
        quiz_info = quiz_data['quiz_info']
        
        # Show quiz information
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Quiz Details:**")
            st.write(f"📋 **Type:** {quiz_info['type']}")
            st.write(f"🎯 **Difficulty:** {quiz_info['difficulty']}")
            st.write(f"❓ **Questions:** {quiz_info['question_count']}")
            st.write(f"📅 **Created:** {quiz_info['created_at']}")
        
        with col2:
            st.markdown("**Source Information:**")
            st.write(f"📄 **PDF:** {quiz_info['pdf_name']}")
            st.write(f"🎯 **Topic:** {quiz_info['topic_focus']}")
        
        st.markdown("---")
        st.markdown("### What would you like to do?")
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🎯 Take Quiz", key="take_saved_quiz", type="primary", use_container_width=True):
                self._start_saved_quiz(quiz_data)
        
        with col2:
            if st.button("📊 View Results", key="view_results", use_container_width=True):
                st.info("📊 Results viewing feature coming soon!")
        
        with col3:
            if st.button("🔙 Back to List", key="back_to_list", use_container_width=True):
                self._clear_selected_quiz()
    
    def _start_saved_quiz(self, quiz_data: Dict[str, Any]):
        """Start taking the saved quiz"""
        # Clear any existing quiz state
        self._clear_quiz_state()
        
        # Set up quiz session state similar to generated quiz
        st.session_state.current_quiz = {
            'type': quiz_data['quiz_info']['type'],
            'difficulty': quiz_data['quiz_info']['difficulty'],
            'content': '',  # Not needed for saved quiz
            'from_saved': True,
            'saved_quiz_id': st.session_state.selected_saved_quiz_id
        }
        st.session_state.quiz_questions = quiz_data['questions']
        st.session_state.quiz_answers = {}
        st.session_state.quiz_completed = False
        st.session_state.quiz_user_id = st.session_state.user_id
        st.session_state.quiz_pdf_id = quiz_data['pdf_id']
        st.session_state.quiz_saved = False
        st.session_state.feedback_shown = False
        
        # Initialize chatbot state
        quiz_type = quiz_data['quiz_info']['type']
        self._init_chatbot_state(quiz_type)
        
        # Clear selected quiz and switch to quiz mode
        self._clear_selected_quiz()
        st.session_state.app_mode = 'taking_saved_quiz'
        
        st.success(f"✅ Starting quiz: {quiz_data['quiz_info']['name']}")
        st.rerun()
    
    def _init_chatbot_state(self, quiz_type: str):
        """Initialize chatbot state for quiz"""
        chatbot_key = 'quiz_chatbot_messages' if quiz_type == 'MCQ' else 'open_quiz_chatbot_messages'
        chatbot_open_key = 'quiz_chatbot_open' if quiz_type == 'MCQ' else 'open_quiz_chatbot_open'
        if chatbot_key not in st.session_state:
            st.session_state[chatbot_key] = []
        if chatbot_open_key not in st.session_state:
            st.session_state[chatbot_open_key] = False
    
    def _clear_quiz_state(self):
        """Clear existing quiz state"""
        keys_to_clear = []
        for key in list(st.session_state.keys()):
            if any(prefix in key for prefix in [
                'current_quiz', 'quiz_questions', 'quiz_answers', 'quiz_completed',
                'quiz_chatbot_', 'open_quiz_chatbot_', 'quiz_saved',
                'quiz_feedback', 'quiz_score_data', 'feedback_shown'
            ]):
                keys_to_clear.append(key)
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
    
    def _clear_selected_quiz(self):
        """Clear selected quiz state"""
        if 'selected_saved_quiz_id' in st.session_state:
            del st.session_state.selected_saved_quiz_id
        if 'selected_saved_quiz_name' in st.session_state:
            del st.session_state.selected_saved_quiz_name
        st.rerun()
    
    def handle_quiz_operations(self, user_id: str):
        """Handle rename and delete operations"""
        if st.session_state.get('rename_quiz_id'):
            self._show_rename_quiz_form(user_id)
        
        if st.session_state.get('delete_quiz_id'):
            self._show_delete_confirmation_form(user_id)
    
    def _show_rename_quiz_form(self, user_id: str):
        """Show rename quiz form"""
        quiz_id = st.session_state.get('rename_quiz_id')
        current_name = st.session_state.get('rename_quiz_name', '')
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("✏️ Rename Quiz")
        
        with st.sidebar.form("rename_quiz_form"):
            new_name = st.text_input("New quiz name:", value=current_name)
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("✅ Save", type="primary"):
                    if new_name.strip():
                        result = self.saved_quiz_service.update_quiz_name(
                            quiz_id, user_id, new_name.strip()
                        )
                        if result.success:
                            st.success("Quiz renamed successfully!")
                            self._clear_rename_state()
                            st.rerun()
                        else:
                            st.error(result.message)
                    else:
                        st.warning("Please enter a quiz name")
            with col2:
                if st.form_submit_button("❌ Cancel"):
                    self._clear_rename_state()
                    st.rerun()
    
    def _show_delete_confirmation_form(self, user_id: str):
        """Show delete confirmation form"""
        quiz_id = st.session_state.get('delete_quiz_id')
        quiz_name = st.session_state.get('delete_quiz_name', 'Unknown Quiz')
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("🗑️ Delete Quiz")
        st.sidebar.warning(f"⚠️ Delete '{quiz_name}'?")
        st.sidebar.write("This action cannot be undone!")
        
        with st.sidebar.form("delete_quiz_form"):
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("🗑️ Delete", type="primary"):
                    result = self.saved_quiz_service.delete_quiz(quiz_id, user_id)
                    if result.success:
                        st.success("Quiz deleted successfully!")
                        self._clear_delete_state()
                        st.rerun()
                    else:
                        st.error(result.message)
            with col2:
                if st.form_submit_button("❌ Cancel"):
                    self._clear_delete_state()
                    st.rerun()
    
    def _clear_rename_state(self):
        """Clear rename state"""
        if 'rename_quiz_id' in st.session_state:
            del st.session_state.rename_quiz_id
        if 'rename_quiz_name' in st.session_state:
            del st.session_state.rename_quiz_name
    
    def _clear_delete_state(self):
        """Clear delete state"""
        if 'delete_quiz_id' in st.session_state:
            del st.session_state.delete_quiz_id
        if 'delete_quiz_name' in st.session_state:
            del st.session_state.delete_quiz_name
    
    def show_sidebar_quizzes(self, user_id: str, folder_id: str, folder_name: str):
        """Display saved quizzes in sidebar"""
        st.sidebar.header(f"📁 {folder_name}")
        st.sidebar.markdown("---")
        st.sidebar.subheader("📝 Saved Quizzes")
        
        # Get saved quizzes
        result = self.saved_quiz_service.get_folder_quizzes(user_id, folder_id)
        
        if result.success and result.data:
            for quiz in result.data:
                self._display_sidebar_quiz_item(quiz)
        else:
            st.sidebar.info("No saved quizzes yet!")
    
    def _display_sidebar_quiz_item(self, quiz: Dict[str, Any]):
        """Display quiz item in sidebar"""
        quiz_id = quiz['id']
        quiz_name = quiz['name']
        
        col1, col2, col3 = st.sidebar.columns([3, 1, 1])
        
        with col1:
            button_type = "primary" if self._is_selected_quiz(quiz_id) else "secondary"
            if st.button(
                f"📝 {quiz_name[:15]}{'...' if len(quiz_name) > 15 else ''}",
                key=f"sidebar_quiz_{quiz_id}",
                use_container_width=True,
                type=button_type
            ):
                self._select_quiz(quiz_id, quiz_name)
        
        with col2:
            if st.button("✏️", key=f"sidebar_rename_{quiz_id}", help="Rename"):
                st.session_state.rename_quiz_id = quiz_id
                st.session_state.rename_quiz_name = quiz_name
                st.rerun()
        
        with col3:
            if st.button("🗑️", key=f"sidebar_delete_{quiz_id}", help="Delete"):
                st.session_state.delete_quiz_id = quiz_id
                st.session_state.delete_quiz_name = quiz_name
                st.rerun()
        
        # Show quiz details
        st.sidebar.caption(f"📋 {quiz['type']} | {quiz['question_count']}Q")
    
    def _is_selected_quiz(self, quiz_id: str) -> bool:
        """Check if quiz is currently selected"""
        return st.session_state.get('selected_saved_quiz_id') == quiz_id
    
    @staticmethod
    def clear_all_saved_quiz_state():
        """Clear all saved quiz related session state"""
        keys_to_clear = []
        for key in list(st.session_state.keys()):
            if any(prefix in key for prefix in [
                'selected_saved_quiz', 'rename_quiz_', 'delete_quiz_',
                'app_mode'
            ]):
                keys_to_clear.append(key)
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]