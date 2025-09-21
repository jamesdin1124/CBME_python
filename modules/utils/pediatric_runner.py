#!/usr/bin/env python3
"""
小兒部住院醫師評核系統啟動腳本
"""

import subprocess
import sys
import os

def main():
    """啟動小兒部評核系統"""
    print("🏥 小兒部住院醫師評核系統")
    print("=" * 50)
    
    # 檢查當前目錄
    current_dir = os.getcwd()
    print(f"當前目錄: {current_dir}")
    
    # 檢查必要檔案
    required_files = [
        "new_dashboard.py",
        "pediatric_evaluation.py",
        ".streamlit/secrets.toml"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ 缺少必要檔案:")
        for file in missing_files:
            print(f"   - {file}")
        print("\n請確保所有必要檔案都存在後再執行。")
        return False
    
    print("✅ 所有必要檔案都存在")
    
    # 檢查Python版本
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("❌ 需要Python 3.8或更高版本")
        return False
    
    print(f"✅ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 啟動Streamlit應用
    print("\n🚀 正在啟動小兒部評核系統...")
    print("系統將在瀏覽器中自動開啟")
    print("如果沒有自動開啟，請手動前往: http://localhost:8501")
    print("\n按 Ctrl+C 停止系統")
    print("=" * 50)
    
    try:
        # 啟動Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "new_dashboard.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n\n👋 系統已停止")
    except Exception as e:
        print(f"\n❌ 啟動失敗: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
