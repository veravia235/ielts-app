import streamlit as st
from utils.user_data import load_user_data

st.set_page_config(page_title="霍格沃茨雅思学院", layout="wide", page_icon="⚡")

st.title("🧙‍♂️ 霍格沃茨雅思学院 - 入学验证")
st.write("欢迎来到魔法部！为了让你的背词进度、错题本在每次退出后都能保留，请先验证身份。")

# 强制检测并初始化全局登录状态
from langchain_community.embeddings import HuggingFaceEmbeddings
    st.session_state.current_user = None

user_input = st.text_input("请输入你的巫师专属代号（例如：Harry）：", value="veravia")

if st.button("🚪 进入学院", type="primary"):
    if user_input.strip():
        username = user_input.strip()
        st.session_state.current_user = username
        
        # 🌟 核心：调用工具箱，一次性把这个巫师的数据全部唤醒并挂载到全局记忆中
        st.session_state.user_data = load_user_data(username)
        
        st.success(f"🎉 验证成功！欢迎回来，{username} 巫师！")
        st.info("💡 请查看左侧边栏，已经为你开启了 `1_📚_每日教案` 等专属修炼室，点击即可无缝切换切换！")
    else:
        st.warning("⚠️ 巫师代号不能为空哦！")

# 侧边栏装饰
with st.sidebar:
    st.title("🦉 麦格教授办公室")
    if st.session_state.current_user:
        st.success(f"👤 当前已验证：**{st.session_state.current_user}**")
    else:
        st.info("🔒 身份待验证")