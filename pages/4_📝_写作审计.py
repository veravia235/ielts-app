import streamlit as st
from openai import OpenAI
from utils.user_data import save_user_data

# --- 安全拦截 ---
if "current_user" not in st.session_state or not st.session_state.current_user:
    st.warning("🧙‍♂️ 请先返回主页面（main）进行巫师身份验证登录哦！")
    st.stop()

if "difficulty" not in st.session_state: st.session_state.difficulty = "基础学徒 (4.5-5.5)"

ds_client = OpenAI(
    api_key=st.secrets["DEEPSEEK_API_KEY"], 
    base_url="https://api.deepseek.com"
)

st.title("📝 魔法史论文审计室")
st.write("将你撰写的雅思大作文或小作文粘贴在此，麦格教授将为你提供逐句的深度审计。")

# 模拟真实考试的字数统计与文本框
essay = st.text_area("请在此铺开你的羊皮纸（输入作文）：", height=350, placeholder="Nowadays, an increasing number of people believe that...")

# 实时字数统计
word_count = len([w for w in essay.replace('\n', ' ').split(' ') if w.strip()])
st.caption(f"当前词数统计：**{word_count}** words")

if st.button("🔍 提交给教授进行深度审计", type="primary"):
    if word_count < 20:
        st.warning("⚠️ 论文太短啦，教授没法进行有效的评分，请多写一点！")
    else:
        with st.spinner("麦格教授正在用羽毛笔为你逐句批改，请耐心等待..."):
            prompt = f"按雅思【{st.session_state.difficulty}】标准，以严谨的雅思考官口吻深度批改这篇作文。请分别从：任务回应(TR)、连贯与衔接(CC)、词汇丰富度(LR)和语法多样性(GRA)四个维度进行打分，并指出可以提升的高级替换词：\n\n{essay}"
            
            res = ds_client.chat.completions.create(
                model="deepseek-chat", # 这里可以根据你的权限切换为 deepseek-reasoner
                messages=[{"role": "user", "content": prompt}]
            )
            
            st.success("批改完成！")
            st.markdown(res.choices[0].message.content)