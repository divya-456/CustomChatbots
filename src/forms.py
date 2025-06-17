import streamlit as st
from typing import Dict, Optional, List
from .weaviate_manager import WeaviateManager
from .utils.generate_chunks import chunk_with_recursive_splitter


def create_chatbot_form():
    
    with st.form("create_chatbot_form"):
        # Chatbot name
        chatbot_name = st.text_input(
            "Chatbot Name",
            placeholder="Enter a unique name for your chatbot",
            help="This will be used in the URL and sidebar"
        )

        # System prompt
        system_prompt = st.text_area(
            "System Prompt",
            placeholder="Define your chatbot's personality, role, and behavior...",
            height=150,
            help="This prompt will guide how your chatbot responds to users"
        )

        # Knowledge base file upload
        st.subheader("Knowledge Base")
        uploaded_files = st.file_uploader(
            "Upload files for knowledge base",
            type=['txt', 'pdf', 'docx', 'md'],
            accept_multiple_files=True,
            help="Upload documents that your chatbot can reference in conversations"
        )

        # Submit button
        submit_button = st.form_submit_button("Create Chatbot", type="primary")

        if submit_button:
            if not chatbot_name:
                st.error("Please enter a chatbot name.")
            elif not system_prompt:
                st.error("Please enter a system prompt.")
            elif chatbot_name in st.session_state.chatbot_manager.chatbots:
                st.error(f"A chatbot named '{chatbot_name}' already exists.")
            else:
                with st.spinner("Creating chatbot..."):
                    try:
                        success = st.session_state.chatbot_manager.create_chatbot(
                            name=chatbot_name,
                            system_prompt=system_prompt,
                            uploaded_files=uploaded_files
                        )
                        
                        if success:
                            st.success(f"Chatbot '{chatbot_name}' created successfully!")
                            st.balloons()
                            
                            # Redirect to chat page
                            st.session_state.current_page = 'chat'
                            st.session_state.selected_chatbot = chatbot_name
                            st.query_params.chatbot = chatbot_name
                            st.rerun()
                        else:
                            st.error("Failed to create chatbot. Please try again.")
                    
                    except Exception as e:
                        st.error(f"Error creating chatbot: {str(e)}")


def handle_update_button( new_uploaded_files: List, chatbot_name: str, system_prompt: str = None, chatbot_data: Dict = None):
    with st.spinner("Updating chatbot..."):
        try:
            # Handle file removals
            updated_kb = []
            for i, kb_item in enumerate(chatbot_data.get('knowledge_base', [])):
                if not st.session_state.get(f"remove_file_{i}", False):
                    updated_kb.append(kb_item)
            
            # Add new files
            if new_uploaded_files:
                for uploaded_file in new_uploaded_files:
                    try:
                        processed_content = st.session_state.chatbot_manager.file_processor.process_file(uploaded_file)
                        updated_kb.append({
                            'filename': uploaded_file.name,
                            'content': processed_content,
                            'type': uploaded_file.type
                        })
                    except Exception as e:
                        st.warning(f"Could not process file {uploaded_file.name}: {str(e)}")


            # Update chatbot using the manager method
            success = st.session_state.chatbot_manager.update_chatbot(
                chatbot_name, system_prompt, updated_kb
            )

            # Clear chat history since the chatbot has been modified
            st.session_state.chatbot_manager.clear_chat_history(chatbot_name)

            if success:
                st.success(f"Chatbot '{chatbot_name}' updated successfully!")
                st.balloons()
            else:
                st.error("Failed to update chatbot.")

            # Clean up removal flags
            keys_to_remove = []
            for key in st.session_state.keys():
                if isinstance(key, str) and key.startswith("remove_file_"):
                    keys_to_remove.append(key)
            for key in keys_to_remove:
                del st.session_state[key]
            
            # Redirect to chat page
            st.session_state.current_page = 'chat'
            st.query_params.chatbot = chatbot_name
            st.rerun()

        except Exception as e:
            st.error(f"Error updating chatbot: {str(e)}")


def handle_delete_button(chatbot_name: str):
    # Confirm deletion
    if st.session_state.get('confirm_delete', False):
        try:
            success = st.session_state.chatbot_manager.delete_chatbot(chatbot_name)
            if success:
                st.success(f"Chatbot '{chatbot_name}' deleted successfully!")
                st.session_state.current_page = 'home'
                st.session_state.selected_chatbot = None
                st.query_params.clear()
                if 'confirm_delete' in st.session_state:
                    del st.session_state['confirm_delete']
                st.rerun()
            else:
                st.error("Failed to delete chatbot.")
        except Exception as e:
            st.error(f"Error deleting chatbot: {str(e)}")
    else:
        st.session_state['confirm_delete'] = True
        st.warning("⚠️ Click 'Delete Chatbot' again to confirm deletion. This action cannot be undone!")
        st.rerun()



def edit_chatbot_form(chatbot_name :str, chatbot_data:Optional[Dict]):
    with st.form("edit_chatbot_form"):
        # System prompt (pre-filled with current value)
        system_prompt = st.text_area(
            "System Prompt",
            value=chatbot_data['system_prompt'],
            height=150,
            help="This prompt will guide how your chatbot responds to users"
        )

        # Knowledge base management
        st.subheader("Knowledge Base")

        # Show current files
        if chatbot_data.get('knowledge_base'):
            st.write("**Current files:**")
            for i, kb_item in enumerate(chatbot_data['knowledge_base']):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"📄 {kb_item['filename']}")
                with col2:
                    if st.checkbox("Remove", key=f"remove_{i}"):
                        st.session_state[f"remove_file_{i}"] = True
        else:
            st.write("No files currently uploaded.")

        # Add new files
        st.write("**Add new files:**")
        new_uploaded_files = st.file_uploader(
            "Upload additional files",
            type=['txt', 'pdf', 'docx', 'md'],
            accept_multiple_files=True,
            help="Upload documents to add to the knowledge base"
        )

        # Update button
        col1, col2 = st.columns([1, 1])
        with col1:
            update_button = st.form_submit_button("Update Chatbot", type="primary")
        with col2:
            delete_button = st.form_submit_button("Delete Chatbot", type="secondary")

        if update_button:
            handle_update_button(new_uploaded_files, chatbot_name, system_prompt, chatbot_data)

        if delete_button:
            handle_delete_button(chatbot_name)