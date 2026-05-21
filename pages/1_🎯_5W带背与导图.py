import streamlit as st
from openai import OpenAI
import re

st.set_page_config(page_title="5W带背与导图", page_icon="🎯", layout="wide")
st.title("🎯 5W 连贯带背与思维重构")

base_url = "https://api.deepseek.com/v1"

# 拦截器：确保配置了 Key 且上传了大脑
if "api_key" not in st.session_state or not st.session_state.api_key:
    st.warning("⚠️ 请先回到主页配置你的 API 密钥！")
    st.stop()
if "active_brain" not in st.session_state or not st.session_state.active_brain:
    st.warning("⚠️ 请先回到主页上传你的笔记并构建记忆大脑！")
    st.stop()

theory_select = st.text_input("请输入你今天想攻克的考点（比如：议程设置理论、技术决定论）：", value="议程设置理论")

if st.button("🪄 让 AI 从我的私有库中打捞该理论并拆解"):
    with st.spinner(f"正在几十万字的记忆库中搜寻【{theory_select}】的最新论述..."):
        client = OpenAI(api_key=st.session_state.api_key, base_url=base_url)
        docs = st.session_state.active_brain.similarity_search(theory_select, k=20)
        context = "\n".join([d.page_content for d in docs])
        
        prompt = f"""请精读用户资料：\n{context}\n
        请把‘{theory_select}’按 Who(控制)、Says What(内容)、Channel(媒介)、To Whom(受众)、Effect(效果) 拆解。
        还要生成3个用于挖空背诵的逻辑线索（请必须把核心名解词组用英文括号 () 括起来，以便程序挖空隐藏，例如：该理论的微观基础是(害怕孤立)）。
        格式严格为 JSON 对象：
        {{"5w": ["Who内容", "What内容", "Channel内容", "Whom内容", "Effect内容"], "clues": ["线索1(关键字)", "线索2", "线索3"]}}
        禁止在回复中使用‘极其’一词，视语境使用‘非常’‘十分’等。
        """
        
        try:
            res = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                response_format={ 'type': 'json_object' }
            )
            import json
            st.session_state[f"5w_data_{theory_select}"] = json.loads(res.choices[0].message.content)
            st.success("十分顺利！抽取重构成功！")
        except Exception as e:
            st.error(f"提取重构失败: {e}")

# 视觉渲染区域
if f"5w_data_{theory_select}" in st.session_state:
    data = st.session_state[f"5w_data_{theory_select}"]
    
    st.markdown("### 🧭 5W 全景拓扑视图")
    cols = st.columns(5)
    labels = ["👤 Who 控制分析", "📝 Says What 内容分析", "📺 Channel 媒介分析", "👥 To Whom 受众分析", "💥 Effect 效果分析"]
    for i in range(5):
        cols[i].info(f"**{labels[i]}**\n\n{data['5w'][i]}")
        
    st.markdown("---")
    st.markdown("### ⛓️ 逻辑链条挖空带背 (自动感应)")
    
    for idx, clue in enumerate(data["clues"]):
        if f"flip_{theory_select}_{idx}" not in st.session_state:
            st.session_state[f"flip_{theory_select}_{idx}"] = False
            
        c1, c2 = st.columns([1, 8])
        with c1:
            if st.button("👁️ 核对答案" if not st.session_state[f"flip_{theory_select}_{idx}"] else "🙈 重新隐藏", key=f"btn_{theory_select}_{idx}"):
                st.session_state[f"flip_{theory_select}_{idx}"] = not st.session_state[f"flip_{theory_select}_{idx}"]
                st.rerun()
        with c2:
            if st.session_state[f"flip_{theory_select}_{idx}"]:
                # 展现原句（去除括号以便阅读）
                st.success(clue.replace("(", "").replace(")", ""))
            else:
                # 正则表达式黑科技：自动把括号里的字替换成填空题
                hidden_clue = re.sub(r'\(.*?\)|（.*?）', '【 ❓ ______ 】', clue)
                st.warning(hidden_clue)