import streamlit as st
from openai import OpenAI

# --- 安全检查与记忆挂载 ---
if "current_user" not in st.session_state or not st.session_state.current_user:
    st.warning("🧙‍♂️ 请先返回主页面（main）进行巫师身份验证登录哦！")
    st.stop()

if "DEEPSEEK_API_KEY" not in st.secrets:
    st.error("❌ 缺少 API 密钥。请确保已经配置了 DEEPSEEK_API_KEY。")
    st.stop()

client = OpenAI(
    api_key=st.secrets["DEEPSEEK_API_KEY"], 
    base_url="https://api.deepseek.com"
)

st.set_page_config(page_title="雅思词汇塔", layout="wide")
st.title("🏰 雅思词汇塔")
st.write("在这里通过场景化学习，构建你的高分词汇库。")

# --- 状态管理 ---
if "vocab_log" not in st.session_state:
    st.session_state.vocab_log = []

# --- 界面双分栏设计 ---
tab1, tab2 = st.tabs(["✨ AI 生成话题词汇", "📥 导入生词本"])

with tab1:
    st.subheader("场景化词汇抽取")
    topic = st.text_input("请输入你想学习的雅思话题 (例如: Environment, Education, Travel):")

    if st.button("开始构建词汇塔"):
        if not topic:
            st.warning("请先输入一个话题！")
        else:
            with st.spinner("正在抽取高分词汇..."):
                prompt = f"你是一名雅思高级讲师。请针对话题 '{topic}'，提供 5 个雅思口语/写作常用高分词汇，并给出每个词的英文释义、例句以及同义词替换。请以清晰的 Markdown 格式输出。"
                
                try:
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "system", "content": "你是专业的雅思词汇助手。"}, {"role": "user", "content": prompt}]
                    )
                    result = response.choices[0].message.content
                    st.session_state.vocab_log.append({"topic": topic, "content": result})
                except Exception as e:
                    st.error(f"构建失败: {e}")

# --- 报错对应的导入功能块（严格对齐） ---
with tab2:
    st.subheader("解析本地生词本")
    st.write("📥 或者导入你自己的生词本：")
    uploaded_file = st.file_uploader("支持上传 TXT 格式的单词列表", type=['txt'])
    
    if uploaded_file is not None:
        if st.button("开始解析我的生词"):
            with st.spinner("正在解析文件并生成精讲..."):
                try:
                    # 读取文本内容
                    # 提取文件字节
file_bytes = uploaded_file.getvalue()
try:
    # 优先使用 utf-8-sig，它能自动过滤掉 Windows 的隐形 BOM 头 (0xef)
    text_content = file_bytes.decode("utf-8-sig")
except UnicodeDecodeError:
    try:
        # 如果还报错，说明可能是国内 Windows 默认的 GBK 编码，尝试用 GBK 解码
        text_content = file_bytes.decode("gbk", errors="ignore")
    except Exception as e:
        st.error(f"无法识别文件编码，请确保文件是 TXT 格式。错误详情：{e}")
        st.stop()
                    prompt = f"以下是学生导入的生词列表，请作为雅思老师，为这些单词提供精准的中文翻译、音标和一个雅思相关的英文例句：\n\n{text_content}"
                    
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "system", "content": "你是专业的雅思词汇助手。"}, {"role": "user", "content": prompt}]
                    )
                    result = response.choices[0].message.content
                    st.session_state.vocab_log.append({"topic": f"生词本导入: {uploaded_file.name}", "content": result})
                    st.success("解析完成！请在下方查看。")
                except Exception as e:
                    st.error(f"文件解析失败: {e}")

st.markdown("---")

# --- 显示历史记录 ---
if st.session_state.vocab_log:
    st.subheader("📚 你的词汇塔记录")
    for entry in st.session_state.vocab_log:
        with st.expander(f"📌 {entry['topic']}", expanded=True):
            st.markdown(entry['content'])
            
    if st.button("🧹 清空词汇塔"):
        st.session_state.vocab_log = []
        st.rerun()