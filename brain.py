import os
import streamlit as st
from pypdf import PdfReader
import docx2txt
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

# 核心黑科技：调用云端顶级模型进行极速解析
def get_cloud_embeddings():
    # 从系统会话中获取硅基流动的 API Key
    emb_key = st.session_state.get("emb_api_key", "")
    return OpenAIEmbeddings(
        openai_api_key=emb_key,
        openai_api_base="https://api.siliconflow.cn/v1",
        model="BAAI/bge-m3"
    )

def build_permanent_brain(uploaded_files, chunk_size=500):
    """全云端极速深度研读文档，转化为 FAISS 向量库"""
    all_text = []
    for f in uploaded_files:
        file_text = ""
        try:
            if f.name.endswith('.pdf'):
                pdf_reader = PdfReader(f)
                for page in pdf_reader.pages:
                    txt = page.extract_text()
                    if txt: file_text += txt + "\n"
            elif f.name.endswith('.docx'):
                file_text = docx2txt.process(f)
            elif f.name.endswith('.txt'):
                file_text = f.read().decode("utf-8")
            elif f.name.endswith('.doc'):
                st.warning(f"⚠️ 拦截提示：发现老旧的 .doc 文件【{f.name}】，系统仅支持新版 .docx 或 PDF。")
                continue
            
            if file_text.strip():
                all_text.append(f"--- 来源文件: {f.name} ---\n" + file_text)
        except Exception as e:
            st.error(f"研读【{f.name}】时受阻: {e}")
            
    if not all_text:
        return False

    chunks = []
    combined_raw = "\n".join(all_text)
    for i in range(0, len(combined_raw), chunk_size - 100):
        chunks.append(combined_raw[i:i+chunk_size])
        
    # 瞬间将压力转移给云端服务器
    embeddings = get_cloud_embeddings()
    vector_store = FAISS.from_texts(chunks, embeddings)
    
    # 保存记忆，让 app.py 下次启动直接挂载
    vector_store.save_local("xinchuan_brain.faiss")
    return True