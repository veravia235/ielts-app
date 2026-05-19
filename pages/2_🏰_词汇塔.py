import streamlit as st
from openai import OpenAI
import json
import random
from gtts import gTTS
import io
# 引入底层工具箱
from utils.user_data import save_user_data

# 安全拦截
if "current_user" not in st.session_state or not st.session_state.current_user:
    st.warning("🧙‍♂️ 请先返回主页面（main）进行巫师身份验证登录哦！")
    st.stop()

username = st.session_state.current_user
if "word_bank" not in st.session_state: st.session_state.word_bank = st.session_state.user_data.get("word_bank", [])
if "failed_words" not in st.session_state: st.session_state.failed_words = set(st.session_state.user_data.get("failed_words", []))
if "last_lesson" not in st.session_state: st.session_state.last_lesson = st.session_state.user_data.get("last_lesson", "尚未开启首日课程")
if "study_sessions" not in st.session_state: st.session_state.study_sessions = st.session_state.user_data.get("study_sessions", 0)

# 词汇塔专属临时状态初始化
if "current_test_word" not in st.session_state: st.session_state.current_test_word = None
if "word_learning_stage" not in st.session_state: st.session_state.word_learning_stage = "初筛"

ds_client = OpenAI(
    api_key=st.secrets["DEEPSEEK_API_KEY"], 
    base_url="https://api.deepseek.com"
)

st.title("🏰 霍格沃茨词汇强化塔")
st.write("欢迎来到词汇特训中心。在这里我们将拒绝死记硬背，通过前置认词与多题型组合，击碎黑魔法生词！")

# 页面排版布局：左侧主力闯关，右侧魔法字典
col_main, col_dict = st.columns([2, 1])

with col_main:
    st.markdown("### ⚔️ 词汇关卡中心")
    
    # 0. 词量召唤源头
    if st.button("🪄 召唤 30 个真题词汇卷轴 (扩充词量)"):
        with st.spinner("正在从魔法部调取学术词汇..."):
            prompt = f"请针对雅思水平提供30个核心学术词汇。必须严格输出JSON对象，格式如下：{{ 'words': [ {{ 'word': '单词', 'phonetic': '/音标/', 'meaning': '中文释义', 'example': '例句' }} ] }}"
            try:
                res = ds_client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompt}], response_format={"type": "json_object"})
                new_words = json.loads(res.choices[0].message.content).get("words", [])
                if new_words:
                    st.session_state.word_bank.extend(new_words)
                    save_user_data(username, st.session_state.word_bank, st.session_state.failed_words, st.session_state.last_lesson, st.session_state.study_sessions)
                    st.success(f"🎉 成功调取 {len(new_words)} 个新词！当前词库共 {len(st.session_state.word_bank)} 词。")
                    st.rerun()
            except Exception as e: st.error(f"召唤失败: {e}")
