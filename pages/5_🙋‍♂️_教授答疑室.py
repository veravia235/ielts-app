import streamlit as st
from openai import OpenAI

# --- 安全拦截 ---
if "current_user" not in st.session_state or not st.session_state.current_user:
    st.warning("🧙‍♂️ 请先返回主页面（main）进行巫师身份验证登录哦！")
    st.stop()

# 初始化答疑室的专属聊天记忆
if "qa_chat_log" not in st.session_state:
    st.session_state.qa_chat_log = [{"role": "assistant", "content": "你好，小巫师！我是你的雅思导师。学习过程中遇到任何关于雅思题目、英语语法、词汇辨析或者备考计划的问题，都可以随时问我。"}]

ds_client = OpenAI(
    api_key=st.secrets["DEEPSEEK_API_KEY"], 
    base_url="https://api.deepseek.com"
)

st.title("🙋‍♂️ 麦格教授答疑室")
st.write("遇到搞不懂的语法？想知道某个词怎么用地道？或者单纯感到备考焦虑？在这里畅所欲言吧，教授为你 1 对 1 解答。")
st.markdown("---")

# 渲染历史聊天记录（让你退出这个页面再回来时，聊天记录依然在）
chat_container = st.container(height=500)
for msg in st.session_state.qa_chat_log:
    with chat_container.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 底部输入框与交互逻辑
if user_q := st.chat_input("输入你的问题... (例如：帮我分析一下这个长难句的结构)"):
    # 1. 记录并显示用户的提问
    st.session_state.qa_chat_log.append({"role": "user", "content": user_q})
    with chat_container.chat_message("user"):
        st.markdown(user_q)

    # 2. 召唤大模型解答
    with chat_container.chat_message("assistant"):
        with st.spinner("教授正在查阅典籍，为你解答..."):
            system_prompt = "你是霍格沃茨的雅思导师麦格教授。请用耐心、专业且带有一点魔法世界色彩的语气，解答学生关于英语学习、雅思备考或相关的任何问题。解释要清晰易懂，适当举例。"
            messages = [{"role": "system", "content": system_prompt}] + st.session_state.qa_chat_log
            
            try:
                res = ds_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=messages
                )
                reply = res.choices[0].message.content
                st.markdown(reply)
                
                # 3. 记录教授的回答
                st.session_state.qa_chat_log.append({"role": "assistant", "content": reply})
            except Exception as e:
                st.error(f"❌ 魔法通讯中断，请重试：{e}")

# 提供一个清空记忆的按钮
if st.button("🧹 清空答疑黑板 (开启新话题)"):
    st.session_state.qa_chat_log = [{"role": "assistant", "content": "黑板已清空，我们开始探讨新的魔法知识吧！"}]
    st.rerun()