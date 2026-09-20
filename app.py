import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import json
from PIL import Image
from google import genai

st.set_page_config(page_title="E-Commerce AI OS", layout="wide")
st.title("📦 E-Commerce Business & Finance Operating System")

# Database Setup
conn = sqlite3.connect("business_data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    vendor TEXT,
    item_name TEXT,
    quantity INTEGER,
    purchase_rate REAL,
    gst_percent REAL,
    total_amount REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    order_id TEXT,
    platform TEXT,
    item_name TEXT,
    quantity INTEGER,
    sale_price REAL,
    order_status TEXT,
    payment_status TEXT,
    amount_received REAL,
    pending_amount REAL
)
""")
conn.commit()

# Configuration (Sidebar)
st.sidebar.header("⚙️ Configuration")
gemini_api_key = st.secrets.get("GEMINI_API_KEY", "")
if not gemini_api_key:
    gemini_api_key = st.sidebar.text_input("Gemini API Key", type="password")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📸 AI Bill Scanner", 
    "🛒 Orders & Sales Tracker", 
    "📊 Month-End & GST Report", 
    "🚀 Marketing & Automation"
])

# 1. Bill Scanner
with tab1:
    st.subheader("Purchase Bill / Invoice Scanner")
    uploaded_file = st.file_uploader("Bill ki photo upload karo (JPG/PNG)", type=["jpg", "png", "jpeg"])

    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, caption="Uploaded Bill", width=300)

        if st.button("AI se Bill Scan Karo"):
            if not gemini_api_key:
                st.error("Pehle Sidebar ya Secrets me Gemini API Key enter karo!")
            else:
                try:
                    with st.spinner("AI bill ko read kar raha hai..."):
                        client = genai.Client(api_key=gemini_api_key)
                        prompt = """
                        Scan this bill/invoice and extract details in pure valid JSON without markdown:
                        {
                            "vendor": "Supplier Name",
                            "items": [
                                {
                                    "item_name": "Product Name",
                                    "quantity": 1,
                                    "purchase_rate": 0.0,
                                    "gst_percent": 0.0,
                                    "total_amount": 0.0
                                }
                            ]
                        }
                        """
                        response = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=[prompt, img]
                        )
                        cleaned_json = response.text.replace("```json", "").replace("```", "").strip()
                        data = json.loads(cleaned_json)
                        today = datetime.today().strftime('%Y-%m-%d')
                        for item in data.get("items", []):
                            cursor.execute("""
                            INSERT INTO purchases (date, vendor, item_name, quantity, purchase_rate, gst_percent, total_amount)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (
                                today, 
                                data.get("vendor", "Direct"), 
                                item.get("item_name"), 
                                item.get("quantity", 1), 
                                item.get("purchase_rate", 0), 
                                item.get("gst_percent", 0), 
                                item.get("total_amount", 0)
                            ))
                        conn.commit()
                        st.success("✅ Bill successfully scan hokar database me save ho gaya!")
                        st.json(data)
                except Exception as e:
                    st.error(f"Error: {e}")

    st.write("---")
    st.subheader("Stock Purchase History")
    df_purchases = pd.read_sql_query("SELECT * FROM purchases ORDER BY id DESC", conn)
    st.dataframe(df_purchases, use_container_width=True)

# 2. Orders Tracker
with tab2:
    st.subheader("Naya Order Entry & Tracking")
    with st.form("new_order_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            order_id = st.text_input("Order ID")
            platform = st.selectbox("Platform", ["Instagram/Direct", "Meesho", "Flipkart", "Amazon", "Website"])
            item_name = st.text_input("Product Name")
        with col2:
            quantity = st.number_input("Quantity", min_value=1, value=1)
            sale_price = st.number_input("Total Sale Price (₹)", min_value=0.0, step=50.0)
            order_status = st.selectbox("Order Status", ["Delivered", "Hold / RTO Pending", "Dispatched", "Pending"])
        with col3:
            payment_status = st.selectbox("Payment Status", ["Received", "Pending", "Partial"])
            amount_received = st.number_input("Amount Received (₹)", min_value=0.0, step=50.0)
            pending_amount = sale_price - amount_received

        submit_order = st.form_submit_button("Order Save Karo")
        if submit_order:
            today = datetime.today().strftime('%Y-%m-%d')
            cursor.execute("""
            INSERT INTO orders (date, order_id, platform, item_name, quantity, sale_price, order_status, payment_status, amount_received, pending_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (today, order_id, platform, item_name, quantity, sale_price, order_status, payment_status, amount_received, pending_amount))
            conn.commit()
            st.success("✅ Order save ho gaya!")

    st.write("---")
    st.subheader("All Orders")
    df_orders = pd.read_sql_query("SELECT * FROM orders ORDER BY id DESC", conn)
    st.dataframe(df_orders, use_container_width=True)

# 3. Reports
with tab3:
    st.subheader("📈 Month-End Business Performance")
    total_purchases = cursor.execute("SELECT SUM(total_amount) FROM purchases").fetchone()[0] or 0.0
    total_sales = cursor.execute("SELECT SUM(sale_price) FROM orders WHERE order_status != 'Cancelled'").fetchone()[0] or 0.0
    total_received = cursor.execute("SELECT SUM(amount_received) FROM orders").fetchone()[0] or 0.0
    total_pending = cursor.execute("SELECT SUM(pending_amount) FROM orders WHERE payment_status != 'Received'").fetchone()[0] or 0.0
    
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Total Sales", f"₹{total_sales:,.2f}")
    col_m2.metric("Total Purchases", f"₹{total_purchases:,.2f}")
    col_m3.metric("Paisa Aa Gaya", f"₹{total_received:,.2f}")
    col_m4.metric("Pending / Hold Paisa", f"₹{total_pending:,.2f}")

    gross_profit = total_sales - total_purchases
    st.info(f"💰 **Net Gross Profit:** ₹{gross_profit:,.2f}")

    if not df_orders.empty:
        st.write("---")
        st.subheader("Platform Breakdown")
        st.bar_chart(df_orders["platform"].value_counts())

# 4. Marketing Blueprint
with tab4:
    st.subheader("🤖 Marketing & Auto DM Blueprint")
    st.markdown("""
    - **Instagram Auto DM:** ManyChat integrate karke keyword comments ("Price", "Link") par automated DM send karein.
    - **WhatsApp Automation:** Interakt ya Wati ke sath order confirmation aur hold tracking auto-messages set karein.
    """)
            
