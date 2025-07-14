import streamlit as st
from typing import List, Dict, Any
from backend.services import ChatService

class ChatInterface:
    """Chat interface component for PDF interaction"""
    
    def __init__(self):
        self.chat_service = ChatService()
    
    def show_chat_interface(self, user_id: str, pdf_id: str, pdf_name: str):
        """Display the main chat interface"""
        st.subheader(f"💬 Chat with: {pdf_name}")
        
        # Initialize chat history for this specific PDF
        self._init_chat_history(pdf_id)
        
        # Display chat messages
        self._display_chat_messages(pdf_id)
        
        # Chat input
        self._handle_chat_input(user_id, pdf_id)
        
        # Chat controls
        self._show_chat_controls(pdf_id)
    
    def _init_chat_history(self, pdf_id: str):
        """Initialize chat history for the specific PDF"""
        chat_key = f"chat_messages_{pdf_id}"
        if chat_key not in st.session_state:
            st.session_state[chat_key] = []
    
    def _display_chat_messages(self, pdf_id: str):
        """Display chat message history"""
        chat_key = f"chat_messages_{pdf_id}"
        messages = st.session_state.get(chat_key, [])
        
        if not messages:
            # Show welcome message
            with st.chat_message("assistant"):
                st.write("👋 Hello! I'm ready to help you understand this document. Ask me anything!")
        
        # Display message history
        for message in messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
    
    def _handle_chat_input(self, user_id: str, pdf_id: str):
        """Handle chat input and generate responses"""
        chat_key = f"chat_messages_{pdf_id}"
        
        # Chat input with unique key for this PDF
        if prompt := st.chat_input("Ask me anything about the PDF...", key=f"chat_input_{pdf_id}"):
            # Add user message
            st.session_state[chat_key].append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.write(prompt)
            
            # Generate and display AI response
            with st.chat_message("assistant"):
                with st.spinner("🤔 Thinking..."):
                    result = self.chat_service.chat_with_pdf(user_id, pdf_id, prompt, "Explain")
                    
                    if result.success:
                        response = result.data['response']
                        st.write(response)
                        
                        # Add AI response to history
                        st.session_state[chat_key].append({
                            "role": "assistant", 
                            "content": response
                        })
                    else:
                        error_msg = f"I'm sorry, I encountered an error: {result.message}"
                        st.error(error_msg)
                        
                        # Add error to history
                        st.session_state[chat_key].append({
                            "role": "assistant", 
                            "content": error_msg
                        })
    
    def _show_chat_controls(self, pdf_id: str):
        """Show chat control buttons"""
        chat_key = f"chat_messages_{pdf_id}"
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            if st.button("🔄 New Conversation", key=f"new_conv_{pdf_id}", use_container_width=True):
                st.session_state[chat_key] = []
                st.rerun()
        
        with col2:
            if st.button("📋 Example Questions" , key=f"example_qs_{pdf_id}", use_container_width=True):
                self._show_example_questions(pdf_id)
        
        with col3:
            message_count = len(st.session_state.get(chat_key, []))
            st.metric("Messages", message_count)
    
    def _show_example_questions(self, pdf_id: str):
        """Show example questions to help users get started"""
        st.markdown("### 💡 Example Questions to Try:")
        
        example_questions = [
            "📋 What are the main topics covered in this document?",
            "🔍 Can you summarize the key points?",
            "❓ What is the most important concept explained?",
            "📊 Are there any statistics or data mentioned?",
            "🎯 What are the main conclusions or recommendations?",
            "🔗 How do the different sections relate to each other?",
            "📝 Can you explain [specific term] mentioned in the document?",
            "🔍 What examples are provided to illustrate the concepts?"
        ]
        
        for i, question in enumerate(example_questions):
            if st.button(question, key=f"example_{pdf_id}_{i}", use_container_width=True):
                # Add the example question to chat
                chat_key = f"chat_messages_{pdf_id}"
                clean_question = question.split("] ", 1)[1] if "] " in question else question[2:]  # Remove emoji prefix
                
                st.session_state[chat_key].append({
                    "role": "user", 
                    "content": clean_question
                })
                st.rerun()
    
    def show_chat_sidebar_info(self, pdf_name: str, pdf_id: str):
        """Show chat-related information in sidebar"""
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 💬 Chat Mode")
        st.sidebar.info(f"**Current PDF:** {pdf_name}")
        
        st.sidebar.markdown("**Tips for better conversations:**")
        st.sidebar.markdown("""
        - Ask specific questions about the content
        - Request explanations of complex concepts
        - Ask for examples or clarifications
        - Request summaries of specific sections
        """)
        
        # Show conversation stats for this specific PDF
        chat_key = f"chat_messages_{pdf_id}"
        if chat_key in st.session_state:
            total_messages = len(st.session_state[chat_key])
            if total_messages > 0:
                st.sidebar.metric("Total Messages", total_messages)
        
        # Add clear chat button in sidebar
        if st.sidebar.button("🗑️ Clear Chat History", key=f"clear_chat_sidebar_{pdf_id}"):
            chat_key = f"chat_messages_{pdf_id}"
            st.session_state[chat_key] = []
            st.rerun()
    
    def export_conversation(self, pdf_id: str, pdf_name: str) -> str:
        """Export conversation history as text"""
        chat_key = f"chat_messages_{pdf_id}"
        messages = st.session_state.get(chat_key, [])
        
        if not messages:
            return "No conversation to export."
        
        export_text = f"# Chat Conversation with {pdf_name}\n\n"
        
        for i, message in enumerate(messages, 1):
            role = "You" if message["role"] == "user" else "AI Assistant"
            export_text += f"**{role}:** {message['content']}\n\n"
        
        return export_text
    
    def get_conversation_summary(self, user_id: str, pdf_id: str) -> str:
        """Get AI-generated summary of the conversation"""
        chat_key = f"chat_messages_{pdf_id}"
        messages = st.session_state.get(chat_key, [])
        
        if not messages:
            return "No conversation to summarize."
        
        # Create conversation context
        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}" for msg in messages
        ])
        
        summary_query = f"Please provide a brief summary of this conversation: {conversation_text}"
        
        result = self.chat_service.chat_with_pdf(user_id, pdf_id, summary_query, "Explain")
        
        if result.success:
            return result.data['response']
        else:
            return "Could not generate conversation summary."
    
    @staticmethod
    def clear_all_chat_history():
        """Clear all chat history for all PDFs (used during logout)"""
        keys_to_clear = []
        for key in list(st.session_state.keys()):
            if key.startswith('chat_messages_'):
                keys_to_clear.append(key)
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]