import os
import json

# 確保 .streamlit 目錄存在
os.makedirs('.streamlit', exist_ok=True)

# 建立正確格式的 secrets.toml 檔案
with open('.streamlit/secrets.toml', 'w') as f:
    f.write('''[gcp_service_account]
type = "service_account"
project_id = "tsghcbme"
private_key_id = "63c8f408314197b279090554cb04aa3dc7ccc9e7"
private_key = """-----BEGIN PRIVATE KEY-----
MIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQDPChi1qApnaCRn
EFbbHratAMsou0KSUrQfZIJxtsPxsms5RA+z9NjcO/93wBq2GWSehUEuu0B9gO8A
B+1SVuyFXZzjuBy5riz/qggX7Idtvi3WRy3KgBAu0OsTMzdAEoJDBZL4fBSstmhw
Q7S/rLNvY8qQARz2YjgNlph7SVKOjmlO92tjCuGPUnTLGyX/dbv8nq/XsvmhNh9v
mMwvZbFKjDjqLU+fduL4GJi4Qm3KL3j2ndS0HkXCeWm2bQRnfn8ZclJ6p+LGFIWZ
Kbv2rJca4t+IhjnWpGipHdbIrZrHFx2BLC2ZR67Fhdw7l9RE77/DfKglkc9aQZgH
qwEQCZWPAgMBAAECggEADmCOHLdBmbKyrHGHBopYdyUR9o8ibVTO60sof8sISlVw
eraOPJnpIUoNUHyHnlOfGB76ysr4DH8SmbbzNP+SRyScC3gyjnZY65wcGcU0FlvZ
hQLGXESOWyHo4RlyYcGnSA4wCY9cRC4ajIk3GQReJYMRgvSA1V82s0Lc7drGn92F
1QB1fDTE7viYXxFuPqQMN0m0nEXWncWThtTK0yGvE1tnjyxgJxnH6yhg0WBGAfQR
Y/h0ZRB5fCR4ayF18njU4+sho/+0XWRW0KfQjdw0blVWIHFwgBZKTccIuDaAwKWK
w397Hf4OhiEl2KqPKliUApn5lAd3nG90GMw3RwPRGQKBgQDvS0fyoSmRFpnqc9u9
qdSpv54YCa6Sly3Ze7CC4X+cY8x9jyoVof5KEj4uSDTqc01chs+bJ/zF1OgSQu/Z
R30gkUjoa/EqKAEIxeN5yfQjdPN/bioG8bzefYgF1f7BtqpPuGEjJmL6VhMHTkK+
bqmkTxeErK8O7gezEtGGaPR3MwKBgQDdflpy0EQj4Pst04SiqcPJUVBAKpTrI6wP
en+8AU/g+qKKxzAKX+oq7gyX5xNXc1eZ0aKqaimRqzGR+ZlYlHVIcGwnOThql2Yb
9fI1B7h92wyoD5WUESE7TVEpXHq0b6RbbE1XNI6cdjeZtHB9O3wIQ0nYtsJ7zTMr
pnlI+D94NQKBgQCZe0ybd/lEQR3ZvhQcM3jeo7PQMS2Sgnr6+pW9bMs/0NcRVakl
lPCYK9lMMC4Yjnn5NdKk7uH3NdbgF6TlVTARmn4L7WgSpPP834hGzlzT/ShM/Kji
KVz9y8BaFea/8tyMI3PSasWjUWAFGJJAuJQAemZYR7ZEujGgDxrqvhjG9wKBgQDE
ldvDYZPI4GsvLjffg5uQ98mpWeHYnU2eY1Qx0lxKS0musMGzw5N7zNKClAY3rNjI
Xibo59bDQlV5wTXYR9OcmqNzYLbw7DUlhfIWHScjFSMzmrlgtJ9xGdt6QWlq8lfH
COXQC4az2bzZgCwDCqO4VbiaTwNojCTpjhTBrgvvLQKBgQC7tRXPvSry0FHfkSTK
XBZNmHWXjk6YeZZewPKnPukqjxO9n0VRwhW3ArPQJCwcIonTJwojSFEBH9IeYH6n
pZOFK5bBDzth7uX0nke/OtYNAqHBPnXB52WE6lYgWxpsuyFykuTAoMMBWg8rl7dZ
SzxiOkz4VS2c2RvPcUtD/eHqjQ==
-----END PRIVATE KEY-----"""
client_email = "tsghcbme@tsghcbme.iam.gserviceaccount.com"
client_id = "105277885772518514331"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/tsghcbme%40tsghcbme.iam.gserviceaccount.com"
universe_domain = "googleapis.com"
''')