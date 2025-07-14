import streamlit as st
from backend.services import FolderService, PDFService, SavedQuizService

class FolderManager:
    """Folder management UI component"""

    def __init__(self):
        self.folder_service = FolderService()
        self.pdf_service = PDFService()
        self.saved_quiz_service = SavedQuizService()

    def show_sidebar_folders(self, user_id: str):
        """Display folder management in sidebar"""
        st.sidebar.header("📁 Folders")

        if st.sidebar.button("➕ Add New Folder", key="add_new_folder_btn", type="primary", use_container_width=True):
            self._show_add_folder_dialog(user_id)

        folders_result = self.folder_service.get_user_folders(user_id)

        if folders_result.success and folders_result.data:
            st.sidebar.markdown("---")
            for folder in folders_result.data:
                self._display_folder_item(folder, user_id)
        else:
            st.sidebar.info("Click ➕ to create your first folder!")

    def _display_folder_item(self, folder: dict, user_id: str):
        """Display individual folder item"""
        folder_id = folder['id']
        folder_name = folder['name']

        col1, col2, col3 = st.sidebar.columns([3, 1, 1])

        with col1:
            button_type = "primary" if self._is_selected_folder(folder_id) else "secondary"
            if st.button(
                f"📂 {folder_name}",
                key=f"folder_{folder_id}",
                use_container_width=True,
                type=button_type
            ):
                self._clear_folder_context()
                st.session_state.selected_folder = folder_id
                st.session_state.selected_folder_name = folder_name
                st.session_state.app_mode = None
                st.rerun()

        with col2:
            if st.button("✏️", key=f"rename_{folder_id}", help="Rename folder"):
                st.session_state.rename_folder_id = folder_id
                st.session_state.rename_folder_name = folder_name
                st.rerun()

        with col3:
            if st.button("🗑️", key=f"delete_{folder_id}", help="Delete folder"):
                st.session_state.delete_folder_id = folder_id
                st.session_state.delete_folder_name = folder_name
                st.rerun()

    def _clear_folder_context(self):
        keys_to_clear = []
        for key in list(st.session_state.keys()):
            if any(prefix in key for prefix in [
                'selected_pdf', 'current_quiz', 'quiz_questions', 'quiz_answers',
                'quiz_chatbot_', 'open_quiz_chatbot_', 'quiz_completed',
                'quiz_user_id', 'quiz_pdf_id', 'chat_messages_', 'app_mode',
                'selected_saved_quiz'  # Clear saved quiz selections too
            ]):
                keys_to_clear.append(key)

        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]

    def _show_add_folder_dialog(self, user_id: str):
        st.session_state.show_add_folder = True
        st.rerun()

    def handle_folder_operations(self, user_id: str):
        if st.session_state.get('show_add_folder', False):
            self._show_add_folder_form(user_id)

        if st.session_state.get('rename_folder_id'):
            self._show_rename_folder_form(user_id)

        if st.session_state.get('delete_folder_id'):
            self._show_delete_confirmation_form(user_id)

    def _show_add_folder_form(self, user_id: str):
        st.sidebar.markdown("---")
        st.sidebar.subheader("➕ Add New Folder")

        with st.sidebar.form("add_folder_form"):
            folder_name = st.text_input("Folder name:", placeholder="Enter folder name")
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("✅ Create", type="primary"):
                    if folder_name.strip():
                        result = self.folder_service.create_folder(user_id, folder_name.strip())
                        if result.success:
                            st.success("Folder created successfully!")
                            st.session_state.show_add_folder = False
                            st.rerun()
                        else:
                            st.error(result.message)
                    else:
                        st.warning("Please enter a folder name")
            with col2:
                if st.form_submit_button("❌ Cancel"):
                    st.session_state.show_add_folder = False
                    st.rerun()

    def _show_rename_folder_form(self, user_id: str):
        folder_id = st.session_state.get('rename_folder_id')
        current_name = st.session_state.get('rename_folder_name', '')

        st.sidebar.markdown("---")
        st.sidebar.subheader("✏️ Rename Folder")

        with st.sidebar.form("rename_folder_form"):
            new_name = st.text_input("New folder name:", value=current_name)
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("✅ Save", type="primary"):
                    if new_name.strip():
                        result = self.folder_service.update_folder_name(
                            folder_id, user_id, new_name.strip()
                        )
                        if result.success:
                            st.success("Folder renamed successfully!")
                            self._clear_rename_state()
                            st.rerun()
                        else:
                            st.error(result.message)
                    else:
                        st.warning("Please enter a folder name")
            with col2:
                if st.form_submit_button("❌ Cancel"):
                    self._clear_rename_state()
                    st.rerun()

    def _show_delete_confirmation_form(self, user_id: str):
        folder_id = st.session_state.get('delete_folder_id')
        folder_name = st.session_state.get('delete_folder_name', 'Unknown Folder')

        st.sidebar.markdown("---")
        st.sidebar.subheader("🗑️ Delete Folder")

        # Get counts for PDFs and quizzes
        pdfs_result = self.pdf_service.get_user_pdfs(user_id, folder_id)
        pdf_count = len(pdfs_result.data) if pdfs_result.success else 0
        
        quizzes_result = self.saved_quiz_service.get_folder_quizzes(user_id, folder_id)
        quiz_count = len(quizzes_result.data) if quizzes_result.success else 0

        st.sidebar.warning(f"⚠️ Delete '{folder_name}'?")
        if pdf_count > 0:
            st.sidebar.write(f"This will delete {pdf_count} PDF(s)")
        if quiz_count > 0:
            st.sidebar.write(f"and {quiz_count} saved quiz(zes)!")

        with st.sidebar.form("delete_folder_form"):
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("🗑️ Delete", type="primary"):
                    self._delete_folder_and_contents(folder_id, user_id)
            with col2:
                if st.form_submit_button("❌ Cancel"):
                    self._clear_delete_state()
                    st.rerun()

    def _delete_pdf(self, pdf_id: str, user_id: str):
        """Delete PDF and associated quizzes"""
        with st.spinner("🗑️ Deleting PDF and associated quizzes..."):
            # First delete associated quizzes
            self.saved_quiz_service.delete_quizzes_by_pdf(pdf_id, user_id)
            
            # Then delete the PDF
            result = self.pdf_service.delete_pdf(pdf_id, user_id)
            if result.success:
                st.success(f"PDF and associated quizzes deleted successfully!")
                if st.session_state.get('selected_pdf') == pdf_id:
                    self._clear_pdf_context()
                st.rerun()
            else:
                st.error(result.message)

    def _clear_pdf_context(self):
        keys_to_clear = []
        for key in list(st.session_state.keys()):
            if any(prefix in key for prefix in [
                'selected_pdf', 'current_quiz', 'quiz_questions', 'quiz_answers',
                'quiz_chatbot_', 'open_quiz_chatbot_', 'quiz_completed',
                'quiz_user_id', 'quiz_pdf_id', 'chat_messages_', 'app_mode'
            ]):
                keys_to_clear.append(key)

        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]

    def _delete_folder_and_contents(self, folder_id: str, user_id: str):
        """Delete folder and all its contents (PDFs and quizzes)"""
        with st.spinner("🗑️ Deleting folder and all contents..."):
            # Delete all quizzes in the folder
            self.saved_quiz_service.delete_quizzes_by_folder(folder_id, user_id)
            
            # Delete all PDFs in the folder
            self.pdf_service.delete_folder_pdfs(folder_id, user_id)
            
            # Delete the folder itself
            folder_result = self.folder_service.delete_folder(folder_id, user_id)
            
            if folder_result.success:
                st.success(f"Folder and all contents deleted successfully!")
                if st.session_state.get('selected_folder') == folder_id:
                    self._clear_folder_context()
                    st.session_state.selected_folder = None
                    st.session_state.selected_folder_name = None
                    st.session_state.app_mode = None
                self._clear_delete_state()
                st.rerun()
            else:
                st.error(folder_result.message)

    def _clear_delete_state(self):
        if 'delete_folder_id' in st.session_state:
            del st.session_state.delete_folder_id
        if 'delete_folder_name' in st.session_state:
            del st.session_state.delete_folder_name

    def _clear_rename_state(self):
        if 'rename_folder_id' in st.session_state:
            del st.session_state.rename_folder_id
        if 'rename_folder_name' in st.session_state:
            del st.session_state.rename_folder_name

    def _is_selected_folder(self, folder_id: str) -> bool:
        return st.session_state.get('selected_folder') == folder_id

    def get_selected_folder_info(self) -> dict:
        selected_id = st.session_state.get('selected_folder')
        selected_name = st.session_state.get('selected_folder_name')
        if selected_id:
            return {
                'id': selected_id,
                'name': selected_name or 'Selected Folder'
            }
        return None

    def show_pdf_list_with_delete(self, user_id: str, folder_id: str):
        """Show PDF list with immediate delete behavior"""
        pdfs_result = self.pdf_service.get_user_pdfs(user_id, folder_id)

        if pdfs_result.success and pdfs_result.data:
            st.markdown("### 📄 Your PDFs in this folder:")

            for pdf in pdfs_result.data:
                pdf_id = str(pdf['id'])
                pdf_name = pdf['name']

                col1, col2, col3 = st.columns([6, 2, 1])

                with col1:
                    st.success(f"✅ {pdf_name}")
                    st.caption(f"Uploaded: {pdf.get('uploaded_at', 'Unknown')} | Size: {pdf.get('file_size', '?')} KB")

                with col2:
                    if st.button("🎯 Select PDF", key=f"use_pdf_{pdf_id}", type="primary"):
                        self._clear_pdf_context()
                        st.session_state.selected_pdf = pdf_id
                        st.session_state.selected_pdf_name = pdf_name
                        st.rerun()

                with col3:
                    if st.button("🗑️", key=f"delete_pdf_{pdf_id}", help="Delete PDF"):
                        self._delete_pdf(pdf_id, user_id)

            st.markdown("---")

        else:
            st.info("No PDFs in this folder yet. Upload some PDFs to get started!")
            
    def show_content_stats(self, user_id: str, folder_id: str):
        """Show statistics about folder contents"""
        pdfs_result = self.pdf_service.get_user_pdfs(user_id, folder_id)
        quizzes_result = self.saved_quiz_service.get_folder_quizzes(user_id, folder_id)
        
        pdf_count = len(pdfs_result.data) if pdfs_result.success else 0
        quiz_count = len(quizzes_result.data) if quizzes_result.success else 0
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📄 PDFs", pdf_count)
        with col2:
            st.metric("📝 Saved Quizzes", quiz_count)