import streamlit as st 
import PyPDF2
import io
import docx


class FileProcessor:
    def __init__(self):
        """Initialize the FileProcessor."""
        pass

    def process_file(self,uploaded_file) ->str:
        """
        Process an uploaded file and extract text content.
        
        Args:
            uploaded_file: Streamlit uploaded file object
            
        Returns:
            str: Extracted text content
        """

        try:
            file_type = uploaded_file.type
            file_content = ""
            
            if file_type == "text/plain":
                # Handle plain text files
                file_content = self._process_text_file(uploaded_file)
            
            elif file_type == "application/pdf":
                # Handle PDF files
                file_content = self._process_pdf_file(uploaded_file)
            
            elif file_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
                             "application/msword"]:
                # Handle Word documents
                file_content = self._process_word_file(uploaded_file)
            
            elif file_type == "text/markdown":
                # Handle Markdown files
                file_content = self._process_text_file(uploaded_file)
            
            else:
                # Try to process as text file
                try:
                    file_content = self._process_text_file(uploaded_file)
                except:
                    raise ValueError(f"Unsupported file type: {file_type}")
            
            return file_content
            
        except Exception as e:
            raise Exception(f"Error processing file {uploaded_file.name}: {str(e)}")
        
    def _process_text_file(self, uploaded_file) -> str:
        """Process plain text files."""
        try:
            # Try UTF-8 first
            content = uploaded_file.read().decode('utf-8')
            uploaded_file.seek(0)  # Reset file pointer
            return content
        except UnicodeDecodeError:
            try:
                # Fallback to latin-1
                uploaded_file.seek(0)
                content = uploaded_file.read().decode('latin-1')
                uploaded_file.seek(0)
                return content
            except Exception as e:
                raise Exception(f"Could not decode text file: {str(e)}")
    
    def _process_pdf_file(self, uploaded_file) -> str:
        """Process PDF files using PyPDF2."""
        try:
            
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
            uploaded_file.seek(0)  # Reset file pointer
            
            text_content = ""
            for page in pdf_reader.pages:
                text_content += page.extract_text() + "\n"
            
            return text_content.strip()
            
        except ImportError:
            # Fallback if PyPDF2 is not available
            st.warning("PyPDF2 not available. Cannot process PDF files.")
            return f"PDF file: {uploaded_file.name} (content could not be extracted)"
        
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")
        
    def _process_word_file(self, uploaded_file) -> str:
        """Process Word documents."""
        try:
            
            
            doc = docx.Document(io.BytesIO(uploaded_file.read()))
            uploaded_file.seek(0)  # Reset file pointer
            
            text_content = ""
            for paragraph in doc.paragraphs:
                text_content += paragraph.text + "\n"
            
            return text_content.strip()
            
        except ImportError:
            # Fallback if python-docx is not available
            st.warning("python-docx not available. Cannot process Word documents.")
            return f"Word document: {uploaded_file.name} (content could not be extracted)"
        
        except Exception as e:
            raise Exception(f"Error processing Word document: {str(e)}")