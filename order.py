import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import os
import json

# --- 頁面設定 ---
st.set_page_config(page_title="Moos Beef - 線上點餐系統", page_icon="🥩")

# (CSS 與 UI 設定部分維持不變，請保留你原有的 CSS)

# --- 核心模組：環境兼容認證 ---


def get_gspread_client():
    """
    自動判斷環境並返回 gspread client。
    優先使用 Streamlit Secrets (雲端)，否則使用本地 JSON 檔案。
    """
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    # 判斷是否為雲端環境 (透過檢查 st.secrets 是否存在)
    if "gcp_service_account" in st.secrets:
        # 從 Streamlit Cloud 的 Secrets 讀取 (格式為 JSON 字串)
        creds_dict = json.loads(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            creds_dict, scope)
    else:
        # 從本地檔案讀取
        json_path = r"C:\Users\user\Desktop\python\billing\billing.json"
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"找不到本地金鑰檔案：{json_path}")
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            json_path, scope)

    return gspread.authorize(creds)


# --- 訂單確認按鈕 ---
if st.button("確認送出訂單", type="primary", use_container_width=True):
    if not customer_name or total_price == 0:
        st.warning("請檢查訂單內容與稱呼！")
    else:
        with st.spinner("正在連線至 Google 試算表..."):
            try:
                # 取得認證 client
                client = get_gspread_client()

                # 開啟試算表
                sheet = client.open_by_key(
                    '17vqVq5tPUma1ywFWvGPK4Y5R54o5MVL0ZkXbDmg0IVI').sheet1

                # 寫入資料
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                sheet.append_row(
                    [now, customer_name, str(selected_orders), total_price])

                st.balloons()
                st.success("訂單已成功送出！")

            except Exception as e:
                st.error(f"系統錯誤: {e}")
