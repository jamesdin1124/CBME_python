from flask import Flask, render_template, request, jsonify
import gspread
from google.oauth2.service_account import Credentials
import os
import openai
from datetime import datetime
import json
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 檢查 OpenAI API 金鑰
if not os.getenv('OPENAI_API_KEY'):
    raise ValueError("未設定 OPENAI_API_KEY 環境變數")

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Google Sheets API 設定
DEFAULT_SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1VZRYRrsSMNUKoWM32gc5D9FykCHm7IRgcmR1_qXx8_w/edit?resourcekey=&gid=1986457679#gid=1986457679"

# OpenAI API 設定
openai.api_key = os.getenv('OPENAI_API_KEY')

def setup_google_connection():
    """設定與 Google API 的連接"""
    try:
        # 取得目前檔案的目錄路徑
        current_dir = os.path.dirname(os.path.abspath(__file__))
        credentials_path = os.path.join(current_dir, 'credentials.json')
        
        # 檢查 credentials.json 檔案是否存在
        if not os.path.exists(credentials_path):
            raise Exception(f"未找到 credentials.json 檔案，預期路徑：{credentials_path}")
            
        # 設定 Google API 範圍
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/cloud-platform'
        ]
        
        # 建立認證
        creds = Credentials.from_service_account_file(credentials_path, scopes=scope)
        client = gspread.authorize(creds)
        
        # 測試連接
        try:
            # 嘗試列出所有試算表
            client.list_spreadsheet_files()
            print("成功連接到 Google Sheets API")
        except Exception as e:
            print(f"連接測試失敗：{str(e)}")
            return None
        
        return client
    except Exception as e:
        print(f"連接 Google API 時發生錯誤：{str(e)}")
        return None

def extract_spreadsheet_id(url):
    """從 Google 試算表 URL 中提取 spreadsheet ID"""
    import re
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
    if match:
        return match.group(1)
    return None

@app.route('/')
def index():
    """渲染主頁面"""
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit_form():
    """處理表單提交"""
    try:
        # 檢查請求內容類型
        if not request.is_json:
            return jsonify({
                'status': 'error',
                'message': '請求內容必須是 JSON 格式'
            }), 400

        # 取得請求資料
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': '未收到有效的表單資料'
            }), 400

        # 設定 Google Sheets 連接
        client = setup_google_connection()
        if client is None:
            return jsonify({
                'status': 'error',
                'message': '無法連接到 Google Sheets'
            }), 500

        # 從 URL 提取 spreadsheet ID
        spreadsheet_id = extract_spreadsheet_id(DEFAULT_SPREADSHEET_URL)
        if not spreadsheet_id:
            return jsonify({
                'status': 'error',
                'message': '無效的試算表 URL'
            }), 500

        # 開啟試算表
        try:
            spreadsheet = client.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.sheet1
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'無法開啟試算表：{str(e)}'
            }), 500

        # 準備要寫入的資料
        values = [
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            data.get('hierarchy', ''),
            data.get('student_id', ''),
            data.get('student_name', ''),
            data.get('location', ''),
            data.get('patient_id', ''),
            data.get('clinical_scenario', ''),
            data.get('student_epa_level', ''),
            data.get('patient_difficulty', ''),
            data.get('teacher_epa_level', ''),
            data.get('feedback', '')
        ]

        # 寫入資料
        try:
            worksheet.append_row(values)
            return jsonify({
                'status': 'success',
                'message': '資料已成功寫入試算表'
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'寫入資料時發生錯誤：{str(e)}'
            }), 500

    except Exception as e:
        print(f"提交表單時發生錯誤：{str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'處理表單時發生錯誤：{str(e)}'
        }), 500

@app.route('/enhance_text', methods=['POST'])
def enhance_text():
    """使用 OpenAI 增強文字內容"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({
                'status': 'error',
                'message': '未收到文字內容'
            }), 400

        text = data['text']
        
        # 使用 OpenAI 修飾文字
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一個專業的醫學教育回饋修飾助手，請將以下回饋內容改寫得更專業、更具建設性，同時保持原始意思。"},
                {"role": "user", "content": text}
            ]
        )
        
        enhanced_text = response.choices[0].message.content
        return jsonify({
            'status': 'success',
            'text': enhanced_text
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001) 