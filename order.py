import json
import os
import pandas as pd
import streamlit as st

# 嘗試引入 Google Sheets 套件，若失敗則給予提示
try:
    import gspread
    from google.oauth2.service_account import Credentials

    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False

# -------------------------------------------------------------
# 📊 Google Sheets 串接與訂單處理邏輯
# -------------------------------------------------------------
SPREADSHEET_NAME = "SW_RTA_Battle_Logs"


def get_gspread_client():
    """取得授權的 gspread client 物件 (內嵌完整 Service Account 憑證)"""
    if not GSPREAD_AVAILABLE:
        return None

    credentials_info = {
        "type": "service_account",
        "project_id": "api-project-139778228024",
        "private_key_id": "abc2629cd90b7541ff2574a7be85f83cc446e83d",
        "private_key": """-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQDJQK2Z2RLJdZNU
UpTo1kGC+F1/Y4di1O0EiN26NCQ+mV9rS9RHpo2s7SGf3Avvdp2l6GUw1oYgQo7c
WD/PqvCxK3EyyHOK3lVqqkQaVKQOVtgmTeTYI+8TIG4lTnnT7PU5zYUNtgF6ntMf
1Au3zU+6wio22+WYNjbf5mFrgI1PB01g0lr1GSkWmirVdTqdz/Ey/exGrl1wczAI
V53u1peLk+QTsfSSw0g7CJdJjdcOEcivl2OUgIAXLAqmiNib8GJZPTcqLsOR8Wuq
MIZ/5/0shGC4S2zxZHYNrNvWGkCW0ubiZmho5tF5XHr5YCay7djli8GI+rWOV02N
sZAkq3vXAgMBAAECggEAD+MMsT/rFT80Vaw9OBIt0r5zdwpu1hTz7u80/a1/DPgD
ic9PHybdOUDw7hMrWAh3knDBiDTvGp3WdDt9MhIO9RV2VqlvQY+ik4yEWsXCu6UM
ZB2zCoLvrQVa3JQQ1vN2Ok1oivgKrtjZ1sHg+O36tMX+Gh2KxtTEyTEBEMDxpsLL
Wef0tcRLAu/UxnreAHDjFJJe4J1Gev87kq+/DS+P7nMtt92xRVEywgh4gzDfZdJa
11ekbgDYiGFcwocRBO7wOoSnI5p3imTWfZA4rPmFO4xpP8eB7+RgoL0FJXei3Q/P
Cbn4NF7y477crZQlRAxMN+XDqEJQoGQXBbddiZEI5QKBgQD2jZ1UY4KtJN0gIudf
W5/Tl9ERDLOS10XljJUEhCe0sQMjb/ZdHO02wdBesa1WmMieDTbbPQe4Hb0k+Gqp
Qc0tukvZ9To06qHhx00b1FK1ggBigqDYHw+5VOZlQR88ayJwNr1PRMqf+GugtnYi
Q5es44mHv732dUaL/yi/M0yBcwKBgQDQ9rh+/8lDvrq0oZljDJp6adfY4HUbyVAy
nnKaH2oihScwyq7qLtSaybhlwv5e7lKU/CUcVu2OTb+A0yLk8yWbqObTjXf8ECLL6
9a5u8Nl7X1G0H86RyIrlMW6cqOIo0+Xmc2XnXn4OyCJjh63tkHADeL5ub02s4MSU
1XL0+EUzDQKBgDjqfixSAIOp4+YcSJ9Jzn6RKHEwJnA6g+c26duuCmB7EIdovE3I
ndLZUTZ7ek25PPNjHoidAUnzdWKGlOzIxf4UT4ZjCNJqso4w0bweCn0lJZn9XOnxJ
x154S+uJ+gT/kmanLFKVRdViCq6CEIleYzBFIqWUzOyNLCj7UVO6KuojAoGAYHvK
rDkGgRUruAN1g1pqaWM9mpHpAK9vLC9QZSHuPCqK8kqAk8lM2M4lSP3t3VrBAd4S
yGIBlC3v4+9aOEr2DegfMWxRN1ec7GtL40Wp5WEZpIWbJ4zlNPYiEIuaASf12vYl
czMaGVEnL7WSBULPtYqmwu75en09x0rXDW0k5nECgYBsVariZO9yHCpvf0uNgzlP
TNltl7Y2EXl/dd+BJaGs64168Hip2Go7EyQU/0okHpeu7lxnw+5xBxJxkjdIxc3t
1aHWH2HG/P8b3ApG37oo7c7EzyUMNvsnxu+bt0ud1xZ4HG0s05dBudvobVfkxRXX
KkjHCFGV1ZElxHJJpnTViQ==
-----END PRIVATE KEY-----""",
        "client_email": "order-216@api-project-139778228024.iam.gserviceaccount.com",
        "client_id": "117586942730597357800",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/order-216%40api-project-139778228024.iam.gserviceaccount.com",
        "universe_domain": "googleapis.com",
    }

    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_info(
            credentials_info, scopes=scopes
        )
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"⚠️ 建立憑證發生例外錯誤: {e}")
        return None


def process_order(df, sheet_name="Sheet1"):
    """處理訂單資料並安全寫入 Google Sheets"""
    if not GSPREAD_AVAILABLE:
        st.error("❌ 伺服器端尚未安裝 gspread 套件，無法進行 Google 試算表同步。")
        return

    client = get_gspread_client()
    if client is None:
        st.error("❌ 無法取得 Google Sheets 授權客戶端，請檢查憑證格式。")
        return

    try:
        sh = client.open(SPREADSHEET_NAME)
        try:
            worksheet = sh.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sh.add_worksheet(title=sheet_name, rows=100, cols=20)

        worksheet.clear()
        data_to_write = [df.columns.values.tolist()] + df.astype(
            str
        ).values.tolist()
        worksheet.update(data_to_write)

        st.success(
            f"✅ 成功將訂單資料寫入 Google Sheets [{SPREADSHEET_NAME} -> {sheet_name}]！"
        )

    except gspread.exceptions.SpreadsheetNotFound:
        st.error(
            f"❌ 找不到名稱為 `{SPREADSHEET_NAME}` 的 Google 試算表！\n"
            f"請確認您已將該試算表共用給：`order-216@api-project-139778228024.iam.gserviceaccount.com`"
        )
    except Exception as e:
        st.error(f"❌ 寫入 Google Sheets 時發生未預期錯誤: {e}")


# -------------------------------------------------------------
# 🖥️ Streamlit 畫面渲染 (確保有東西顯示，避免白畫面)
# -------------------------------------------------------------
st.title("📦 訂單管理與 Google Sheets 同步系統")

# 建立一個測試用的 DataFrame 確保畫面能正常運作
sample_data = {
    "訂單編號": ["ORD001", "ORD002"],
    "品項": ["招牌套餐", "特製飲品"],
    "數量": [2, 1],
}
df_test = pd.DataFrame(sample_data)

st.subheader("📋 目前測試訂單預覽")
st.dataframe(df_test)

if st.button("確認送出訂單並同步至 Google Sheets"):
    with st.spinner("正在同步至 Google Sheets..."):
        process_order(df_test, sheet_name="Orders")
