import streamlit as st
from typing import List, Dict, Optional
from chat_service import OllamaService
from chat_repository import ChatRepository

class ChatApp:
    """
    Main application class for the Ollama Chat UI.
    Handles the View logic and state management.
    """
    
    def __init__(self, service: OllamaService, repository: ChatRepository):
        self.service = service
        self.repository = repository
        self._setup_page()
        self._initialize_state()

    def _setup_page(self):
        """Configures the Streamlit page settings."""
        st.set_page_config(
            page_title="Ollama Chat",
            page_icon="🤖",
            layout="wide"
        )

    def _initialize_state(self):
        """Initializes the session state variables."""
        if "selected_model" not in st.session_state:
            st.session_state.selected_model = ""
            
        # Initialize current session ID
        if "current_session_id" not in st.session_state:
            self._load_latest_or_new_session()

    def _load_latest_or_new_session(self):
        """Helper to load the most recent session or create a new one."""
        sessions = self.repository.get_all_sessions()
        if sessions:
            st.session_state.current_session_id = sessions[0]['id']
        else:
            st.session_state.current_session_id = self.repository.create_session()

    def render_sidebar(self):
        """Renders the sidebar configuration."""
        with st.sidebar:
            st.title("⚙️ Settings")
            
            # New Chat Button
            if st.button("New Chat", type="primary", use_container_width=True):
                st.session_state.current_session_id = self.repository.create_session()
                st.rerun()
            
            st.divider()
            
            # Model Selection
            available_models = self.service.get_models()
            if available_models:
                current_index = 0
                if st.session_state.selected_model in available_models:
                    current_index = available_models.index(st.session_state.selected_model)
                
                st.session_state.selected_model = st.selectbox(
                    "Select Model",
                    available_models,
                    index=current_index
                )
            else:
                st.error("No models found. Is Ollama running?")
                st.info("Try running `ollama pull llama3` in your terminal.")
            
            st.divider()
            
            # Chat History List
            st.subheader("History")
            sessions = self.repository.get_all_sessions()
            
            for session in sessions:
                col1, col2 = st.columns([0.85, 0.15])
                
                with col1:
                    # Highlight the current session
                    button_type = "primary" if session['id'] == st.session_state.current_session_id else "secondary"
                    if st.button(
                        f"{session['title']}", 
                        key=f"session_{session['id']}", 
                        use_container_width=True,
                        type=button_type
                    ):
                        st.session_state.current_session_id = session['id']
                        st.rerun()
                
                with col2:
                    if st.button("🗑️", key=f"del_{session['id']}", help="Delete chat"):
                        self.repository.delete_session(session['id'])
                        
                        # If we deleted the current session, switch to another
                        if st.session_state.current_session_id == session['id']:
                            del st.session_state.current_session_id
                            # Rerun will trigger _initialize_state which calls _load_latest_or_new_session
                        st.rerun()

    def render_chat_area(self):
        """Renders the chat history messages."""
        # Ensure we have a valid session ID
        if "current_session_id" not in st.session_state:
             self._load_latest_or_new_session()
             
        # Verify session still exists (in case of manual DB edits or race conditions)
        try:
             messages = self.repository.get_messages(st.session_state.current_session_id)
        except Exception:
             # Fallback if session ID is invalid
             self._load_latest_or_new_session()
             messages = self.repository.get_messages(st.session_state.current_session_id)
        
        for message in messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        return messages

    def handle_user_input(self, current_messages: List[Dict]):
        """Handles user input and generates assistant response."""
        if prompt := st.chat_input("Message Ollama..."):
            # 1. Display user message immediately
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # 2. Save user message to DB
            self.repository.add_message(st.session_state.current_session_id, "user", prompt)

            # 3. Generate and display assistant response
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                
                if not st.session_state.selected_model:
                    st.error("Please select a model first.")
                    return

                try:
                    # Prepare context for API (exclude timestamps etc, just role/content)
                    # We might want to limit context window size here for scalability
                    api_messages = [
                        {"role": m["role"], "content": m["content"]} 
                        for m in current_messages
                    ]
                    api_messages.append({"role": "user", "content": prompt})

                    # Stream the response
                    stream = self.service.chat_stream(
                        model=st.session_state.selected_model,
                        messages=api_messages
                    )
                    
                    for chunk in stream:
                        full_response += chunk
                        message_placeholder.markdown(full_response + "▌")
                    
                    message_placeholder.markdown(full_response)
                    
                    # 4. Save assistant response to DB
                    self.repository.add_message(st.session_state.current_session_id, "assistant", full_response)
                    
                    # Rerun to update the session title in sidebar if it changed
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"An error occurred: {e}")

    def run(self):
        """Main execution method."""
        self.render_sidebar()
        
        st.title("🤖 Ollama UI")
        
        current_messages = self.render_chat_area()
        self.handle_user_input(current_messages)

def main():
    # Dependency Injection
    service = OllamaService()
    repository = ChatRepository()
    app = ChatApp(service, repository)
    app.run()

if __name__ == "__main__":
    main()
