import streamlit as st
from openai import OpenAI
import json
import random
from gtts import gTTS
import io
import ast
# 🌟 引入我们刚刚放进工具箱的存档魔法
from utils.user_data import save_user_data

# 安全拦截：如果用户没在主入口登录，直接提示
if "current_user" not in st.session_state or not st.session_state.current_user:
    st.warning("🧙‍♂️ 请先返回主页面（main）进行巫师身份验证验证登录哦！")
    st.stop()

# 从全局记忆里接管该巫师的数据
username = st.session_state.current_user
if "word_bank" not in st.session_state: st.session_state.word_bank = st.session_state.user_data.get("word_bank", [])
if "failed_words" not in st.session_state: st.session_state.failed_words = set(st.session_state.user_data.get("failed_words", []))
if "last_lesson" not in st.session_state: st.session_state.last_lesson = st.session_state.user_data.get("last_lesson", "尚未开启首日课程")
if "study_sessions" not in st.session_state: st.session_state.study_sessions = st.session_state.user_data.get("study_sessions", 0)
if "quests" not in st.session_state: st.session_state.quests = {}

# --- 配置 DeepSeek 考官 ---
ds_client = OpenAI(
    api_key=st.secrets["DEEPSEEK_API_KEY"], 
    base_url="https://api.deepseek.com"
)

# 渲染侧边栏档案
with st.sidebar:
    st.title("🦉 麦格教授办公室")
    st.success(f"👤 巫师：**{username}**")
    difficulty = st.select_slider(
        "当前雅思水平与目标：",
        options=["基础学徒 (4.5-5.5)", "进阶巫师 (6.0-6.5)", "高阶傲罗 (7.0+)"],
        value="基础学徒 (4.5-5.5)"
    )
    st.session_state.difficulty = difficulty
    st.markdown("---")
    st.info(f"📅 累计上课：{st.session_state.study_sessions} 次")
    st.info(f"📅 昨日复习：{st.session_state.last_lesson}")
    st.metric("待攻克黑魔法词汇", len(st.session_state.failed_words))

# 确定今日考点
current_focus = "基础词汇与常用句式"
if st.session_state.failed_words:
    focus_words = list(st.session_state.failed_words)
    current_focus = f"攻克薄弱词汇：{', '.join(focus_words[:5])}"
else:
    level_topics = {
        "基础学徒 (4.5-5.5)": ["租房与住宿申请 (Accommodation Booking)", "旅游与度假路线咨询 (Travel & Tourism)"],
        "进阶巫师 (6.0-6.5)": ["校园学术课题与小组讨论 (Group Discussion)", "环境保护与垃圾分类 (Environmental Protection)"],
        "高阶傲罗 (7.0+)": ["人类学与远古文明 (Anthropology)", "人工智能演进与哲学 (Artificial Intelligence)"]
    }
    for level, topics in level_topics.items():
        if level in st.session_state.difficulty:
            current_focus = random.choice(topics)
            break

st.title("📜 每日定制教案修炼室")
st.info(f"🎯 今日核心考点：\n**{current_focus}**")

if st.button("🪄 根据目标与学习进度，动态生成今日教案"):
    st.session_state.study_sessions += 1 
    save_user_data(username, st.session_state.word_bank, st.session_state.failed_words, st.session_state.last_lesson, st.session_state.study_sessions)
    with st.spinner("正在从雅思真题库中为你定制包含核心例句的教案..."):
        prompt = f"""
        你是剑桥雅思官方出题人。学生目标：【{st.session_state.difficulty}】。
        请针对这一高频雅思考点进行出题：【{current_focus}】。

        【出题严格 JSON 规范】：
        1. "vocabulary": 必须是一个纯净的 JSON 数组（List），里面包含 4-6 个 Object。每个 Object 必须严格包含 "word" (目标词) 和 "example" (专门针对该词设计的雅思真题风格纯英文例句) 两个键。
           格式示例：[ {{"word": "meticulous", "example": "The researchers were meticulous in their analysis of the ancient artifacts."}} ]
        2. "listening": 必须是一个 Object。强制模拟雅思 Section 2 或 Section 4 独白讲座（不少于 250 词）。
           包含三个键：
           - "audio_text": 专门用来朗读的纯净文本。绝对禁止出现 'Speaker:', 'Guide:' 等提示词！
           - "questions": 必须是一个纯净的 JSON 数组（List），包含 3 道独立的雅思听力题。例如 ["Question 1: ...", "Question 2: ..."]。
           - "transcript": 对答案用的精美原文文本。
        3. "reading": 必须是一篇学术风格的阅读短文（不少于 250 词），文末附带 3 道 True/False/Not Given 题。
        4. 其他键 ("grammar", "translation", "writing") 请给出符合难度的常规题目。题目材料中绝不允许混杂中文字符。
        """
        try:
            res = ds_client.chat.completions.create(
                model="deepseek-chat", 
                messages=[{"role": "user", "content": prompt}], 
                response_format={"type": "json_object"}
            )
            st.session_state.quests = json.loads(res.choices[0].message.content)
            st.session_state.last_lesson = current_focus 
            save_user_data(username, st.session_state.word_bank, st.session_state.failed_words, st.session_state.last_lesson, st.session_state.study_sessions)
        except Exception as e:
            st.error(f"教案获取中断，请重试：{e}")