st.markdown("---")
    st.write("📥 或者导入你自己的生词本：")
    uploaded_file = st.file_uploader("上传私人羊皮纸 (.txt)，每行一个单词和释义（用横线或逗号隔开）", type=["txt"])
    if uploaded_file and st.button("✅ 确认导入文本词库", type="primary"):
        lines = [line.strip() for line in uploaded_file.getvalue().decode("utf-8").split('\n') if line.strip()]
        count = 0
        for line in lines:
            sep = '-' if '-' in line else (', ' if ', ' in line else ( '，' if '，' in line else None))
            if sep and len(line.split(sep, 1)) == 2:
                parts = line.split(sep, 1)
                # 防止重复导入
                if not any(w['word'].lower() == parts[0].strip().lower() for w in st.session_state.word_bank):
                    st.session_state.word_bank.append({"word": parts[0].strip(), "meaning": parts[1].strip(), "phonetic": "N/A", "example": "私人词库导入"})
                    count += 1
        if count: 
            save_user_data(username, st.session_state.word_bank, st.session_state.failed_words, st.session_state.last_lesson, st.session_state.study_sessions)
            st.success(f"🎉 成功从羊皮纸中提取并导入 {count} 个专属词汇！")
            st.rerun()
    if not st.session_state.word_bank:
        st.info("💡 你的藏书阁空空如也，请点击上方按钮召唤新词汇，或者在右侧字典里主动加词。")
    else:
        # 随机抽取一个词开始过关
        if not st.session_state.current_test_word:
            st.session_state.current_test_word = random.choice(st.session_state.word_bank)
            st.session_state.word_learning_stage = "初筛"
            
        w_obj = st.session_state.current_test_word
        word_text = w_obj.get("word", "")
        
        st.markdown(f"## 🎯 当前迎战词汇：**{word_text}**")
        
        # 触发发音
        if st.button("🔊 听纯正英音", key="play_tower_word"):
            tts = gTTS(text=word_text, lang='en', tld='co.uk')
            buf = io.BytesIO()
            tts.write_to_fp(buf)
            st.audio(buf, format='audio/mp3')

        # --- 环节 1：前置认知选择 ---
        if st.session_state.word_learning_stage == "初筛":
            st.markdown(f"**音标**：{w_obj.get('phonetic', 'N/A')}")
            st.info("🔮 仔细端详这个单词，在不看释义的情况下，你对它的掌握程度是？")
            
            b1, b2, b3 = st.columns(3)
            if b1.button("✅ 极其熟悉 (跳过)"):
                st.success("词汇熟练度+1！自动切入下一个。")
                st.session_state.current_test_word = None
                st.rerun()
            if b2.button("🤔 模糊/想不起来 (进入拼写与听写)"):
                st.session_state.word_learning_stage = "多题型特训"
                st.rerun()
            if b3.button("❌ 彻底不认识 (打入错题本并重点特训)"):
                st.session_state.failed_words.add(word_text)
                save_user_data(username, st.session_state.word_bank, st.session_state.failed_words, st.session_state.last_lesson, st.session_state.study_sessions)
                st.session_state.word_learning_stage = "多题型特训"
                st.rerun()

        # --- 环节 2：多题型全方位轰炸 ---
        elif st.session_state.word_learning_stage == "多题型特训":
            task_type = st.radio("选择你当前想要进行的防御特训模式：", ["🎧 盲听音频拼写", "📝 雅思学术例句填空", "⚔️ 终极魔咒造句"])
            
            if task_type == "🎧 盲听音频拼写":
                st.write("请点击上方发音条进行盲听，并在下方完整拼写出该单词（大小写均可）：")
                user_spell = st.text_input("你的拼写：", key="spell_input")
                if st.button("提交拼写卷轴"):
                    if user_spell.strip().lower() == word_text.lower():
                        st.success("🎉 拼写百分之百正确！防御成功！")
                        if word_text in st.session_state.failed_words: 
                            st.session_state.failed_words.remove(word_text)
                            save_user_data(username, st.session_state.word_bank, st.session_state.failed_words, st.session_state.last_lesson, st.session_state.study_sessions)
                        st.session_state.current_test_word = None
                        st.rerun()
                    else:
                        st.error(f"❌ 拼写有误哦，正确答案是: {word_text}。继续加油！")
                        st.session_state.failed_words.add(word_text)
                        save_user_data(username, st.session_state.word_bank, st.session_state.failed_words, st.session_state.last_lesson, st.session_state.study_sessions)

            elif task_type == "📝 雅思学术例句填空":
                st.markdown("### 📖 根据上下文和释义补全句子")
                st.markdown(f"**中文含义**：{w_obj.get('meaning', '暂无释义')}")
                # 隐藏核心词，模拟真实填空
                blind_example = w_obj.get('example', 'No example').replace(word_text, "_______").replace(word_text.capitalize(), "_______")
                st.write(f"👉 *Example:* {blind_example}")
                
                user_fill = st.text_input("请在这补全抠掉的单词（或其对应的派生词变形）：", key="fill_input")
                if st.button("提交填空结果"):
                    if word_text.lower() in user_fill.strip().lower():
                        st.success("🎉 切中要害！回答正确！")
                        st.session_state.current_test_word = None
                        st.rerun()
                    else:
                        st.info(f"💡 没填对？核心原词是 `{word_text}`。完整例句：\n*{w_obj.get('example')}*")

            elif task_type == "⚔️ 终极魔咒造句":
                st.markdown(f"### 用 `{word_text}` 施展一段雅思级学术造句")
                st.write(f"已知含义：{w_obj.get('meaning')}")
                user_essay = st.text_input("在下方输入你亲手书写的英语句子：", key="essay_word_input")
                if st.button("提交造句进行论文级批改"):
                    with st.spinner("正在审查语法和句式地道度..."):
                        res = ds_client.chat.completions.create(
                            model="deepseek-chat",
                            messages=[{"role": "user", "content": f"学生要练习单词【{word_text}】的用法，他写的造句子是：{user_essay}。请用中文针对他的语法、用词进行批改点评，如果句子没问题，明确在开头包含“咒语生效”四个字。"}]
                        )
                        st.markdown(res.choices[0].message.content)
                        if "咒语生效" in res.choices[0].message.content and word_text in st.session_state.failed_words:
                            st.session_state.failed_words.remove(word_text)
                            save_user_data(username, st.session_state.word_bank, st.session_state.failed_words, st.session_state.last_lesson, st.session_state.study_sessions)

            if st.button("⏭ 换个单词，进入下一关"):
                st.session_state.current_test_word = None
                st.rerun()

