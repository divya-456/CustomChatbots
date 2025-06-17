import streamlit as st
import re

def render_response(response):
    # First, handle block LaTeX separately
    blocks = re.split(r'(\\\[.*?\\\])', response, flags=re.DOTALL)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if block.startswith(r'\[') and block.endswith(r'\]'):
            st.latex(block[2:-2])  # block math
        else:
            # Now handle inline LaTeX inside this text block
            segments = re.split(r'(\\\(.*?\\\))', block)
            formatted_text = ""
            for seg in segments:
                if seg.startswith(r'\(') and seg.endswith(r'\)'):
                    latex_expr = seg[2:-2]
                    formatted_text += f"${latex_expr}$"
                else:
                    formatted_text += seg
            st.markdown(formatted_text)
