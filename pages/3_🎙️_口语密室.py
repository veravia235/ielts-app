import streamlit as st
from openai import OpenAI
from gtts import gTTS
import io
import speech_recognition as sr
from utils.user_data import save_user_data

# --- 安全拦截与记忆挂载 ---
if "current_user" not in st.session_state or not st.session_state.current_user:
    st.warning("🧙‍♂️ 请先返回主页面（main）进行巫师身份验证登录哦！")
    st.stop()

username = st.session_state.current_user
if "oral_chat_log" not in st.session_state: st.session_state.oral_chat_log = []
if "interactive_chat_log" not in st.session_state: st.session_state.interactive_chat_log = []
if "difficulty" not in st.session_state: st.session_state.difficulty = "基础学徒 (4.5-5.5)"

ds_client = OpenAI(
    api_key=st.secrets["DEEPSEEK_API_KEY"], 
    base_url="https://api.deepseek.com"
)

st.title("🎙️ 魔法部口语密室")
st.write("请戴上耳机，调整麦克风。你将在这里直面考官，进行雅思口语的全真模拟。")

# 内部双开标签页
tab1, tab2 = st.tabs(["🗣️ Part 1 基础问答", "🕵️‍♂️ 考官密室 (全真语音交互)"])

with tab1:
    st.subheader(f"基础口语热身 ({st.session_state.difficulty})")
    
    if "auto_speaking_task" not in st.session_state:
        st.session_state.auto_speaking_task = "Let's talk about your hometown. Where are you from and what do you like about it?"

    st.info(f"📜 **今日热身课题：**\n\n{st.session_state.auto_speaking_task}")
    
    chat_container = st.container(height=350)
    for chat in st.session_state.oral_chat_log:
        with chat_container.chat_message(chat["role"]): st.markdown(chat["content"])

    audio_data = st.audio_input("点击麦克风回答")
    if audio_data: st.audio(audio_data)

    if user_speak := st.chat_input("输入对话内容...", key="oral_input"):
        st.session_state.oral_chat_log.append({"role": "user", "content": user_speak})
        with chat_container.chat_message("user"): st.markdown(user_speak)
        with chat_container.chat_message("assistant"):
            with st.spinner("考官正在回应..."):
                res = ds_client.chat.completions.create(
                    model="deepseek-chat", 
                    messages=[{"role": "system", "content": "你是雅思口语考官。保持全英文交流，严禁任何中文。"}, *st.session_state.oral_chat_log]
                ).choices[0].message.content
                st.markdown(res)
                st.session_state.oral_chat_log.append({"role": "assistant", "content": res})
        st.rerun()

    if st.button("🏁 结束热身并索要复盘报告", key="btn_oral_report"):
        if st.session_state.oral_chat_log:
            with st.spinner("正在生成复盘报告..."):
                review_res = ds_client.chat.completions.create(
                    model="deepseek-chat", 
                    messages=[{"role": "user", "content": f"请用中文深度复盘以下雅思口语对练：{str(st.session_state.oral_chat_log)}"}]
                ).choices[0].message.content
                st.session_state.oral_feedback_report = review_res
    if "oral_feedback_report" in st.session_state:
        with st.expander("📝 查看考官复盘报告", expanded=True): st.markdown(st.session_state.oral_feedback_report)

with tab2:
    st.subheader("考官密室：动态口语实战")
    st.caption("在这里，考官会全程用标准的英式口音音频对你进行追问。绝无中文字符干扰！")

    chat_container_int = st.container(height=400)

    if not st.session_state.interactive_chat_log:
        if st.button("🚪 敲门，开启全真考官对话"):
            with st.spinner("考官正在入座并开口..."):
                init_prompt = f"你是雅思口语考官麦格教授，学生水平【{st.session_state.difficulty}】。请用纯正的英语主动向学生提问一个简短的开场问题。**绝对禁止返回任何中文字符和人名提示前缀！**"
                res = ds_client.chat.completions.create(model="deepseek-chat", messages=[{"role": "system", "content": init_prompt}]).choices[0].message.content
                
                tts = gTTS(text=res, lang='en', tld='co.uk')
                buf = io.BytesIO()
                tts.write_to_fp(buf)
                st.session_state.interactive_chat_log.append({"role": "assistant", "content": res, "audio": buf.getvalue()})
                st.rerun()

    for chat in st.session_state.interactive_chat_log:
        with chat_container_int.chat_message(chat["role"]):
            st.markdown(chat["content"])
            if "audio" in chat: st.audio(chat["audio"], format="audio/mp3")

    if st.session_state.interactive_chat_log:
        st.write("🎙️ **你的回合（请打字或对着麦克风作答）**")
        audio_data_int = st.audio_input("点击麦克风录音", key="audio_int")
        user_text_int = st.chat_input("向考官作答...", key="text_int")

        user_speak_int = user_text_int if user_text_int else None
        
        # 🌟 如果侦测到麦克风有录音，立刻触发自动识别
        if audio_data_int: 
            with st.spinner("⏳ 正在听写你的发音..."):
                try:
                    r = sr.Recognizer()
                    with sr.AudioFile(audio_data_int) as source:
                        audio = r.record(source)
                    recognized_text = r.recognize_google(audio, language="en-GB")
                    st.success(f"🗣️ 你说的是：{recognized_text}")
                    user_speak_int = recognized_text
                except sr.UnknownValueError:
                    st.error("❌ 考官没有听清，请大点声或字正腔圆地再试一次！")
                except Exception as e:
                    st.error(f"❌ 语音识别中断（请检查网络连接）: {e}")

        if user_speak_int:
            clean_history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.interactive_chat_log]
            st.session_state.interactive_chat_log.append({"role": "user", "content": user_speak_int})
            clean_history.append({"role": "user", "content": user_speak_int})
            
            with chat_container_int.chat_message("user"): st.markdown(user_speak_int)
            
            with chat_container_int.chat_message("assistant"):
                with st.spinner("考官正在思考追问..."):
                    res = ds_client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "system", "content": "你是雅思口语考官。紧扣学生刚才的内容进行全英文追问。**绝对禁止任何中文字符和人名提示词！**"}, *clean_history]
                    )
                    ai_reply = res.choices[0].message.content
                    st.markdown(ai_reply)
                    
                    with st.spinner("生成英音原声..."):
                        tts = gTTS(text=ai_reply, lang='en', tld='co.uk')
                        buf = io.BytesIO()
                        tts.write_to_fp(buf)
                        st.audio(buf.getvalue(), format="audio/mp3")
                    
                    st.session_state.interactive_chat_log.append({"role": "assistant", "content": ai_reply, "audio": buf.getvalue()})
            st.rerun()

        if st.button("🏁 结束本轮密室对话并复盘", key="btn_int_report"):
            if len(st.session_state.interactive_chat_log) > 2:
                with st.spinner("正在生成深度反馈..."):
                    clean_history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.interactive_chat_log]
                    review_res = ds_client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "user", "content": f"请使用中文针对以下口语对话给出深度复盘，指出语法错误和高分替换表达：{str(clean_history)}"}]
                    ).choices[0].message.content
                    st.session_state.interactive_feedback = review_res
            else: st.warning("对话太短，考官无法准确评估。")
        
        if "interactive_feedback" in st.session_state:
            with st.expander("📝 查看密室复盘报告", expanded=True): st.markdown(st.session_state.interactive_feedback)