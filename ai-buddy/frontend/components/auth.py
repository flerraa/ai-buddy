# File: frontend/components/auth.py

import streamlit as st
import hashlib
from typing import Optional, Dict, Any
from backend.services import AuthService

class AuthComponent:
    """Authentication component for user management"""
    
    def __init__(self):
        self.auth_service = AuthService()
    
    def check_authentication(self) -> bool:
        """Check if user is authenticated"""
        return st.session_state.get('authenticated', False)
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current authenticated user data"""
        if self.check_authentication():
            return st.session_state.get('user_data')
        return None
    
    def show_login_page(self):
        """Display login/registration page"""
        st.title("🦉 Welcome to AI Buddy")
        st.markdown("### Your Intelligent Study Companion")
        
        # Create tabs for login and registration
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])
        
        with tab1:
            self._show_login_form()
        
        with tab2:
            self._show_registration_form()
    
    def _show_login_form(self):
        """Show login form"""
        st.subheader("Login to Your Account")
        
        with st.form("login_form"):
            username = st.text_input("Username:", placeholder="Enter your username")
            password = st.text_input("Password:", type="password", placeholder="Enter your password")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                login_button = st.form_submit_button("🔑 Login", type="primary", use_container_width=True)
            with col2:
                st.form_submit_button("🔄 Clear", use_container_width=True)
            
            if login_button:
                self._handle_login(username, password)
    
    def _show_registration_form(self):
        """Show registration form"""
        st.subheader("Create New Account")
        
        with st.form("registration_form"):
            reg_username = st.text_input("Choose Username:", placeholder="Enter desired username")
            reg_email = st.text_input("Email (optional):", placeholder="Enter your email")
            reg_password = st.text_input("Choose Password:", type="password", placeholder="Choose a strong password")
            reg_confirm_password = st.text_input("Confirm Password:", type="password", placeholder="Confirm your password")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                register_button = st.form_submit_button("📝 Register", type="primary", use_container_width=True)
            with col2:
                st.form_submit_button("🔄 Clear", use_container_width=True)
            
            if register_button:
                self._handle_registration(reg_username, reg_email, reg_password, reg_confirm_password)
    
    def _handle_login(self, username: str, password: str):
        """Handle user login"""
        if not username or not password:
            st.error("Please enter both username and password")
            return
        
        with st.spinner("🔑 Logging in..."):
            result = self.auth_service.login_user(username.strip(), password)
            
            if result.success:
                # Clear any existing session state
                self.clear_all_session_state()
                
                # Set authentication state
                st.session_state.authenticated = True
                st.session_state.user_data = result.data
                st.session_state.user_id = str(result.data['_id'])
                st.session_state.username = result.data['username']
                
                st.success(f"✅ Welcome back, {result.data['username']}!")
                st.rerun()
            else:
                st.error(f"❌ Login failed: {result.message}")
    
    def _handle_registration(self, username: str, email: str, password: str, confirm_password: str):
        """Handle user registration"""
        # Validation
        if not username or not password:
            st.error("Username and password are required")
            return
        
        if len(username.strip()) < 3:
            st.error("Username must be at least 3 characters long")
            return
        
        if len(password) < 6:
            st.error("Password must be at least 6 characters long")
            return
        
        if password != confirm_password:
            st.error("Passwords do not match")
            return
        
        with st.spinner("📝 Creating account..."):
            result = self.auth_service.register_user(
                username.strip(), 
                password, 
                email.strip() if email else ""
            )
            
            if result.success:
                st.success("✅ Account created successfully! Please login.")
                st.balloons()
                # Switch to login tab (user will need to click login tab manually)
                st.info("👈 Click the Login tab to sign in with your new account")
            else:
                st.error(f"❌ Registration failed: {result.message}")
    
    def show_user_info(self):
        """Show user info in sidebar"""
        if not self.check_authentication():
            return
        
        user_data = self.get_current_user()
        if not user_data:
            return
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 👤 User Info")
        st.sidebar.write(f"**Username:** {user_data.get('username', 'Unknown')}")
        
        if user_data.get('email'):
            st.sidebar.write(f"**Email:** {user_data.get('email')}")
        
        # Show last login if available
        if user_data.get('last_login'):
            last_login = user_data['last_login']
            if hasattr(last_login, 'strftime'):
                st.sidebar.write(f"**Last Login:** {last_login.strftime('%Y-%m-%d %H:%M')}")
        
        st.sidebar.markdown("---")
        
        # Logout button
        if st.sidebar.button("🚪 Logout", key="sidebar_logout_btn", type="secondary", use_container_width=True):
            self.logout()
    
    def show_user_settings(self):
        """Show user settings interface"""
        if not self.check_authentication():
            st.error("Please login to access settings")
            return
        
        user_data = self.get_current_user()
        st.subheader("⚙️ User Settings")
        
        # Password change section
        with st.expander("🔒 Change Password"):
            with st.form("change_password_form"):
                current_password = st.text_input("Current Password:", type="password")
                new_password = st.text_input("New Password:", type="password")
                confirm_new_password = st.text_input("Confirm New Password:", type="password")
                
                if st.form_submit_button("🔒 Update Password", type="primary"):
                    self._handle_password_change(current_password, new_password, confirm_new_password)
        
        # Account info section
        with st.expander("ℹ️ Account Information"):
            st.write(f"**Username:** {user_data.get('username', 'Unknown')}")
            st.write(f"**Email:** {user_data.get('email', 'Not set')}")
            st.write(f"**Member Since:** {user_data.get('created_at', 'Unknown')}")
            st.write(f"**Account Status:** {user_data.get('status', 'Active').title()}")
    
    def _handle_password_change(self, current_password: str, new_password: str, confirm_new_password: str):
        """Handle password change"""
        if not all([current_password, new_password, confirm_new_password]):
            st.error("All password fields are required")
            return
        
        if new_password != confirm_new_password:
            st.error("New passwords do not match")
            return
        
        if len(new_password) < 6:
            st.error("New password must be at least 6 characters long")
            return
        
        user_id = st.session_state.get('user_id')
        if not user_id:
            st.error("User not found")
            return
        
        with st.spinner("🔒 Updating password..."):
            result = self.auth_service.update_user_password(user_id, current_password, new_password)
            
            if result.success:
                st.success("✅ Password updated successfully!")
            else:
                st.error(f"❌ Failed to update password: {result.message}")
    
    @staticmethod
    def logout():
        """Handle user logout - clear ALL session state"""
        # Import here to avoid circular imports
        try:
            from .quiz_display import QuizDisplay
            from .chat_interface import ChatInterface
            from .saved_quiz_manager import SavedQuizManager
            
            # Clear component-specific data
            
            ChatInterface.clear_all_chat_history()
            SavedQuizManager.clear_all_saved_quiz_state()
        except ImportError:
            # Components might not be available during testing
            pass
        
        # Clear everything except Streamlit internal keys
        streamlit_internal_keys = {
            '_rerun_queue', '_streamlit_params', '_script_run_count',
            '_widget_id_counter', '_new_widget_state', '_old_widget_state'
        }
        
        keys_to_clear = []
        for key in list(st.session_state.keys()):
            if key not in streamlit_internal_keys:
                keys_to_clear.append(key)
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        st.success("Logged out successfully!")
        st.rerun()
    
    @staticmethod
    def clear_all_session_state():
        """Clear all application session state (used during login)"""
        # Import here to avoid circular imports
        try:
            from .quiz_display import QuizDisplay
            from .chat_interface import ChatInterface
            from .saved_quiz_manager import SavedQuizManager
            
            # Clear component-specific data
           
            ChatInterface.clear_all_chat_history()
            SavedQuizManager.clear_all_saved_quiz_state()
        except ImportError:
            # Components might not be available during testing
            pass
        
        # Clear everything except Streamlit internal keys and authentication
        streamlit_internal_keys = {
            '_rerun_queue', '_streamlit_params', '_script_run_count',
            '_widget_id_counter', '_new_widget_state', '_old_widget_state'
        }
        
        keys_to_clear = []
        for key in list(st.session_state.keys()):
            if key not in streamlit_internal_keys and not key.startswith('authenticated'):
                keys_to_clear.append(key)
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
    
    def require_authentication(self):
        """Decorator-like method to require authentication"""
        if not self.check_authentication():
            st.error("🔒 Please login to access this feature")
            st.stop()
        return True
    
    def get_user_id(self) -> Optional[str]:
        """Get current user ID"""
        if self.check_authentication():
            return st.session_state.get('user_id')
        return None
    
    def get_username(self) -> Optional[str]:
        """Get current username"""
        if self.check_authentication():
            return st.session_state.get('username')
        return None
    
    def is_user_active(self) -> bool:
        """Check if current user account is active"""
        user_data = self.get_current_user()
        if user_data:
            return user_data.get('status', 'active').lower() == 'active'
        return False