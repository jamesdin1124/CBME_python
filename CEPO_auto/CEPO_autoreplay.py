from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import SessionNotCreatedException
import sys

def setup_chrome_driver():
    """
    設置並返回 Chrome WebDriver 實例
    包含錯誤處理和版本檢查
    """
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    # 指定 Chrome 瀏覽器的路徑
    chrome_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    
    try:
        # 使用 ChromeDriverManager 自動下載對應版本的 ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("成功初始化 Chrome WebDriver")
        return driver
    except SessionNotCreatedException as e:
        print(f"ChromeDriver 初始化失敗：{str(e)}")
        raise
    except Exception as e:
        print(f"設置 Chrome WebDriver 時發生錯誤：{str(e)}")
        raise

# 初始化 WebDriver
driver = setup_chrome_driver()

try:
    # 前往登入頁面
    driver.get("https://cts.tsgh.ndmctsgh.edu.tw/")  # 請替換成實際的登入頁面網址
    
    # 等待帳號輸入框出現並填入帳號
    username_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "loginName"))
    )
    username_input.send_keys("DOC31060")
    
    # 等待密碼輸入框出現並填入密碼
    password_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "loginPin"))
    )
    password_input.send_keys("D!122080819")
    
    # 等待登入按鈕出現並點擊
    login_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.btn-primary.block.full-width.m-b.btn-lg"))
    )
    login_button.click()
    
    # 登入後自動偵測警告彈窗，若出現則點擊確認按鈕
    try:
        print("等待『表單提交完成!』訊息彈窗出現...", file=sys.stderr)
        # 先等彈窗可見，再等按鈕可點擊
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="body-container"]/div[14]/div[2]/div/div/div/div/div[4]/button'))
        )
        confirm_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="body-container"]/div[14]/div[2]/div/div/div/div/div[4]/button'))
        )
        confirm_btn.click()
        print("已自動點擊『表單提交完成!』訊息的確認按鈕")
        time.sleep(1)
    except Exception as confirm_error:
        print("自動點擊提交完成確認按鈕失敗：", str(confirm_error))
    

    # 點擊「待填表單」分頁
    try:
        # 等待「待填表單」分頁按鈕出現並點擊
        todo_form_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="go-tab-todoForm"]'))
        )
        todo_form_tab.click()
        print("已自動點擊『待填表單』分頁")
    except Exception as todo_tab_error:
        print("自動點擊『待填表單』分頁失敗：", str(todo_tab_error))

    # 匯入並呼叫夜間學習紀錄_縱貫組 handler
    try:
        from form_handlers.handle_night_study import handle_night_study
        handle_night_study(driver)
    except Exception as handler_error:
        print("呼叫夜間學習紀錄_縱貫組 handler 失敗：", str(handler_error))

except Exception as e:
    print(f"發生錯誤：{str(e)}")

finally:
    # 關閉瀏覽器
    driver.quit()



#（六年級）西醫實習醫學生（UGY）訓練計畫第二年_M119期班使用