import streamlit as st
import pandas as pd
import sounddevice as sd
import wave
import numpy as np
import time
import os
from tempfile import NamedTemporaryFile
from openai import OpenAI
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def clean_transcribed_text(text):
    """
    清理轉錄文字，移除不相關的固定文字模式
    """
    if not text:
        return text
        
    patterns_to_remove = [
        "請不吝點贊訂閱轉發打賞支持明鏡與點點欄目",
        "請訂閱點贊轉發",
        "謝謝觀看",
        "歡迎訂閱",
        "請點贊轉發",
    ]
    
    cleaned_text = text
    for pattern in patterns_to_remove:
        cleaned_text = cleaned_text.replace(pattern, "")
    
    cleaned_text = "\n".join(line.strip() for line in cleaned_text.splitlines() if line.strip())
    
    return cleaned_text

def record_audio(duration=5, sample_rate=16000, channels=1):
    """
    使用 sounddevice 錄製音訊，並顯示進度條
    """
    try:
        estimated_size_mb = (sample_rate * 2 * channels * duration) / (1024 * 1024)
        st.info(f"預估檔案大小：{estimated_size_mb:.2f} MB")
        
        progress_bar = st.progress(0)
        time_text = st.empty()
        
        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=channels,
            dtype='int16'
        )
        
        start_time = time.time()
        while sd.get_stream().active:
            elapsed_time = time.time() - start_time
            remaining_time = duration - elapsed_time
            progress = min(elapsed_time / duration, 1.0)
            
            progress_bar.progress(progress)
            time_text.markdown(f"⏱️ 剩餘時間：{remaining_time:.1f} 秒")
            
            time.sleep(0.1)
        
        progress_bar.progress(1.0)
        time_text.markdown("✅ 錄音完成！")
        
        with NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            filename = temp_file.name
            
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(recording.tobytes())
            
            actual_size_mb = os.path.getsize(filename) / (1024 * 1024)
            st.info(f"實際檔案大小：{actual_size_mb:.2f} MB")
        
        return filename, recording
        
    except Exception as e:
        st.error(f"❌ 錄音失敗：{str(e)}")
        return None, None

def transcribe_audio(audio_file, client):
    """
    使用 Whisper API 將音訊檔案轉換為文字，保持原始語言
    """
    if not client:
        st.warning("無法獲取 OpenAI 客戶端，語音轉文字功能無法使用。")
        return None
        
    try:
        st.info("正在使用 Whisper API 轉換語音...")
        
        with open(audio_file, "rb") as audio:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio,
                # 移除 language 參數，讓 Whisper 自動檢測語言
            )
            
        text = clean_transcribed_text(response.text.strip())
        
        if not text:
            st.warning("未檢測到有效的語音內容")
            return None
            
        st.success("✅ 語音轉換成功！")
        return text
        
    except Exception as e:
        st.error(f"❌ 語音轉換失敗：{str(e)}")
        return None

def correct_text_with_gpt(text, client):
    """
    使用 GPT API 修正文字
    """
    if not client:
        st.warning("無法獲取 OpenAI 客戶端，文字修正功能無法使用。")
        return text

    try:
        st.info("正在呼叫 OpenAI API 進行文字修正...")
        
        system_content = "繁體中文回覆，你是一個專業的醫學教育文字編輯助手。你的任務是整理臨床教師對實習醫學生的口頭回饋，使其更有條理且易於閱讀。請保持原意，但可以：\n1. 修正錯別字和語法\n2. 改善句子結構\n3. 適當分段\n4. 使用更專業的醫學用語\n5. 保持評語的建設性和教育意義\n\n請直接返回修改後的文字，不需要其他說明。"
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": text}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        st.success("✅ OpenAI API 呼叫成功！")
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"❌ 呼叫 OpenAI API 時發生錯誤：{str(e)}")
        return text

