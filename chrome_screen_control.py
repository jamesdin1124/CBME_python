import pyautogui
import time
import pandas as pd
import subprocess
import os
import platform
import re

# 設定儲存路徑
SAVE_PATH = '/Users/mbpr/Library/Mobile Documents/com~apple~CloudDocs/教學型主治醫師  訓練官/CBME_python/CBME Resident'

# 確保儲存路徑存在
os.makedirs(SAVE_PATH, exist_ok=True)

# 設定 pyautogui 的安全設定
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 1

def get_active_window_title():
    """
    獲取當前視窗標題
    """
    if platform.system() == 'Darwin':
        try:
            cmd = """
                osascript -e 'tell application "Google Chrome"
                    get title of active tab of front window
                end tell'
            """
            result = subprocess.check_output(cmd, shell=True).decode().strip()
            return result
        except:
            return None
    return None

def sanitize_filename(filename):
    """
    清理檔案名稱，移除不合法字元
    """
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = filename.strip('. ')
    return filename if filename else 'spreadsheet_data'

def open_chrome_with_url(url):
    """
    根據作業系統開啟 Chrome 並訪問指定網址
    """
    try:
        if platform.system() == 'Darwin':  # macOS
            subprocess.Popen(['open', '-a', 'Google Chrome', url])
            print("開啟 Chrome...")
        elif platform.system() == 'Windows':
            chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            subprocess.Popen([chrome_path, url, '--start-maximized'])
            print("開啟 Chrome...")
        
        time.sleep(3)
        return True
        
    except Exception as e:
        print(f"開啟 Chrome 時發生錯誤：{str(e)}")
        return False

def google_login(email, password):
    """
    執行 Google 登入
    """
    try:
        time.sleep(5)
        
        print("輸入郵箱...")
        pyautogui.write(email + "@gmail.com")
        time.sleep(1)
        pyautogui.press('return')
        time.sleep(3)
        
        print("輸入密碼...")
        pyautogui.write(password)
        time.sleep(1)
        pyautogui.press('return')
        time.sleep(5)
        
        print("登入完成")
        return True
        
    except Exception as e:
        print(f"登入過程發生錯誤：{str(e)}")
        return False

def copy_sheet_data():
    """
    複製試算表資料並獲取標題
    """
    try:
        time.sleep(8)  # 等待試算表載入
        
        # 獲取試算表標題
        sheet_title = get_active_window_title()
        if sheet_title:
            sheet_title = sheet_title.replace(' - Google 試算表', '')
        
        # 全選
        print("全選資料...")
        if platform.system() == 'Darwin':
            pyautogui.hotkey('command', 'a')
        else:
            pyautogui.hotkey('ctrl', 'a')
        time.sleep(2)
        
        # 複製
        print("複製資料...")
        if platform.system() == 'Darwin':
            pyautogui.hotkey('command', 'c')
        else:
            pyautogui.hotkey('ctrl', 'c')
        time.sleep(2)
        
        return sheet_title
        
    except Exception as e:
        print(f"複製資料時發生錯誤：{str(e)}")
        return None

def main():
    EMAIL = "jamesdin1124"
    PASSWORD = "Jamesdin1002"
    SHEET_URL = 'https://docs.google.com/spreadsheets/d/1mFyF4PTiA-5n_19MpXOcpxlmS9cjB3aCTsquqdbpVsA/edit?resourcekey=&gid=400927580#gid=400927580'
    
    try:
        if not open_chrome_with_url("https://accounts.google.com/signin"):
            return
        
        if not google_login(EMAIL, PASSWORD):
            return
        
        print("開啟試算表...")
        if not open_chrome_with_url(SHEET_URL):
            return
        
        # 複製資料並獲取標題
        sheet_title = copy_sheet_data()
        if not sheet_title:
            sheet_title = "試算表資料"
        
        # 清理檔案名稱
        safe_title = sanitize_filename(sheet_title)
        
        # 從剪貼簿獲取資料並處理
        import pyperclip
        data = pyperclip.paste()
        
        print("處理資料中...")
        rows = [row.split('\t') for row in data.split('\n') if row.strip()]
        if rows:
            df = pd.DataFrame(rows[1:], columns=rows[0])
            
            # 使用完整路徑儲存檔案
            output_file = os.path.join(SAVE_PATH, f"{safe_title}.xlsx")
            
            # 檢查檔案是否已存在
            counter = 1
            base_name = os.path.splitext(output_file)[0]
            extension = os.path.splitext(output_file)[1]
            while os.path.exists(output_file):
                output_file = f"{base_name}_{counter}{extension}"
                counter += 1
            
            # 儲存檔案
            df.to_excel(output_file, index=False)
            print(f'已成功儲存為 {output_file}')
            
            # 在 Mac 中開啟檔案位置
            if platform.system() == 'Darwin':
                subprocess.run(['open', '-R', output_file])
                
            # 顯示檔案的完整路徑
            print(f"\n檔案儲存位置：{output_file}")
        else:
            print("未能獲取到資料")
        
    except Exception as e:
        print(f"執行過程發生錯誤：{str(e)}")
    
    finally:
        input("按 Enter 鍵結束程式...")

if __name__ == '__main__':
    # 檢查儲存路徑
    if not os.path.exists(SAVE_PATH):
        print(f"正在建立儲存路徑：{SAVE_PATH}")
        try:
            os.makedirs(SAVE_PATH)
            print("儲存路徑建立成功")
        except Exception as e:
            print(f"建立儲存路徑時發生錯誤：{str(e)}")
            exit(1)
    
    print(f"目前作業系統：{platform.system()}")
    print(f"檔案將儲存至：{SAVE_PATH}")
    
    # 確認是否繼續
    response = input("請確認儲存位置是否正確 (y/n)? ")
    if response.lower() != 'y':
        print("程式已取消")
        exit(0)
    
    main() 