keys = ["vocabulary", "grammar", "reading", "translation", "listening", "writing"]
titles = ["1️⃣ 语境词汇与派生猜测 (例句强化版)", "2️⃣ 语法结构特训", "3️⃣ 雅思学术阅读", "4️⃣ 实用场景翻译", "5️⃣ 全真雅思听力模拟 (一题一框版)", "6️⃣ 观点或图表写作"]

for k, title in zip(keys, titles):
    quest_raw = st.session_state.quests.get(k)
    if quest_raw:
        with st.expander(title, expanded=False):
            if k == "vocabulary":
                st.info("💡 研读下方的地道真题例句，在输入框中写出单词的意思或派生变形：")
                vocab_data = quest_raw if isinstance(quest_raw, list) else []
                if not vocab_data: continue

                user_answers = {}
                for idx, item in enumerate(vocab_data):
                    if isinstance(item, dict):
                        word = item.get("word", "Unknown")
                        example = item.get("example", "No example available.")
                        st.markdown(f"### 📍 Word {idx+1}: `{word}`")
                        st.markdown(f"📖 **Core Example**: *{example}*")
                        user_answers[word] = st.text_input(f"输入含义或派生变形：", key=f"vocab_input_{idx}")
                        st.markdown("---")

                if st.button(f"🚀 统一提交 {title} 答卷", key=f"btn_{k}_daily", type="primary"):
                    ans_compiled = "\n".join([f"单词: {w} | 学生猜测: {a}" for w, a in user_answers.items() if a.strip()])
                    with st.spinner("批阅中..."):
                        fb = ds_client.chat.completions.create(
                            model="deepseek-chat", 
                            messages=[{"role": "user", "content": f"题目及例句：{str(vocab_data)}\n学生回答：\n{ans_compiled}\n请逐一分析，详细列出每个词的释义、词性转换及雅思替换考点。"}] 
                        )
                        st.success("批改完成！")
                        st.markdown(fb.choices[0].message.content)
            
            elif k == "listening" and isinstance(quest_raw, dict):
                audio_text = quest_raw.get("audio_text", "")
                questions_raw = quest_raw.get("questions", [])
                transcript = quest_raw.get("transcript", audio_text)
                
                st.info("💡 真实雅思长听力。原文已盲听隐藏，请播放音频后逐题在独立输入框作答。")
                if st.button("▶ 播放纯正英式听力 (无名字干扰)", key=f"play_audio_{k}"):
                    tts = gTTS(text=audio_text, lang='en', tld='co.uk')
                    buf = io.BytesIO()
                    tts.write_to_fp(buf)
                    st.audio(buf, format='audio/mp3')
                
                st.markdown("### 📝 听力测试题")
                listen_q_list = questions_raw if isinstance(questions_raw, list) else [str(questions_raw)]

                user_listen_answers = {}
                for idx, q_text in enumerate(listen_q_list):
                    st.markdown(f"**{q_text}**")
                    user_listen_answers[f"Question {idx+1}"] = st.text_input(f"输入 Question {idx+1} 的答案：", key=f"listen_input_{idx}")
                
                if st.button(f"🚀 统一提交 {title} 答卷", key=f"btn_{k}_daily", type="primary"):
                    listen_ans_compiled = "\n".join([f"{key_q}: {v}" for key_q, v in user_listen_answers.items() if v.strip()])
                    with st.spinner("阅卷中..."):
                        fb = ds_client.chat.completions.create(
                            model="deepseek-chat", 
                            messages=[{"role": "user", "content": f"听力题目列表：{listen_q_list}\n听力原文：{transcript}\n学生答案：\n{listen_ans_compiled}\n请按照雅思标准严格阅卷批改。"}] 
                        )
                        st.success("批改完成！")
                        st.markdown(fb.choices[0].message.content)
                        with st.expander("👀 查看精美听力长原文", expanded=True): st.write(transcript)

            else:
                display_text = " ".join([str(v) for v in quest_raw.values()]) if isinstance(quest_raw, dict) else str(quest_raw)
                st.markdown(display_text)
                ans = st.text_area("在此作答：", key=f"ans_{k}_daily")
                if st.button(f"🚀 提交 {title} 答卷", key=f"btn_{k}_daily"):
                    with st.spinner("批阅中..."):
                        fb = ds_client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": f"题目：{display_text}\n学生回答：{ans}\n请给出纠错表达建议。"}] )
                        st.info(fb.choices[0].message.content)