def show_voice_input_section(client):
    """顯示語音輸入部分"""
    try:
        if not client:
            st.warning('請先設置有效的 OpenAI API 金鑰才能使用語音轉文字功能')
            return
            
        st.subheader("語音輸入")
        
        if 'accumulated_text' not in st.session_state:
            st.session_state.accumulated_text = ""
        
        col1, col2 = st.columns(2)
        with col1:
            duration = st.slider("錄音時長（秒）", 
                               min_value=10,
                               max_value=30,
                               value=15,
                               step=5)
        with col2:
            st.info("💡 請確保在安靜的環境下錄音，並保持適當的音量")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🎙️ 開始錄音"):
                filename, recording = record_audio(duration=duration)
                if filename:
                    st.session_state.audio_file = filename
                    st.session_state.recording_data = recording
                    st.audio(filename)
                    
                    text = transcribe_audio(filename, client)
                    if text:
                        if st.session_state.accumulated_text:
                            st.session_state.accumulated_text += "\n"
                        st.session_state.accumulated_text += text
                        st.session_state.input_comments = st.session_state.accumulated_text
                        st.session_state.transcribed_text = st.session_state.accumulated_text
        
        with col2:
            uploaded_file = st.file_uploader("或上傳音訊檔案", type=['wav', 'mp3', 'm4a'])
            if uploaded_file:
                with NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    temp_file.write(uploaded_file.getvalue())
                    filename = temp_file.name
                
                st.audio(filename)
                
                if st.button("開始轉換"):
                    text = transcribe_audio(filename, client)
                    if text:
                        if st.session_state.accumulated_text:
                            st.session_state.accumulated_text += "\n"
                        st.session_state.accumulated_text += text
                        st.session_state.input_comments = st.session_state.accumulated_text
                        st.session_state.transcribed_text = st.session_state.accumulated_text
        
        with col3:
            if st.button("清除所有文字"):
                st.session_state.accumulated_text = ""
                st.session_state.input_comments = ""
                st.session_state.transcribed_text = ""
                st.success("已清除所有文字")
        
        if st.session_state.accumulated_text:
            st.text_area("累積的轉換結果", 
                        st.session_state.accumulated_text,
                        height=150,
                        key="accumulated_text_display")
            
            if st.button("GPT修正文字"):
                corrected_text = correct_text_with_gpt(st.session_state.accumulated_text, client)
                if corrected_text:
                    st.session_state.accumulated_text = corrected_text
                    st.session_state.input_comments = corrected_text
                    st.session_state.corrected_comments = corrected_text
                    
    except Exception as e:
        st.error(f"顯示語音輸入部分時發生錯誤: {str(e)}")

