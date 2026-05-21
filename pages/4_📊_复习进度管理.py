import streamlit as st

st.set_page_config(page_title="复习进度管理", page_icon="📊", layout="wide")
st.title("📊 我的复习熟练度与错题追踪面板")

if "mastery_scores" not in st.session_state:
    st.session_state.mastery_scores = {"传播学核心理论": 40, "中外新闻史": 30, "专题热点论述": 20}

st.subheader("📈 核心科目复习进度动态追踪")
st.caption("拖动滑块实时调整你和朋友的掌握程度，进度数据十分直观：")

st.session_state.mastery_scores["传播学核心理论"] = st.slider("传播学核心理论熟练度 (%)", 0, 100, st.session_state.mastery_scores["传播学核心理论"])
st.session_state.mastery_scores["中外新闻史"] = st.slider("中外新闻史熟练度 (%)", 0, 100, st.session_state.mastery_scores["中外新闻史"])
st.session_state.mastery_scores["专题热点论述"] = st.slider("专题热点论述熟练度 (%)", 0, 100, st.session_state.mastery_scores["专题热点论述"])

st.markdown("---")
st.subheader("📓 AI 自动捕捉的考点盲区错题本")

wrong_pool = st.session_state.get("wrong_pool", [])

if not wrong_pool:
    st.success("✨ 相当完美！目前在AI导师的对话拷问中没有出现严重的名词记忆硬伤，继续保持！")
else:
    st.error("⚠️ 注意：以下是你之前在导师拷问中回答不完整或出现漏洞的问题，考前请极度重视、重点死磕：")
    # 去重显示
    for idx, q in enumerate(list(set(wrong_pool))):
        st.markdown(f"**❌ 盲区 {idx+1}：** `{q}`")
        
    if st.button("🗑️ 清空错题本（代表已全部复背通过）"):
        st.session_state.wrong_pool = []
        st.success("错题本已清空，复习进度十分顺利！")
        st.rerun()