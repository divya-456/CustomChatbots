import streamlit as st 
from .forms import create_chatbot_form, edit_chatbot_form
from .chat_interface import ChatInterface

def show_home_page():
    """
        UI for home page
    """
    st.title("🤖 Chatbot Management Platform")
    st.write("Welcome to your personal chatbot management platform! Create custom chatbots with their own system prompts and knowledge bases.")

    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:
        if st.button("➕ New Chatbot", type="primary", use_container_width=True):
            st.session_state.current_page = 'create'
            st.rerun()
    
    # Show existing chatbots
    chatbots = st.session_state.chatbot_manager.get_chatbot_list()
    
    if chatbots:
        st.subheader("Your Chatbots")
        
        cols = st.columns(min(3, len(chatbots)))
        for i, chatbot_name in enumerate(chatbots):
            with cols[i % 3]:
                with st.container():
                    st.write(f"**{chatbot_name}**")
                    chatbot_data = st.session_state.chatbot_manager.get_chatbot(chatbot_name)
                    st.write(f"System Prompt: {chatbot_data['system_prompt'][:100]}...")
                    st.write(f"Knowledge Base: {len(chatbot_data['knowledge_base'])} files")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"Chat", key=f"home_chat_{chatbot_name}"):
                            st.session_state.current_page = 'chat'
                            st.session_state.selected_chatbot = chatbot_name
                            st.query_params.chatbot = chatbot_name
                            st.rerun()
                    with col2:
                        if st.button(f"Edit", key=f"home_edit_{chatbot_name}"):
                            st.session_state.current_page = 'edit'
                            st.session_state.selected_chatbot = chatbot_name
                            st.rerun()

def show_create_chatbot_page():
    """
        UI for Create chatbot
    """

    st.title("Create New Chatbot")

    create_chatbot_form()

    # Back to home button
    if st.button("← Back to Home"):
        st.session_state.current_page = 'home'
        st.rerun()

def show_edit_chatbot_page():
    """
        UI for edit chatbot 
    """

    if not st.session_state.selected_chatbot:
        st.error("No chatbot selected for editing!")
        return
    
    chatbot_name = st.session_state.selected_chatbot
    chatbot_data = st.session_state.chatbot_manager.get_chatbot(chatbot_name)

    if not chatbot_data:
        st.error(f"Chatbot '{chatbot_name}' not found!")
        return
    
    st.title(f"Edit Chatbot: {chatbot_name}")

    edit_chatbot_form(chatbot_name, chatbot_data)

    # Back to home button
    if st.button("← Back to Home"):
        st.session_state.current_page = 'home'
        # Clean up any deletion confirmation
        if 'confirm_delete' in st.session_state:
            del st.session_state['confirm_delete']
        st.rerun()



def show_chat_page():
    """
        UI for chatbot interface
    """

    if not st.session_state.selected_chatbot:
        st.error("No chatbot selected!")
        return
    
    chatbot_name = st.session_state.selected_chatbot
    chatbot_data = st.session_state.chatbot_manager.get_chatbot(chatbot_name)

    if not chatbot_data:
        st.error(f"Chatbot '{chatbot_name}' not found!")
        return
    
    st.title(f"💬 Chat with {chatbot_name}")

    # Show chatbot info
    with st.expander("Chatbot Information"):
        st.write(f"**System Prompt:** {chatbot_data['system_prompt']}")
        st.write(f"**Knowledge Base:** {len(chatbot_data['knowledge_base'])} files uploaded")
    
    # Initialize chat interface
    chat_interface = ChatInterface(chatbot_data)
    chat_interface.render()