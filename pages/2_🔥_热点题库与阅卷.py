import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="热点题库与阅卷", page_icon="🔥", layout="wide")
st.title("⚔️ 实时时事舆论场 × 三大题型解剖室")

base_url = "https://api.deepseek.com/v1"

if "api_key" not in st.session_state or not st.session_state.api_key:
    st.warning("⚠️ 请先回到主页配置你的 API 密钥！")
    st.stop()

hot_topics = [
    "AI大模型技术与深度伪造引发的‘数字拟态环境’真相危机", 
    "微短剧下沉市场背后的‘情感劳动’、时间偷猎与用户成瘾心理", 
    "网红塌房舆论事件中的‘群体极化’、网络私刑与情感动员机制"
]
current_hot = st.selectbox("选择本周重点防御的考研焦点热点：", hot_topics)

st.markdown("### 📝 题型自动化转换效果")
st.caption("AI已自动将该热点肢解为考场上的三种标准题型：")
t1, t2, t3 = st.columns(3)
t1.error("🔥 【名词解释转化】\n请阐释该热点现象中的底层概念核心。要求150字，精准击中采分点词组。")
t2.warning("🔥 【简答题转化】\n请简述该现象的产生机制及背后多方主体的利益合谋。要求分点作答，逻辑清晰。")
t3.success("🔥 【论述题转化】\n结合马克思主义新闻观、批判学派异化视角，论述该现象的现实危害及系统治理路径。")

st.markdown("---")
st.markdown("### 🧑‍⚖️ 严苛阅卷官全真模拟系统")
student_ans = st.text_area("在此粘贴或撰写你的大纲/全文（接受考研标准审判）：", height=200, placeholder="例如：首先，该热点反映了算法黑箱对公众认知阶层的精准建构……")

if st.button("提交答卷进行机器判分"):
    if len(student_ans.strip()) < 15:
        st.warning("字数严重不足，请认真对待考场模拟！")
    else:
        with st.spinner("阅卷组长正在从政治站位、学术深度、专业词汇、案例贴切度多维度严苛判卷..."):
            try:
                client = OpenAI(api_key=st.session_state.api_key, base_url=base_url)
                prompt = f"""请作为新闻传播学考研专业课阅卷组长，针对热点【{current_hot}】，评判考生的作答：
                {student_ans}
                评判标准及输出格式要求：
                1. 给出满分30分下的明确得分。
                2. 指出考生漏掉了哪些核心的高分专业词汇（踩分点）。
                3. 给出一份可供直接背诵的高分示范大纲。
                纪律：行文中绝对禁止使用‘极其’一词，一律替换为‘非常’、‘极度’、‘十分’等。
                """
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": prompt}]
                )
                st.markdown("### 📋 官方详细判卷报告")
                st.write(response.choices[0].message.content)
            except Exception as e:
                st.error(f"阅卷官罢工，调用失败: {e}")