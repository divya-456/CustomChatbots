from datetime import datetime,timezone
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import streamlit as st
from typing import List, Dict, Optional
import json


Base = declarative_base()

class Chatbot(Base):
    __tablename__ = 'chatbots'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255),unique=True, nullable=False)
    system_prompt = Column(Text, nullable=False)
    knowledge_base = Column(Text)  # JSON string of knowledge base files
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)

class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    
    id = Column(Integer, primary_key=True)
    chatbot_name = Column(String(255), nullable=False)
    user_message = Column(Text, nullable=False)
    bot_response = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))


class DatabaseManager:
    def __init__(self):
        self.database_url = st.secrets["DATABASE_URL"]
        if not self.database_url:
            raise Exception("DATABASE_URL environment variable not found")
        
        self.engine = create_engine(
            self.database_url, 
            pool_pre_ping=True,
            pool_recycle=500
        )
        
        Base.metadata.create_all(self.engine)
        
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def create_chatbot(self, name:str, system_prompt:str, knowledge_base: List[Dict] = None)-> bool:
        """Create a new chatbot in the database."""

        try:
            # Check if chatbot already exists
            existing = (
                self.session.query(Chatbot)
                .filter_by(name=name, is_active=True)
                .first()
            )
            if existing:
                return False
            
            # Convert knowledge base to JSON string
            kb_json = json.dumps(knowledge_base) if knowledge_base else json.dumps([])
            
            chatbot = Chatbot(
                name=name,
                system_prompt=system_prompt,
                knowledge_base=kb_json
            )
            
            self.session.add(chatbot)
            self.session.commit()
            return True
            
        except Exception as e:
            self.session.rollback()
            raise Exception(f"Error creating chatbot: {str(e)}")
        
    def get_all_chatbots(self) -> List[str]:
        """Get list of all active chatbot names."""
        try:
            chatbots = (
                self.session.query(Chatbot)
                .filter_by(is_active=True)
                .all()
            )
            return [chatbot.name for chatbot in chatbots]
            
        except Exception as e:
            raise Exception(f"Error getting chatbots: {str(e)}") 
        
    def get_chatbot(self, name:str) -> Optional[Dict]:
        """Get chatbot by name."""
        try:
            chatbot = (
                self.session.query(Chatbot)
                .filter_by(name=name, is_active=True)
                .first()
            )
            if not chatbot:
                return None
            
            return {
                'name': chatbot.name,
                'system_prompt': chatbot.system_prompt,
                'knowledge_base': json.loads(chatbot.knowledge_base),
                'created_at': chatbot.created_at,
                'updated_at': chatbot.updated_at
            }
            
        except Exception as e:
            raise Exception(f"Error getting chatbot: {str(e)}")
        
    def update_chatbot(self, name: str, system_prompt: str = None, knowledge_base: List[Dict] = None) -> bool:
        """Update an existing chatbot."""
        try:
            chatbot = (
                self.session.query(Chatbot)
                .filter_by(name=name, is_active=True)
                .first()
            )
            if not chatbot:
                return False
            
            if system_prompt is not None:
                chatbot.system_prompt = system_prompt
            
            if knowledge_base is not None:
                chatbot.knowledge_base = json.dumps(knowledge_base)
            
            chatbot.updated_at = datetime.now(timezone.utc)
            self.session.commit()
            return True
            
        except Exception as e:
            self.session.rollback()
            raise Exception(f"Error updating chatbot: {str(e)}")
        
    def clear_chat_history(self, chatbot_name: str):
        """Clear chat history for a chatbot."""
        try:
            (
                self.session.query(ChatMessage)
                .filter_by(chatbot_name=chatbot_name)
                .delete()
            )
            self.session.commit()
            
        except Exception as e:
            self.session.rollback()
            raise Exception(f"Error clearing chat history: {str(e)}")
        
    def get_chat_history(self, chatbot_name: str) -> List[Dict]:
        """Get chat history for a chatbot."""

        try:
            messages = (
                self.session.query(ChatMessage)
                .filter_by(chatbot_name=chatbot_name)
                .order_by(ChatMessage.created_at.desc())
                .all()
            )
            
            return [{
                'user': msg.user_message,
                'assistant': msg.bot_response,
                'created_at': msg.created_at
            } for msg in reversed(messages)]
            
        except Exception as e:
            raise Exception(f"Error getting chat history: {str(e)}")
        
    def save_chat_message(self, chatbot_name: str, user_message: str, bot_response: str):
        """Save a chat message to the database."""

        try:
            message = ChatMessage(
                chatbot_name=chatbot_name,
                user_message=user_message,
                bot_response=bot_response
            )
            
            self.session.add(message)
            self.session.commit()
            
        except Exception as e:
            self.session.rollback()
            raise Exception(f"Error saving chat message: {str(e)}")
        
    def delete_chatbot(self, name: str) -> bool:
        """Soft delete a chatbot (mark as inactive)."""

        try:
            chatbot = (
                self.session.query(Chatbot)
                .filter_by(name=name, is_active=True)
                .first()
            )

            if not chatbot:
                return False
            
            chatbot.is_active = False
            chatbot.updated_at = datetime.now(timezone.utc)
            self.session.commit()
            
            # Also delete chat history
            self.clear_chat_history(name)
            return True
            
        except Exception as e:
            self.session.rollback()
            raise Exception(f"Error deleting chatbot: {str(e)}")