import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import os
import json

# --- 頁面設定 ---
st.set_page_config(page_title="Moos Beef - 線上點餐系統", page_icon="🥩")

# --- 自訂 CSS (簡潔米白色風格) ---
st.markdown("""
    <style>
        .stApp { background-color: #FDFBF7; color: #333; }
        h1, h3 { color: #8B4513 !important; text-align: center; }
        .restaurant-info { text-align: center; color: #555; font-size: 14px; margin-bottom: 20px; }
        
        .menu-card {
            background-color: #FFFFFF; 
            border-bottom: 1px solid #E0D8C3;
            padding: 10px 0px; 
            margin-bottom: 10px;
        }
        .item-name { font-size: 16px; font-weight: bold; color: #222; }
        .item-desc { font-size: 11px; color: #666; margin-bottom: 3px; }
        .item-price { font-size: 15px; font-weight: bold; color: #8B4513; }
    </style>
""", unsafe_allow_html=True)

# --- 彈出視窗：查看食物原圖 ---


@st.dialog("食物原圖")
def show_full_image(img_path):
    st.image(img_path, use_container_width=True)


# --- 頁面 Header ---
st.markdown("<h1>Moos Beef</h1>", unsafe_allow_html=True)
st.markdown("<div class='restaurant-info'>地址：尖沙咀重慶大廈地庫 S30 號舖</div>",
            unsafe_allow_html=True)
st.markdown("---")

# --- 完整菜單資料庫 ---
MENU_ITEMS = [
    {"id": "A1", "name": "Triple Beef (120g) w/Rice",
     "desc": "Beef Sirloin, Beef Chuck Flap, Hanging Tender", "price": 138, "img": "A1.jpg"},
    {"id": "A2", "name": "Herb Roasted Beef Sirloin (70g) w/ Rice",
     "desc": "Herb Roasted Beef Sirloin", "price": 78, "img": "A2.jpg"},
    {"id": "A3", "name": "Slow Roasted Beef Chuck Flap (70g) w/ Rice",
     "desc": "Slow Roasted Beef Chuck Flap", "price": 75, "img": "A3.jpg"},
    {"id": "A4", "name": "Roast Beef Hanging Tender (70g) w/ Rice",
     "desc": "Roast Beef Hanging Tender", "price": 80, "img": "A4.jpg"},
    {"id": "A5", "name": "Double Beef w/ Rice",
        "desc": "Braised Beef Cheek, Braised Beef Tongue and Onsen Egg", "price": 88, "img": "A5.jpg"},
    {"id": "A6", "name": "Braised Beef Tongue w/ Rice",
        "desc": "Braised Beef Tongue", "price": 72, "img": "A6.jpg"}
]

selected_orders = {}
total_price = 0

# --- 渲染菜單介面 ---
for item in MENU_ITEMS:
    st.markdown(f"<div class='menu-card'>", unsafe_allow_html=True)
    col_img, col_info = st.columns([2, 3])

    with col_img:
        img_path = os.path.join("static", item["img"])
        if os.path.exists(img_path):
            st.image(img_path, width=120)
            if st.button("🔍 查看原圖", key=f"zoom_{item['id']}"):
                show_full_image(img_path)
        else:
            st.warning("無圖")

    with col_info:
        st.markdown(
            f"<div class='item-name'>{item['id']}. {item['name']}</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='item-desc'>{item['desc']}</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='item-price'>${item['price']}</div>", unsafe_allow_html=True)

        qty = st.number_input(f"數量 {item['id']}", min_value=0, max_value=10,
                              value=0, key=f"qty_{item['id']}", label_visibility="collapsed")
        if qty > 0:
            selected_orders[item['id']] = {
                "name": item['name'], "price": item['price'], "qty": qty}
            total_price += item['price'] * qty

    st.markdown(f"</div>", unsafe_allow_html=True)

# --- 結帳與加購區 ---
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    add_drink = st.checkbox("+$6 配飲品")
with col2:
    add_egg = st.checkbox("+$10 配溫泉蛋")

if add_drink:
    total_price += 6
if add_egg:
    total_price += 10

st.markdown(
    f"<h3 style='text-align: left; color: #8B4513;'>總金額：${total_price}</h3>", unsafe_allow_html=True)
customer_name = st.text_input("客人稱呼 / 桌號 (必填)")

# --- 核心模組：修復型態錯誤的環境兼容認證 ---


def get_gspread_client():
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    # 檢查是否有設定雲端 secrets
    if hasattr(st, "secrets") and "gcp_service_account" in st.secrets:
        raw_secret = st.secrets["gcp_service_account"]
        # 如果是 AttrDict 或 dict，直接轉成 dict 處理；如果是字串才用 json.loads
        if isinstance(raw_secret, str):
            creds_dict = json.loads(raw_secret)
        else:
            creds_dict = dict(raw_secret)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            creds_dict, scope)
    else:
        # 本地端直接讀取檔案
        json_path = r"C:\Users\user\Desktop\python\billing\billing.json"
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"找不到本地金鑰檔案：{json_path}")
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            json_path, scope)

    return gspread.authorize(creds)


# --- 訂單確認與送出按鈕 ---
if st.button("確認送出訂單", type="primary", use_container_width=True):
    if not customer_name or total_price == 0:
        st.warning("請檢查訂單內容與稱呼！")
    else:
        with st.spinner("正在連線至 Google 試算表，請稍候..."):
            try:
                client = get_gspread_client()
                sheet = client.open_by_key(
                    '17vqVq5tPUma1ywFWvGPK4Y5R54o5MVL0ZkXbDmg0IVI').sheet1

                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                sheet.append_row(
                    [now, customer_name, str(selected_orders), total_price])

                st.balloons()
                st.success("訂單已成功送出！")

            except Exception as e:
                st.error(f"系統錯誤: {e}")
