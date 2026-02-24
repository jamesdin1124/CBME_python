import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd
import time
import os
import ssl
import certifi
import pyperclip

# 設定 SSL 證書
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
ssl._create_default_https_context = ssl._create_unverified_context

def google_login_and_fetch(email, password, sheet_urls):
    """
    登入 Google 並抓取試算表資料
    """
    try:
        # 初始化瀏覽器選項
        options = uc.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        
        print("初始化瀏覽器...")
        driver = uc.Chrome(options=options, suppress_welcome=True)
        
        # 登入 Google
        print("開啟登入頁面...")
        driver.get("https://accounts.google.com/signin")
        time.sleep(5)
        
        try:
            # 輸入郵箱
            print("輸入郵箱...")
            email_input = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "identifierId"))
            )
            email_input.clear()
            email_input.send_keys(email + "@gmail.com")
            time.sleep(2)
            email_input.send_keys(Keys.RETURN)
            time.sleep(3)
            
            # 輸入密碼
            print("輸入密碼...")
            password_input = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            password_input.clear()
            password_input.send_keys(password)
            time.sleep(2)
            password_input.send_keys(Keys.RETURN)
            time.sleep(5)
            
            print("登入完成，開始處理試算表...")
            
            # 處理每個試算表
            for url in sheet_urls:
                try:
                    print(f"\n開始處理試算表：{url}")
                    driver.get(url)
                    time.sleep(8)  # 等待試算表完全載入
                    
                    # 等待表格元素出現
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "grid-container"))
                    )
                    
                    # 全選資料
                    print("複製資料中...")
                    actions = ActionChains(driver)
                    actions.key_down(Keys.CONTROL)
                    actions.send_keys('a')
                    actions.key_up(Keys.CONTROL)
                    actions.perform()
                    time.sleep(2)
                    
                    # 複製
                    actions = ActionChains(driver)
                    actions.key_down(Keys.CONTROL)
                    actions.send_keys('c')
                    actions.key_up(Keys.CONTROL)
                    actions.perform()
                    time.sleep(2)
                    
                    # 從剪貼簿獲取資料
                    data = pyperclip.paste()
                    
                    # 獲取試算表標題
                    title = driver.title.replace(' - Google 試算表', '')
                    output_file = f"{title}.xlsx"
                    
                    # 將資料轉換為 DataFrame
                    print("處理資料中...")
                    rows = [row.split('\t') for row in data.split('\n') if row.strip()]
                    if rows:
                        df = pd.DataFrame(rows[1:], columns=rows[0])
                        
                        # 儲存為 Excel
                        df.to_excel(output_file, index=False)
                        print(f'已成功將「{title}」儲存為 {output_file}')
                    else:
                        print("未能獲取到資料")
                    
                except Exception as e:
                    print(f'處理試算表時發生錯誤：{str(e)}')
                    continue
            
            print("\n所有試算表處理完成！")
            input("按 Enter 鍵結束程式...")
            
        except Exception as e:
            print(f"登入過程發生錯誤：{str(e)}")
            input("請手動操作完成登入，完成後按 Enter 繼續...")
        
    except Exception as e:
        print(f"瀏覽器初始化錯誤：{str(e)}")
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == '__main__':
    # 設定登入資訊
    EMAIL = "jamesdin1124"
    PASSWORD = "Jamesdin1002"
    
    # 設定試算表網址
    SHEET_URLS = [
        'https://docs.google.com/spreadsheets/d/1mFyF4PTiA-5n_19MpXOcpxlmS9cjB3aCTsquqdbpVsA/edit?resourcekey=&gid=400927580#gid=400927580'
    ]
    
    google_login_and_fetch(EMAIL, PASSWORD, SHEET_URLS) 