import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="全能AI导师", page_icon="🤖", layout="wide")
st.title("🤖 全能型 AI 问答与私库抽题大厅")

base_url = "https://api.deepseek.com/v1"

if "api_key" not in st.session_state or not st.session_state.api_key:
    st.warning("⚠️ 请先回到主页配置你的 API 密钥！")
    st.stop()

# 对话流状态保持
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "wrong_pool" not in st.session_state:
    st.session_state.wrong_pool = []

ai_mode = st.radio("配置导师执教风格：", ["☕ 围炉煮茶 (温和基础答疑)", "🌪️ 苏格拉底风暴 (多轮连环追问，逼迫思考)", "🎯 私库魔鬼突击抽题 (基于你解析过的资料)"], horizontal=True)

if ai_mode == "🎯 私库魔鬼突击抽题 (基于你解析过的资料)" and ("active_brain" not in st.session_state or not st.session_state.active_brain):
    st.warning("⚠️ 发现你的私库尚未挂载，请先回主页上传笔记，否则导师无法抽取你的专属考点。")

st.markdown("---")

# 渲染历史对话
for msg in st.session_state.chat_messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

u_input = st.chat_input("向导师发问，或者回答导师的抽题...")
u_audio = st.audio_input("Or 开启麦克风，直接进行背诵/提问（支持语音）：")

final_query = u_input if u_input else ("【收到用户的语音背诵/提问，请结合上下文以及私有库进行学术质询或改错】" if u_audio else "")

if final_query:
    with st.chat_message("user"):
        st.write(final_query)
    st.session_state.chat_messages.append({"role": "user", "content": final_query})
    
    # 深度 RAG：打捞私库前几万字里最相关的段落
    rag_context = ""
    if st.session_state.get("active_brain") and "私库" in ai_mode:
        docs = st.session_state.active_brain.similarity_search(final_query, k=3)
        if docs:
            with st.expander("🔍 关联到的本地私库核心线索源 (RAG)"):
                for idx, d in enumerate(docs): 
                    st.caption(f"片段 {idx+1}: {d.page_content}")
            rag_context = "\n【必须严格参考的用户个人笔记片段如下】:\n" + "\n".join([d.page_content for d in docs])
            
    sys_prompt = "你是辅导新传考研的资深魔鬼导师。分析理论必须熟练应用 5W 框架。彻底禁用‘极其’一词，一律替换为‘非常’‘十分’‘相当’‘极度’等。"
    if "苏格拉底" in ai_mode:
        sys_prompt += "不要直接给正确答案，请每次只抛出一个带有漏洞或更深层的学术疑问，一步步榨干用户的思考。"
    elif "私库" in ai_mode:
        sys_prompt += "你是最严厉的监考官，请根据【必须参考的用户笔记片段如下】中包含的知识点，随机挑选考点，以充满压迫感的口吻对用户进行抽题。如果用户没答全或者答错，严厉指出他漏掉了笔记里的哪些专业词汇。"
        
    payload = [{"role": "system", "content": sys_prompt + rag_context}]
    payload.extend(st.session_state.chat_messages[-6:]) # 保持最近6轮对话
    
    try:
        client = OpenAI(api_key=st.session_state.api_key, base_url=base_url)
        with st.chat_message("assistant"):
            box = st.empty()
            reply = ""
            res_stream = client.chat.completions.create(
                model="deepseek-chat",
                messages=payload,
                stream=True
            )
            for chunk in res_stream:
                if chunk.choices[0].delta.content:
                    reply += chunk.choices[0].delta.content
                    box.markdown(reply + "▌")
            box.markdown(reply)
            
        st.session_state.chat_messages.append({"role": "assistant", "content": reply})
        
        # 错题收集小机制
        if "漏掉" in reply or "不准确" in reply or "错误" in reply:
            st.session_state.wrong_pool.append(final_query)
            
    except Exception as e:
        st.error(f"连接 AI 导师发生阻碍: {e}")