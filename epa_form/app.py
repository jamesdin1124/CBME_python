from flask import Flask, render_template, request, jsonify, redirect, url_for
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
DEFAULT_SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1I2GzYptiPvhN5dT3_qzVXlIAoPeI8S9MaTVzxfDVjrw/edit?gid=0#gid=0"

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
            error_msg = f"未找到 credentials.json 檔案，預期路徑：{credentials_path}"
            print(error_msg)
            print(f"當前工作目錄: {os.getcwd()}")
            print(f"模組目錄: {current_dir}")
            # 嘗試列出模組目錄的檔案
            try:
                files = os.listdir(current_dir)
                print(f"模組目錄檔案: {', '.join(files)}")
            except Exception as list_e:
                print(f"列出目錄檔案時出錯: {list_e}")
            return None
        
        print(f"找到憑證檔案: {credentials_path}")
        # 檢查檔案大小確保不是空檔案
        file_size = os.path.getsize(credentials_path)
        if file_size == 0:
            print(f"憑證檔案大小為0，可能是空檔案")
            return None
        print(f"憑證檔案大小: {file_size} bytes")
        
        # 嘗試讀取憑證內容以確保它是有效的 JSON
        try:
            with open(credentials_path, 'r') as f:
                cred_content = json.load(f)
                # 檢查關鍵欄位是否存在
                required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
                missing_fields = [field for field in required_fields if field not in cred_content]
                if missing_fields:
                    print(f"憑證檔案缺少必要欄位: {', '.join(missing_fields)}")
                    return None
                print(f"憑證檔案格式正確，項目 ID: {cred_content.get('project_id')}")
        except json.JSONDecodeError as json_e:
            print(f"憑證檔案不是有效的 JSON 格式: {json_e}")
            return None
        except Exception as read_e:
            print(f"讀取憑證檔案時出錯: {read_e}")
            return None
            
        # 設定 Google API 範圍
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/cloud-platform'
        ]
        
        # 建立認證
        try:
            creds = Credentials.from_service_account_file(credentials_path, scopes=scope)
            client = gspread.authorize(creds)
            
            # 測試連接
            try:
                spreadsheets = client.list_spreadsheet_files()
                print(f"成功連接到 Google API，找到 {len(spreadsheets)} 個試算表")
                return client
            except Exception as test_e:
                print(f"測試連接時出錯: {test_e}")
                import traceback
                print(f"錯誤詳情: {traceback.format_exc()}")
                return None
                
        except Exception as auth_e:
            print(f"授權 Google API 時出錯: {auth_e}")
            import traceback
            print(f"錯誤詳情: {traceback.format_exc()}")
            return None
            
    except Exception as e:
        print(f"連接 Google API 時發生未預期錯誤：{e}")
        import traceback
        print(f"錯誤堆疊: {traceback.format_exc()}")
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
        spreadsheet_url = "https://docs.google.com/spreadsheets/d/1I2GzYptiPvhN5dT3_qzVXlIAoPeI8S9MaTVzxfDVjrw/edit?gid=0#gid=0"
        spreadsheet_id = extract_spreadsheet_id(spreadsheet_url)
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

@app.route('/register', methods=['GET', 'POST'])
def register():
    """註冊帳號頁面"""
    if request.method == 'GET':
        return render_template('register.html')
    
    try:
        # 處理 POST 請求 (表單提交)
        data = request.form
        
        # 基本資料驗證
        required_fields = ['username', 'password', 'confirm_password', 'name', 'role']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'status': 'error',
                    'message': f'缺少必要欄位: {field}'
                }), 400
                
        # 密碼確認
        if data['password'] != data['confirm_password']:
            return jsonify({
                'status': 'error',
                'message': '兩次輸入的密碼不一致'
            }), 400
            
        # 學生必須填寫學號
        if data['role'] == 'student' and (not data.get('student_id') or not data['student_id']):
            return jsonify({
                'status': 'error',
                'message': '學生必須填寫學號'
            }), 400
            
        # 設定 Google Sheets 連接
        client = setup_google_connection()
        if client is None:
            return jsonify({
                'status': 'error',
                'message': '無法連接到 Google Sheets'
            }), 500
            
        # 從 URL 提取 spreadsheet ID
        spreadsheet_url = "https://docs.google.com/spreadsheets/d/1I2GzYptiPvhN5dT3_qzVXlIAoPeI8S9MaTVzxfDVjrw/edit?gid=0#gid=0"
        spreadsheet_id = extract_spreadsheet_id(spreadsheet_url)
        
        if not spreadsheet_id:
            return jsonify({
                'status': 'error',
                'message': '無效的試算表 URL'
            }), 500
            
        # 開啟試算表
        try:
            spreadsheet = client.open_by_key(spreadsheet_id)
            try:
                worksheet = spreadsheet.worksheet("帳密")
            except:
                worksheet = spreadsheet.sheet1
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'無法開啟試算表：{str(e)}'
            }), 500
            
        # 檢查使用者名稱是否已存在
        existing_usernames = worksheet.col_values(2)  # 假設使用者名稱在第2列
        if data['username'] in existing_usernames:
            return jsonify({
                'status': 'error',
                'message': '使用者名稱已存在'
            }), 400
            
        # 雜湊密碼
        import hashlib
        hashed_password = hashlib.sha256(data['password'].encode()).hexdigest()
        
        # 準備要寫入的資料
        values = [
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            data['username'],
            hashed_password,
            data['name'],
            data['role'],
            data.get('student_id', ''),
            data.get('extension', ''),
            data.get('email', '')
        ]
        
        # 寫入資料
        try:
            worksheet.append_row(values)
            return jsonify({
                'status': 'success',
                'message': '帳號申請成功！等待管理員審核。'
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'寫入資料時發生錯誤：{str(e)}'
            }), 500
            
    except Exception as e:
        print(f"處理註冊時發生錯誤：{str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'處理註冊時發生錯誤：{str(e)}'
        }), 500

@app.route('/form', methods=['GET'])
def form():
    """顯示評核表單頁面"""
    return render_template('form.html')

@app.route('/add_epa_form', methods=['POST'])
def add_epa_form():
    """處理EPA評核表單提交"""
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
        spreadsheet_url = DEFAULT_SPREADSHEET_URL  # 使用默認URL或從請求中獲取
        spreadsheet_id = extract_spreadsheet_id(spreadsheet_url)
        if not spreadsheet_id:
            return jsonify({
                'status': 'error',
                'message': '無效的試算表 URL'
            }), 500

        # 開啟試算表
        try:
            spreadsheet = client.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.worksheet("EPA評核")  # 嘗試使用特定的工作表
        except Exception as e:
            try:
                worksheet = spreadsheet.sheet1  # 如果找不到特定工作表，使用第一個
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
            data.get('epa_type', ''),  # 新增 EPA 類型欄位
            data.get('clinical_scenario', ''),
            data.get('student_epa_level', ''),
            data.get('patient_difficulty', ''),
            data.get('teacher_epa_level', ''),
            data.get('feedback', ''),
            data.get('teacher_name', '')  # 新增教師姓名欄位
        ]

        # 寫入資料
        try:
            worksheet.append_row(values)
            return jsonify({
                'status': 'success',
                'message': '評核資料已成功提交'
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'寫入資料時發生錯誤：{str(e)}'
            }), 500

    except Exception as e:
        print(f"提交評核表單時發生錯誤：{str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'處理評核表單時發生錯誤：{str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001) 