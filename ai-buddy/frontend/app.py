import sys
import os
import streamlit as st
import logging

# Configure Streamlit
st.set_page_config(
    page_title="AI Buddy", 
    page_icon="🦉", 
    layout="wide"
)

from datetime import datetime
from backend.services import PDFService
from frontend.components import AuthComponent, FolderManager, QuizDisplay

# Configure logging
logger = logging.getLogger(__name__)


class AIBuddyApp:
    """Main AI Buddy application - FIXED PDF SELECTION VERSION"""
    
    def __init__(self):
        try:
            self.auth = AuthComponent()
            self.folder_manager = FolderManager()
            self.quiz_display = QuizDisplay()
            self.pdf_service = PDFService()
            logger.info("AIBuddyApp initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing AIBuddyApp: {e}")
            self.auth = None
            self.folder_manager = None
            self.quiz_display = None
            self.pdf_service = None
            raise
    
    def run(self):
        """Run the main application"""
        if not self.auth.check_authentication():
            self.auth.show_login_page()
        else:
            self.show_main_app()
    
    def show_main_app(self):
        """Show the main application interface"""
        user_data = self.auth.get_current_user()
        user_id = user_data['_id']
        username = user_data['username']
        
        # Initialize session state
        self._init_session_state(user_id)
        
        # Show header
        self._show_header(username, user_id)
        
        # Show sidebar with folders
        self.folder_manager.show_sidebar_folders(user_id)
        self.folder_manager.handle_folder_operations(user_id)
        
        # Show user info in sidebar
        self.auth.show_user_info()
        
        # Show main content
        self._show_main_content(user_id)
    
    def _init_session_state(self, user_id: str):
        """Initialize session state variables"""
        if 'selected_folder' not in st.session_state:
            st.session_state.selected_folder = None
        if 'selected_folder_name' not in st.session_state:
            st.session_state.selected_folder_name = None
        if 'selected_pdf' not in st.session_state:
            st.session_state.selected_pdf = None
        if 'selected_pdf_name' not in st.session_state:
            st.session_state.selected_pdf_name = None
        
        st.session_state.user_id = user_id
    
    def _show_header(self, username: str, user_id: str):
        """Show application header"""
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.title("🦉 AI Buddy")
            st.caption(f"Welcome back, **{username}**! 👋")
        
        with col2:
            try:
                pdf_count = self.pdf_service.get_pdf_count_for_user(user_id)
                st.metric("📄 Total PDFs", pdf_count)
            except:
                st.metric("📄 Total PDFs", "0")
        
        with col3:
            if st.button("🚪 Logout", key="header_logout_btn", type="secondary", use_container_width=True):
                self.auth.logout()
    
    def _show_main_content(self, user_id: str):
        """Show main content based on application state"""
        if st.session_state.selected_folder is None:
            self._show_welcome_screen()
        else:
            self._show_folder_interface(user_id)
    
    def _show_welcome_screen(self):
        """Show welcome screen when no folder is selected"""
        st.markdown("""
        ## 👋 Welcome to AI Buddy!
        
        **Get started in 3 easy steps:**
        
        1. **📁 Create a folder** - Click "➕ Add New Folder" in the sidebar
        2. **📄 Upload your PDF** - Upload educational materials  
        3. **🎯 Generate quiz** - AI creates personalized questions instantly!
        
        ### 🚀 Features:
        - **Interactive MCQ Quizzes** with clickable answers
        - **Open-ended Questions** with AI feedback
        - **Organized Folders** to manage your studies
        - **🦉 AI Tutor** - Context-aware chatbot during quizzes
        - **Reusable PDFs** - Generate multiple quizzes from same document
        
        ### 💡 Tips:
        - Upload educational PDFs for best results
        - Use descriptive folder names to stay organized
        - Try both quiz modes for comprehensive learning
        - Generate different quizzes from the same PDF with various difficulty levels
        """)
    
    def _show_folder_interface(self, user_id: str):
        """Show folder interface with PDFs and quiz generation"""
        folder_info = self.folder_manager.get_selected_folder_info()
        if not folder_info:
            st.error("No folder selected")
            return
        
        # Back button
        if st.button("← Back to Welcome", key="back_to_welcome_btn"):
            self._clear_all_context()
            st.rerun()
        
        st.header(f"📂 {folder_info['name']}")
        
        # Show PDF interface
        self._show_pdf_interface(user_id, folder_info['id'])
    
    def _show_pdf_interface(self, user_id: str, folder_id: str):
        """Show PDF management and quiz generation interface"""
        selected_pdf = st.session_state.get('selected_pdf')
        
        if selected_pdf and selected_pdf.get('id'):
            # Show quiz interface for selected PDF
            self._show_quiz_interface(user_id, selected_pdf)
        else:
            # Show PDF list and upload interface
            self._show_pdf_management_interface(user_id, folder_id)
    
    def _show_pdf_management_interface(self, user_id: str, folder_id: str):
        """Show PDF list, selection, and upload interface"""
        # Get PDFs in this folder
        pdfs_result = self.pdf_service.get_user_pdfs(user_id, folder_id)
        
        if pdfs_result.success and pdfs_result.data:
            st.subheader(f"📚 Your PDFs ({len(pdfs_result.data)} total):")
            
            # Display each PDF with actions
            for pdf in pdfs_result.data:
                self._display_pdf_item(pdf, user_id)
            
            # Handle PDF deletion if requested
            self._handle_pdf_deletion(user_id)
            
            st.markdown("---")
            st.markdown("### ⬆️ Upload New PDF:")
        else:
            st.info("📁 No PDFs in this folder yet. Upload one to get started!")
        
        # Show upload interface
        self._show_pdf_upload_form(user_id, folder_id)
    
    def _display_pdf_item(self, pdf: dict, user_id: str):
        """Display individual PDF with selection and delete options"""
        pdf_id = str(pdf.get('id', ''))
        pdf_name = pdf.get('original_name', pdf.get('name', 'Unknown PDF'))
        is_processed = pdf.get('processed', True)
        
        # Create columns for layout
        col1, col2, col3 = st.columns([3, 2, 1])
        
        with col1:
            # PDF info
            status_icon = "✅" if is_processed else "⏳"
            file_size_kb = self._safe_calculate_file_size(pdf)
            st.write(f"{status_icon} **{pdf_name}**")
            
            upload_date = pdf.get('upload_date', 'Unknown')
            if isinstance(upload_date, str) and len(upload_date) > 10:
                upload_date = upload_date[:10]
            st.caption(f"📅 {upload_date} | 📊 {file_size_kb} KB")
        
        with col2:
            # Selection button
            if is_processed:
                button_key = f"select_pdf_{pdf_id}_{hash(pdf_name)}"  # Unique key
                if st.button("🎯 Generate Quiz", key=button_key, type="primary", use_container_width=True):
                    self._select_pdf_for_quiz(pdf_id, pdf_name)
            else:
                st.info("⏳ Processing...")
        
        with col3:
            # Delete button
            delete_key = f"delete_pdf_{pdf_id}_{hash(pdf_name)}"  # Unique key
            if st.button("🗑️", key=delete_key, help="Delete PDF"):
                st.session_state.delete_pdf_id = pdf_id
                st.session_state.delete_pdf_name = pdf_name
                st.rerun()
        
        st.markdown("---")
    
    def _select_pdf_for_quiz(self, pdf_id: str, pdf_name: str):
        """Select a PDF for quiz generation"""
        try:
            # Clear any existing quiz context
            self._clear_quiz_context()
            
            # Create PDF data structure
            pdf_data = {
                'id': str(pdf_id),
                'name': str(pdf_name)
            }
            
            # Set in session state
            st.session_state.selected_pdf = pdf_data
            st.session_state.selected_pdf_name = str(pdf_name)
            
            # Log for debugging
            logger.info(f"PDF selected: ID={pdf_id}, Name={pdf_name}")
            
            # Show success and rerun
            st.success(f"✅ Selected: **{pdf_name}**")
            st.rerun()
            
        except Exception as e:
            st.error(f"Error selecting PDF: {str(e)}")
            logger.error(f"PDF selection error: {e}")
    
    def _show_pdf_upload_form(self, user_id: str, folder_id: str):
        """Show PDF upload form"""
        uploaded_file = st.file_uploader(
            "Choose a PDF file:",
            type="pdf",
            accept_multiple_files=False,
            help="Upload educational PDFs for best quiz results",
            key="pdf_uploader_main"
        )
        
        if uploaded_file:
            if st.button("⬆️ Upload PDF", key="upload_pdf_btn", type="primary", use_container_width=True):
                self._handle_pdf_upload(user_id, folder_id, uploaded_file)
    
    def _handle_pdf_upload(self, user_id: str, folder_id: str, uploaded_file):
        """Handle PDF upload process"""
        with st.spinner("📚 Uploading and processing PDF..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Update progress
                status_text.text("⬆️ Uploading PDF...")
                progress_bar.progress(25)
                
                # Read file content
                file_content = uploaded_file.read()
                uploaded_file.seek(0)  # Reset file pointer
                
                # Create file object for service
                import io
                file_obj = io.BytesIO(file_content)
                file_obj.name = uploaded_file.name
                
                # Upload via service
                progress_bar.progress(75)
                status_text.text("🔄 Processing content...")
                
                result = self.pdf_service.upload_pdf(
                    user_id=user_id,
                    folder_id=folder_id,
                    uploaded_file=file_obj,
                    original_name=uploaded_file.name
                )
                
                progress_bar.progress(100)
                
                if result.success:
                    status_text.text("✅ Upload complete!")
                    st.success("🎉 PDF uploaded and processed successfully!")
                    st.balloons()
                    
                    # Auto-select the uploaded PDF
                    pdf_data = {
                        'id': str(result.data.get('id', '')),
                        'name': str(uploaded_file.name)
                    }
                    
                    st.session_state.selected_pdf = pdf_data
                    st.session_state.selected_pdf_name = uploaded_file.name
                    
                    st.info("📝 Great! Now you can generate a quiz from your uploaded PDF.")
                    st.rerun()
                else:
                    status_text.text("❌ Upload failed")
                    st.error(f"Upload failed: {result.message}")
                    
            except Exception as e:
                st.error(f"Upload error: {str(e)}")
                logger.error(f"PDF upload error: {e}")
    
    def _show_quiz_interface(self, user_id: str, pdf_data: dict):
        """Show quiz generation and interaction interface"""
        try:
            # Validate PDF data
            if not pdf_data or not pdf_data.get('id'):
                st.error("❌ Invalid PDF selection. Please select a PDF again.")
                st.session_state.selected_pdf = None
                st.session_state.selected_pdf_name = None
                st.rerun()
                return
            
            pdf_id = str(pdf_data['id'])
            pdf_name = str(pdf_data.get('name', 'Unknown PDF'))
            
            # Header with PDF info and change option
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.success(f"📄 Ready to generate quiz from: **{pdf_name}**")
            
            with col2:
                if st.button("📁 Change PDF", key="change_pdf_btn", type="secondary"):
                    self._clear_pdf_selection()
                    st.rerun()
            
            st.markdown("---")
            
            # Show quiz interface
            if self.quiz_display._has_active_quiz():
                # Display existing quiz
                self.quiz_display.display_quiz()
            else:
                # Show quiz generator
                self.quiz_display.show_quiz_generator(user_id, pdf_id, pdf_name)
                
        except Exception as e:
            st.error(f"Error in quiz interface: {str(e)}")
            st.write("Please try selecting the PDF again.")
            
            # Clear invalid state
            self._clear_pdf_selection()
            
            # Show error details for debugging
            with st.expander("🐛 Error Details"):
                import traceback
                st.code(traceback.format_exc())
    
    def _handle_pdf_deletion(self, user_id: str):
        """Handle PDF deletion confirmation dialog"""
        if 'delete_pdf_id' in st.session_state and 'delete_pdf_name' in st.session_state:
            pdf_id = st.session_state.delete_pdf_id
            pdf_name = st.session_state.delete_pdf_name
            
            st.warning(f"⚠️ Are you sure you want to delete **{pdf_name}**?")
            
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                if st.button("✅ Yes, Delete", key=f"confirm_delete_{pdf_id}", type="primary"):
                    with st.spinner(f"🗑️ Deleting {pdf_name}..."):
                        result = self.pdf_service.delete_pdf(pdf_id, user_id)
                        
                        if result.success:
                            st.success(f"✅ **{pdf_name}** deleted successfully!")
                            
                            # Clear selection if deleted PDF was selected
                            if (st.session_state.get('selected_pdf') and 
                                st.session_state.selected_pdf.get('id') == pdf_id):
                                self._clear_pdf_selection()
                            
                            # Clear deletion state
                            del st.session_state.delete_pdf_id
                            del st.session_state.delete_pdf_name
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to delete: {result.message}")
            
            with col2:
                if st.button("❌ Cancel", key=f"cancel_delete_{pdf_id}"):
                    del st.session_state.delete_pdf_id
                    del st.session_state.delete_pdf_name
                    st.rerun()
            
            with col3:
                st.empty()
    
    def _safe_calculate_file_size(self, pdf: dict) -> int:
        """Safely calculate file size in KB"""
        try:
            file_size = pdf.get('file_size', 0)
            
            if file_size is None or file_size == "":
                return 0
                
            if isinstance(file_size, str):
                try:
                    file_size = float(file_size)
                except (ValueError, TypeError):
                    return 0
            
            if not isinstance(file_size, (int, float)) or file_size < 0:
                return 0
                
            # Convert to KB
            return int(file_size) // 1024 if file_size > 1024 else int(file_size)
            
        except Exception:
            return 0
    
    def _clear_all_context(self):
        """Clear all application context (back to welcome)"""
        keys_to_clear = [
            'selected_folder', 'selected_folder_name', 
            'selected_pdf', 'selected_pdf_name'
        ]
        
        # Clear quiz-related keys
        for key in list(st.session_state.keys()):
            if any(prefix in key for prefix in [
                'current_quiz', 'quiz_questions', 'quiz_answers', 'quiz_completed',
                'quiz_chatbot_', 'open_quiz_chatbot_', 'quiz_user_id', 'quiz_pdf_id',
                'quiz_saved', 'quiz_feedback', 'quiz_score_data', 'feedback_shown'
            ]):
                keys_to_clear.append(key)
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
    
    def _clear_pdf_selection(self):
        """Clear PDF selection and return to PDF list"""
        st.session_state.selected_pdf = None
        st.session_state.selected_pdf_name = None
        self._clear_quiz_context()
    
    def _clear_quiz_context(self):
        """Clear quiz-specific context"""
        keys_to_clear = []
        for key in list(st.session_state.keys()):
            if any(prefix in key for prefix in [
                'current_quiz', 'quiz_questions', 'quiz_answers', 'quiz_completed',
                'quiz_chatbot_', 'open_quiz_chatbot_', 'quiz_user_id', 'quiz_pdf_id',
                'quiz_saved', 'quiz_feedback', 'quiz_score_data', 'feedback_shown'
            ]):
                keys_to_clear.append(key)
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]


def main():
    """Main application entry point"""
    try:
        app = AIBuddyApp()
        app.run()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.info("Please refresh the page or contact support if the problem persists.")
        with st.expander("🐛 Error Details"):
            st.code(str(e))


if __name__ == "__main__":
    main()