def show_test_form(client):
    """顯示測試表單"""
    st.header("測試表單填寫")
    
    # 添加語音輸入部分
    show_voice_input_section(client)
    
    # 其他評語（表單外）
    st.subheader("其他評語")
    comments = st.text_area("請輸入評語", 
                           value=st.session_state.get('input_comments', ''),
                           height=100, 
                           key="input_comments")
    
    # 使用表單容器
    with st.form("test_form", clear_on_submit=False):
        st.subheader("基本資訊")
        col1, col2 = st.columns(2)
        with col1:
            name = st.selectbox(
                "姓名",
                ["丁OO"]
            )
        with col2:
            batch = st.selectbox(
                "梯次",
                ["2025/02", "2025/03", "2025/04"]
            )
        
        # EPA 評分項目
        st.subheader("EPA 評分")
        epa_scores = {}
        for i in range(1, 6):
            epa_scores[f"EPA_{i}"] = st.slider(
                f"EPA {i} 評分",
                min_value=1,
                max_value=5,
                value=3,
                help="1: 需要監督, 2: 需要指導, 3: 需要提示, 4: 獨立完成, 5: 可指導他人"
            )
        
        # 顯示最終評語
        st.subheader("最終評語")
        final_comments = st.text_area("確認評語", comments, height=100, key="final_comments", disabled=True)
        
        # 提交按鈕
        submitted = st.form_submit_button("提交表單")
        
        if submitted:
            # 建立資料字典
            form_data = {
                "姓名": name,
                "梯次": batch,
                "EPA_1": epa_scores["EPA_1"],
                "EPA_2": epa_scores["EPA_2"],
                "EPA_3": epa_scores["EPA_3"],
                "EPA_4": epa_scores["EPA_4"],
                "EPA_5": epa_scores["EPA_5"],
                "評語": comments,
                "提交時間": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 將資料轉換為 DataFrame
            df = pd.DataFrame([form_data])
            
            try:
                # 如果檔案存在，讀取並附加新資料
                existing_df = pd.read_csv("test_form_data.csv")
                df = pd.concat([existing_df, df], ignore_index=True)
            except FileNotFoundError:
                pass
            
            # 儲存到 CSV 檔案
            df.to_csv("test_form_data.csv", index=False, encoding='utf-8-sig')
            
            # 顯示成功訊息
            st.success("表單提交成功！")
            st.write("提交的資料：")
            st.write(f"姓名：{name}")
            st.write(f"梯次：{batch}")
            st.write("EPA 評分：", epa_scores)
            st.write("評語：", comments)

def show_test_results():
    """顯示測試結果分析"""
    st.header("測試結果分析")
    
    try:
        # 讀取 CSV 檔案
        df = pd.read_csv("test_form_data.csv")
        
        # 顯示原始資料
        st.subheader("原始資料")
        st.dataframe(df)
        
        # EPA 評分統計
        st.subheader("EPA 評分統計")
        epa_columns = [f"EPA_{i}" for i in range(1, 6)]
        epa_stats = df[epa_columns].describe()
        st.dataframe(epa_stats)
        
        # EPA 平均分數雷達圖
        st.subheader("EPA 平均分數雷達圖")
        epa_means = df[epa_columns].mean()
        
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=epa_means.values,
            theta=[f"EPA {i}" for i in range(1, 6)],
            fill='toself',
            name='平均分數',
            hovertemplate='EPA: %{theta}<br>平均分數: %{r:.2f}<extra></extra>'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 5],
                    ticktext=['1', '2', '3', '4', '5'],
                    tickvals=[1, 2, 3, 4, 5]
                )
            ),
            showlegend=False,
            title="EPA 平均分數雷達圖",
            height=500
        )
        st.plotly_chart(fig, width="stretch")
        
        # EPA 評分趨勢圖
        st.subheader("EPA 評分趨勢（按梯次）")
        
        epa_trend = df.groupby('梯次')[epa_columns].mean().reset_index()
        
        fig = go.Figure()
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        
        for i, epa in enumerate(epa_columns):
            fig.add_trace(go.Scatter(
                x=epa_trend['梯次'],
                y=epa_trend[epa],
                mode='lines+markers',
                name=f'EPA {i+1}',
                line=dict(width=3, color=colors[i]),
                marker=dict(size=10, symbol='circle', color=colors[i]),
                hovertemplate='梯次: %{x}<br>平均分數: %{y:.2f}<extra></extra>'
            ))
        
        fig.update_layout(
            title=dict(
                text="EPA 評分趨勢（按梯次）",
                font=dict(size=24)
            ),
            xaxis=dict(
                title="梯次",
                categoryorder='array',
                categoryarray=['2025/02', '2025/03', '2025/04'],
                tickfont=dict(size=14),
                gridcolor='lightgrey'
            ),
            yaxis=dict(
                title="平均分數",
                range=[1, 5],
                tickmode='linear',
                tick0=1,
                dtick=1,
                tickfont=dict(size=14),
                gridcolor='lightgrey'
            ),
            hovermode="x unified",
            showlegend=True,
            legend=dict(
                font=dict(size=12),
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=0.99
            ),
            height=600,
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(t=100)
        )
        
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgrey')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgrey')
        
        st.plotly_chart(fig, width="stretch")
        
        # EPA 評分分布圖
        st.subheader("EPA 評分分布")
        fig = make_subplots(rows=2, cols=3, subplot_titles=[f"{epa} 分布" for epa in epa_columns])
        
        for i, epa in enumerate(epa_columns):
            row = (i // 3) + 1
            col = (i % 3) + 1
            
            fig.add_trace(
                go.Histogram(
                    x=df[epa],
                    nbinsx=5,
                    name=epa,
                    hovertemplate='評分: %{x}<br>次數: %{y}<extra></extra>'
                ),
                row=row, col=col
            )
        
        fig.update_layout(
            height=800,
            showlegend=False,
            title_text="EPA 評分分布"
        )
        st.plotly_chart(fig, width="stretch")
        
        # 評語分析
        st.subheader("評語分析")
        if not df['評語'].empty:
            st.write("最近 5 筆評語：")
            for comment in df['評語'].tail(5):
                st.write(f"- {comment}")
        
    except FileNotFoundError:
        st.warning("尚未有測試資料，請先填寫表單。")
    except Exception as e:
        st.error(f"讀取或分析資料時發生錯誤：{str(e)}") 