import streamlit as st
import os
from src.chatbot_manager import ChatbotManager
from src.pages import show_home_page, show_chat_page, show_create_chatbot_page, show_edit_chatbot_page


def set_page_config():
    """
        Set the web page configurations
    """

    st.set_page_config(
        page_title="Chatbot Management Platform",
        page_icon="🤖",
        layout="wide"
    )


set_page_config()

# Initialize session state
if 'chatbot_manager' not in st.session_state:
    st.session_state.chatbot_manager = ChatbotManager()

if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'

if 'selected_chatbot' not in st.session_state:
    st.session_state.selected_chatbot = None



def handle_url_routing(query_params):
    """
        Handle chatbots according the url,
        if url is /medical_chatbot
        check the chatbot exist and open its page and select it
    """

    if 'chatbot' in query_params:
        chatbot_name = query_params['chatbot']
        if chatbot_name in st.session_state.chatbot_manager.chatbots:
            st.session_state.current_page = 'chat'
            st.session_state.selected_chatbot = chatbot_name
        else:
            st.error(f"Chatbot '{chatbot_name}' not found!")
            st.session_state.current_page = 'home'


def create_sidebar():
    """
        Creates a UI for sidebar 
        where all chatbots are listed
    """

    with st.sidebar:
        st.title("🤖 My Chatbots")
        
        chatbots = st.session_state.chatbot_manager.get_chatbot_list()
        
        if chatbots:
            st.write("Click on a chatbot to start chatting:")
            for chatbot_name in chatbots:
                if st.button(f"💬 {chatbot_name}", key=f"sidebar_{chatbot_name}"):
                    st.session_state.current_page = 'chat'
                    st.session_state.selected_chatbot = chatbot_name
                    st.query_params.chatbot = chatbot_name
                    st.rerun()
        else:
            st.write("No chatbots created yet.")
        
        st.divider()
        
        if st.button("🏠 Home"):
            st.session_state.current_page = 'home'
            st.session_state.selected_chatbot = None
            st.query_params.clear()
            st.rerun()




def main_content_area():
    """
        Selects UI According to current page information came from url routing
    """

    if st.session_state.current_page == "home":
        show_home_page()
    elif st.session_state.current_page == "create":
        show_create_chatbot_page()
    elif st.session_state.current_page == "edit":
        show_edit_chatbot_page()
    elif st.session_state.current_page == "chat":
        show_chat_page()


def main():
    """
        Controller of the flow of our program
    """
    
    

    # Parse URL parameters to handle routing
    query_params = st.query_params

    # Handle URL routing
    handle_url_routing(query_params)

    create_sidebar()

    main_content_area()

if __name__ == "__main__":
    main()