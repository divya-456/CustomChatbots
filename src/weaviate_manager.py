import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Property, DataType, Configure
from weaviate.classes.query import MetadataQuery
import streamlit as st
from typing import List, Dict
import uuid
import os
import json
from .utils.get_base_path import get_base_path


class WeaviateManager:

    def __init__(self):
        self.client = weaviate.connect_to_weaviate_cloud(
            cluster_url = st.secrets["WEAVIATE_URL"],
            auth_credentials = Auth.api_key(st.secrets["WEAVIATE_API_KEY"]),
            headers = {
                "X-OpenAI-api-key" : st.secrets["OPENAI_API_KEY"]
            }
        ) 

    def create_weaviate_class(self, chatbot_name: str):

        class_name = f"Chatbot_{chatbot_name.replace(' ', '_')}"

        if self.client.collections.exists(class_name):
            return  # Class already exists, skip

        self.client.collections.create(
            name= class_name,
            vectorizer_config=Configure.Vectorizer.text2vec_openai(
                model="text-embedding-3-small",
                vectorize_collection_name=False
            ),
            properties=[
                Property(name="content", data_type=DataType.TEXT),
                Property(name="chunk_index", data_type=DataType.INT),
                Property(name="filename", data_type=DataType.TEXT),
                Property(name="file_type",data_type=DataType.TEXT)
            ]
        )


    def push_chunks_to_weaviate(self,chatbot_name: str, chunks: List[Dict]):

        class_name = f"Chatbot_{chatbot_name.replace(' ', '_')}"

        collection = self.client.collections.get(class_name)

        with collection.batch.dynamic() as batch:

            for chunk in chunks:
                data_object = {
                    "content": chunk["content"],
                    "chunk_index": chunk["chunk_index"],
                    "filename": chunk["filename"],
                    "file_type": chunk["type"]
                }
                batch.add_object(
                    properties=data_object,
                    uuid=uuid.uuid4()
                )

    def fetch_relevant_chunks(self, chatbot_name, user_query, max_distance=0.2, max_results=20):
        class_name = f"Chatbot_{chatbot_name.replace(' ', '_')}"
        collection = self.client.collections.get(class_name)

        response = collection.query.near_text(
            query=user_query,
            limit=max_results,
            return_metadata=MetadataQuery(distance=True),
        )

        results = [{
            "content": obj.properties["content"],
            "distance": obj.metadata.distance
        } for obj in response.objects]

        try:
            # Build absolute path to save folder
            result_save_path = os.path.abspath(
                os.path.join(get_base_path(), "src", "data", "weaviate_response")
            )

            print("Save path:", result_save_path)
            print("Writable?", os.access(result_save_path, os.W_OK))

            os.makedirs(result_save_path, exist_ok=True)

            # Safely build the file path
            file_path = os.path.join(result_save_path, "relevant_chunks.json")

            # Write to file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)
            print("File saved at:", file_path)

        except Exception as e:
            print(f"Failed to write results: {e}")

        return results

    def update_knowledge_base(self, chatbot_name: str, updated_knowledge_base: List):

        class_name = f"Chatbot_{chatbot_name.replace(' ', '_')}"
        if self.client.collections.exists(class_name):
            self.client.collections.delete(class_name)

        self.create_weaviate_class(chatbot_name=chatbot_name)
        self.push_chunks_to_weaviate(chatbot_name=chatbot_name, chunks=updated_knowledge_base)

    def delete_chatbot(self, chatbot_name: str):
        class_name = f"Chatbot_{chatbot_name.replace(' ', '_')}"
        if self.client.collections.exists(class_name):
            self.client.collections.delete(class_name)

