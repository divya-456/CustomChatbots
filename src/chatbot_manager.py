from .database_manager import DatabaseManager
from .file_processor import FileProcessor
from .utils.generate_chunks import chunk_with_recursive_splitter
from.weaviate_manager import WeaviateManager
import streamlit as st
from typing import Dict, List, Optional




class ChatbotManager:
    def __init__(self):
        self.file_processor = FileProcessor()
        self.weaviate_manager = WeaviateManager()
        try:
            self.db = DatabaseManager()
        except Exception as e:
            st.error(f"Database Connection failed : {str(e)}")
            # Fallback to session state if database fails
            if 'chatbots' not in st.session_state:
                st.session_state.chatbots = {}
            self.db = None

    @property
    def chatbots(self) -> Dict :
        """Get all chatbots as a dictionary."""
        if self.db:
            # Convert database chatbots to dict format for compatibility
            chatbot_names = self.db.get_all_chatbots()
            chatbots_dict = {}
            for name in chatbot_names:
                chatbot_data = self.db.get_chatbot(name)
                if chatbot_data:
                    chatbots_dict[name] = chatbot_data
            return chatbots_dict
        else:
            return st.session_state.chatbots

    def create_chatbot(self, name: str, system_prompt: str, uploaded_files: List = None) -> bool:
        """
            Create a new chatbot with the given parameters.
            
            Args:
                name: Unique name for the chatbot
                system_prompt: System prompt to guide chatbot behavior
                uploaded_files: List of uploaded files for knowledge base
                
            Returns:
                bool: True if chatbot was created successfully, False otherwise
        """
        try:
            # Process uploaded files for knowledge base
            knowledge_base = []
            knowledge_base_chunks = []
            if uploaded_files:
                for uploaded_file in uploaded_files:
                    try:
                        processed_content = self.file_processor.process_file(uploaded_file)
                        knowledge_base.append({
                            'filename': uploaded_file.name,
                            'content': processed_content,
                            'type': uploaded_file.type
                        })
                        file_chunks = chunk_with_recursive_splitter(processed_content)
                        
                        for i,chunk in enumerate(file_chunks):
                            knowledge_base_chunks.append({
                                "filename": uploaded_file.name,
                                "chunk_index": i,
                                "content": chunk,
                                "type": uploaded_file.type
                            })
                

                    except Exception as e:
                        st.warning(f"Could not process file {uploaded_file.name}: {str(e)}")

                # Create embeddings and push to weaviate
                
                self.weaviate_manager.create_weaviate_class(chatbot_name = name)
                self.weaviate_manager.push_chunks_to_weaviate(chatbot_name=name, chunks=knowledge_base_chunks)


            if self.db:
                # Store in database
                return self.db.create_chatbot(name, system_prompt, knowledge_base)
            else:
                # Fallback to session state
                chatbot_data = {
                    'name': name,
                    'system_prompt': system_prompt,
                    'knowledge_base': knowledge_base,
                    'chat_history': []
                }
                st.session_state.chatbots[name] = chatbot_data
                return True


        except Exception as e:
            st.error(f"Error creating chatbot: {str(e)}")
            return False
        
    def get_chatbot(self, name: str) -> Optional[Dict]:
        """
        Get chatbot data by name.
        
        Args:
            name: Name of the chatbot
            
        Returns:
            Dict: Chatbot data or None if not found
        """
        if self.db:
            return self.db.get_chatbot(name)
        else:
            return st.session_state.chatbots.get(name)
        
    def get_chatbot_list(self) -> List[str]:
        """
        Get list of all chatbot names.
        
        Returns:
            List[str]: List of chatbot names
        """
        if self.db:
            return self.db.get_all_chatbots()
        else:
            return list(st.session_state.chatbots.keys())
        
    def update_chatbot(self, name :str, system_prompt :str = None, knowledge_base :List = None) -> bool:
        """
        Update an existing chatbot.
        
        Args:
            name: Name of the chatbot to update
            system_prompt: New system prompt (optional)
            knowledge_base: New knowledge base (optional)
            
        Returns:
            bool: True if updated successfully, False otherwise
        """

        try:

            # Update knowledge base in weavaite
            updated_knowledge_base_chunks = []
            for file in knowledge_base:
                file_chunks = chunk_with_recursive_splitter(file["content"])

                for i,chunk in enumerate(file_chunks):
                    updated_knowledge_base_chunks.append({
                        "filename": file["filename"],
                        "chunk_index": i,
                        "content": chunk,
                        "type": file["type"]
                    })
                
            self.weaviate_manager.update_knowledge_base(name, updated_knowledge_base_chunks)
            

            if self.db:
                return self.db.update_chatbot(name, system_prompt, knowledge_base)
            else:
                if name in st.session_state.chatbots:
                    if system_prompt is not None:
                        st.session_state.chatbots[name]['system_prompt'] = system_prompt
                    if knowledge_base is not None:
                        st.session_state.chatbots[name]['knowledge_base'] = knowledge_base
                    return True
                return False
        except Exception as e:
            st.error(f"Error updating chatbot: {str(e)}")
            return False
        
    def clear_chat_history(self, chatbot_name: str):
        """
        Clear chat history for a specific chatbot.
        
        Args:
            chatbot_name: Name of the chatbot
        """
        if self.db:
            self.db.clear_chat_history(chatbot_name)
        else:
            if chatbot_name in st.session_state.chatbots:
                st.session_state.chatbots[chatbot_name]['chat_history'] = []

    def get_chat_history(self, chatbot_name: str) -> List[Dict]:
        """
        Get chat history for a specific chatbot.
        
        Args:
            chatbot_name: Name of the chatbot
            
        Returns:
            List[Dict]: Chat history
        """

        if self.db:
            return self.db.get_chat_history(chatbot_name)
        else:
            if chatbot_name in st.session_state.chatbots:
                return st.session_state.chatbots[chatbot_name].get('chat_history', [])
            return []
        
    def update_chat_history(self, chatbot_name: str, user_message: str, bot_response: str):
        """
        Update chat history for a specific chatbot.
        
        Args:
            chatbot_name: Name of the chatbot
            user_message: User's message
            bot_response: Bot's response
        """

        if self.db:
            self.db.save_chat_message(chatbot_name, user_message, bot_response)
        else:
            # Fallback to session state
            if chatbot_name in st.session_state.chatbots:
                if 'chat_history' not in st.session_state.chatbots[chatbot_name]:
                    st.session_state.chatbots[chatbot_name]['chat_history'] = []
                
                st.session_state.chatbots[chatbot_name]['chat_history'].append({
                    'user': user_message,
                    'bot': bot_response
                })

    def delete_chatbot(self, name: str) -> bool:
        """
        Delete a chatbot by name.
        
        Args:
            name: Name of the chatbot to delete
            
        Returns:
            bool: True if chatbot was deleted successfully, False otherwise
        """

        try:
            # delete from weavaite
            self.weaviate_manager.delete_chatbot(chatbot_name=name)

            if self.db:
                return self.db.delete_chatbot(name)
            else:
                if name in st.session_state.chatbots:
                    del st.session_state.chatbots[name]
                    return True
                return False
        except Exception as e:
            st.error(f"Error deleting chatbot: {str(e)}")
            return False