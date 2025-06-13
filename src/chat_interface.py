import streamlit as st
from openai import OpenAI
from .chatbot_manager import ChatbotManager
from typing import Optional, Dict, List


class ChatInterface:
    def __init__(self, chatbot_data: Optional[Dict]):
        """
            Initialize the chat interface for a specific chatbot.
            
            Args:
                chatbot_data: Dictionary containing chatbot configuration
        """

        self.chatbot_data = chatbot_data

        # Initialize OpenAI client
        api_key = st.secrets["OPENAI_API_KEY"]
        if not api_key:
            st.error("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
            return
        
        self.openai_client = OpenAI(api_key=api_key)

        # Initialize chat history - will load from database if available
        self.chat_key = f"chat_history_{self.chatbot_data['name']}"
        if self.chat_key not in st.session_state:
            # Try to load from database first, then fallback to empty list
            try:
                manager = ChatbotManager()
                if manager.db:
                    history = manager.get_chat_history(self.chatbot_data['name'])
                    st.session_state[self.chat_key] = history
                else:
                    st.session_state[self.chat_key] = []
            except:
                st.session_state[self.chat_key] = []




    def render(self):
        """Render the chat interface."""

        if not hasattr(self, 'openai_client'):
            st.error("OpenAI client not initialized. Please check your API key.")
            return
        
        chatbot_name = self.chatbot_data['name']
        chat_key = self.chat_key

        # Chat controls
        col1, col2 = st.columns([7, 1])
        with col2:
            if st.button("🗑️ Clear Chat"):
                st.session_state[chat_key] = []
                st.rerun()

        # Display chat history
        chat_container = st.container()

        with chat_container:
            # Show existing messages
            for message in st.session_state[chat_key]:
                with st.chat_message("user"):
                    st.write(message["user"])
                with st.chat_message("assistant"):
                    st.write(message["assistant"])

        # Chat input
        if prompt := st.chat_input("Type your message here..."):
            # Add user message to chat history
            with st.chat_message("user"):
                st.write(prompt)
            
            # Generate response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        response = self._generate_response(prompt)
                        st.write(response)

                        # Add to chat history
                        st.session_state[chat_key].append({
                            "user": prompt,
                            "assistant": response
                        })

                        # Save to database if available
                        try:
                            manager = ChatbotManager()
                            manager.update_chat_history(chatbot_name, prompt, response)
                        except:
                            pass  # Fallback to session state only
                        
                    except Exception as e:
                        error_message = f"Sorry, I encountered an error: {str(e)}"
                        st.error(error_message)
                        
                        # Add error to chat history
                        st.session_state[chat_key].append({
                            "user": prompt,
                            "assistant": error_message
                        })
    


    def _generate_response(self, user_message: str) -> str:
        """
        Generate a response using OpenAI API with the chatbot's configuration.
        
        Args:
            user_message: User's input message
            
        Returns:
            str: Generated response
        """

        try:
            # Prepare the system message with knowledge base context
            system_message = self.chatbot_data['system_prompt']

            # prepare conversation history
            messages = [
                {"role": "system", "content": system_message}
            ]

            # Add recent chat history for context (last 10 exchanges)
            recent_history = st.session_state.get(self.chat_key, [])[-10:]
            
            for exchange in recent_history:
                messages.append({"role": "user", "content": exchange["user"]})
                messages.append({"role": "assistant", "content": exchange["assistant"]})

            # get top-k from knowledge base vector db

            # Add current user message
            messages.append({"role": "user", "content": user_message})

            # Generate response using OpenAI
            # the newest OpenAI model is "gpt-4o-mini" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )

            return response.choices[0].message.content or "I apologize, but I couldn't generate a response."

        except Exception as e:
            raise Exception(f"Failed to generate response: {str(e)}")