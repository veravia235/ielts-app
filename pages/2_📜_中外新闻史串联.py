import streamlit as st
from openai import OpenAI
import json

st.set_page_config(page_title="中外新闻史串联", page_icon="📜", layout="wide")
st.title("📜 中外新闻史时空纵横线")

base_url = "https://api.deepseek.com/v1"

# 检查权限与大脑
if "api_key" not in st.session_state or not st.session_state.api_key:
    st.warning("⚠️ 请先回到主页配置你的 API 密钥！")
    st.stop()
if "active_brain" not in st.session_state or not st.session_state.active_brain:
    st.warning("⚠️ 请先回到主页上传你的笔记并构建记忆大脑！")
    st.stop()

st.markdown("### 🧙‍♂️ 记忆库时空重构")
st.caption("点击下方按钮，AI将精读你上传的笔记，自动抽炼出核心考点轴。")

if st.button("✨ 启动全库地毯式检索 (深度重构)"):
    with st.spinner("正在执行地毯式全库检索，这可能需要十几秒，请稍候..."):
        client = OpenAI(api_key=st.session_state.api_key, base_url=base_url)
        
        # 1. 暴力拉满检索量：k=80 意味着它会瞬间抓取海量的上下文碎片
        matched_history = st.session_state.active_brain.similarity_search("新闻史 年份 事件 传播史 理论 报刊 阶段 演进 创办 创刊", k=80)
        
        # 2. 拼接成超长上下文喂给 AI
        h_context = "\n".join([d.page_content for d in matched_history])
        
        # 3. 极度苛刻的提示词：强迫它把几十万字里的精髓全挤出来，且内容必须长
        h_prompt = f"""
        你现在是顶级新传考研导师。请执行【地毯式全景信息提取】。
        阅读以下用户笔记的所有片段，并构建一份【高密度、全覆盖】的中外新闻史时间轴。
        
        【参考素材】：
        {h_context}
        
        【任务要求】：
        1. 绝不遗漏：必须覆盖素材中提到的所有核心报刊、重大历史事件与关键人物。
        2. 数量要求：至少提取 15 到 25 个独立的历史节点！不要少！
        3. 深度解析：每个节点的“名解踩分点”和“论述题金句”必须详实饱满，可以直接作为考场答题语料，严禁一笔带过！
        4. 纪律：行文中绝对禁止使用‘极其’一词，视具体情况更改为‘非常’、‘相当’、‘很是’、‘极度’、‘十分’等。
        
        【输出格式】：严格的 JSON 数组格式。
        [
          {{"time": "年份/时期", "title": "事件/报刊", "person": "核心人物", "tag": "详细的名解踩分点(包含核心考点)", "significance": "饱满的论述题高分语料金句(不少于50字)"}}
        ]
        """
        try:
            res = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": h_prompt}],
                response_format={ 'type': 'json_object' }
            )
            import json
            res_content = res.choices[0].message.content
            res_data = json.loads(res_content)
            
            # 兼容不同格式的 JSON 提取
            if isinstance(res_data, list):
                st.session_state.dynamic_history = res_data
            elif "history" in res_data:
                st.session_state.dynamic_history = res_data["history"]
            else:
                # 兜底机制：提取 JSON 中的第一个列表
                for key, value in res_data.items():
                    if isinstance(value, list):
                        st.session_state.dynamic_history = value
                        break
            
            st.success("🎉 全景时空轴重构成功！知识密度大幅跃升！")
        except Exception as e:
            st.error(f"历史数据深度挖掘失败: {e}")

st.markdown("---")

# 渲染视图
if "dynamic_history" in st.session_state and st.session_state.dynamic_history:
    st.subheader("📁 从你的资料库中自动重构出的独家历史考点轴")
    for item in st.session_state.dynamic_history:
        st.markdown(f"""
        <div style='padding: 22px; border-radius: 10px; border-left: 6px solid #c05621; background: #fffaf0; margin-bottom: 15px;'>
            <h4 style='color: #c05621; margin: 0 0 10px 0;'>⏱️ 时期/年份：{item.get('time', '未知')} | 《{item.get('title', '未知')}》</h4>
            <p style='margin: 5px 0;'><b>👤 核心人物：</b> {item.get('person', '无')}</p>
            <p style='margin: 5px 0;'><b>⚠️ 高频名解踩分点：</b> <span style='color:#c05621; font-weight:bold;'>{item.get('tag', '无')}</span></p>
            <p style='margin: 5px 0; background: #fff; padding: 8px; border-radius: 4px;'><b>📝 论述题高分语料金句：</b> <i>“{item.get('significance', '无')}”</i></p>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("👈 请在上方点击按钮，让 AI 深度解析你的笔记。")