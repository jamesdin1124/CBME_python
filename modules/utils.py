import re

def extract_spreadsheet_id(url):
    """從 Google 試算表 URL 中提取 spreadsheet ID"""
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
    return match.group(1) if match else None

def extract_gid(url):
    """從 Google 試算表 URL 中提取 gid"""
    match = re.search(r'gid=(\d+)', url)
    return int(match.group(1)) if match else None 