# --- 右侧悬浮：魔法字典与随时随地主动加词系统 ---
with col_dict:
    st.markdown("### 🔍 魔法放大镜 (随时查词)")
    search_query = st.text_input("输入你在听力/阅读里遇到的生词：", placeholder="e.g., fluctuate")
    
    if search_query.strip():
        if st.button("⚡ 调用大模型查询释义"):
            with st.spinner("正在翻阅剑桥高级词典..."):
                dict_prompt = f"给出生词【{search_query}】在雅思中的核心中文释义、英式音标、一句极其地道的学术真题风格纯英文例句。必须严格输出JSON格式，包含 word, phonetic, meaning, example 键。"
                try:
                    dict_res = ds_client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": dict_prompt}], response_format={"type": "json_object"})
                    search_res_obj = json.loads(dict_res.choices[0].message.content)
                    
                    st.session_state.last_search_result = search_res_obj
                    st.success("查找完毕！")
                except Exception as e: st.error(f"查词中断：{e}")

        if "last_search_result" in st.session_state and st.session_state.last_search_result.get("word", "").lower() == search_query.strip().lower():
            s_obj = st.session_state.last_search_result
            st.markdown(f"**[{s_obj.get('word')}]** `{s_obj.get('phonetic')}`")
            st.write(f"**释义**：{s_obj.get('meaning')}")
            st.write(f"**真题风格例句**：*{s_obj.get('example')}*")
            
            # ➕ 触发主动加词到用户的专属词库
            if st.button("➕ 收入我的专属生词本", type="primary"):
                # 防止重复加入
                if not any(w['word'].lower() == s_obj['word'].lower() for w in st.session_state.word_bank):
                    st.session_state.word_bank.append(s_obj)
                    st.session_state.failed_words.add(s_obj['word']) # 自动加入错题特训
                    save_user_data(username, st.session_state.word_bank, st.session_state.failed_words, st.session_state.last_lesson, st.session_state.study_sessions)
                    st.success(f"🎉 成功！`{s_obj.get('word')}` 已打入黑魔法词汇池，它会被自动联动塞入你今天的听力、阅读教案中！")
                else:
                    st.warning("⚠️ 这个单词早就在你的生词本里啦！")