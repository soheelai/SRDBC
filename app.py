import io
import json
import sqlite3
from datetime import datetime
from google import genai
import pandas as pd
from PIL import Image
import streamlit as st

st.set_page_config(
    page_title="E-Commerce AI Master ERP",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

conn = sqlite3.connect("business_data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS master_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_timestamp TEXT,
    doc_type TEXT,
    marketplace TEXT,
    order_no TEXT,
    sub_order_no TEXT,
    invoice_no TEXT,
    order_date TEXT,
    invoice_date TEXT,
    courier_name TEXT,
    tracking_awb TEXT,
    routing_code TEXT,
    customer_name TEXT,
    customer_phone TEXT,
    customer_address TEXT,
    customer_city TEXT,
    customer_state TEXT,
    customer_pincode TEXT,
    return_seller_name TEXT,
    return_address TEXT,
    seller_gstin TEXT,
    seller_enrolment TEXT,
    sku TEXT,
    product_name TEXT,
    size TEXT,
    color TEXT,
    quantity INTEGER,
    gross_amount REAL,
    discount REAL,
    taxable_amount REAL,
    gst_rate REAL,
    cgst REAL,
    sgst REAL,
    igst REAL,
    tcs_amount REAL,
    shipping_charges REAL,
    other_charges REAL,
    total_invoice_amount REAL,
    payment_mode TEXT,
    order_status TEXT,
    notes TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    vendor TEXT,
    item_name TEXT,
    sku TEXT,
    quantity INTEGER,
    purchase_rate REAL,
    gst_percent REAL,
    total_amount REAL,
    notes TEXT
)
""")
conn.commit()

st.sidebar.title("⚙️ Setup & Settings")
gemini_api_key = st.secrets.get("GEMINI_API_KEY", "")
if not gemini_api_key:
    gemini_api_key = st.sidebar.text_input("Gemini API Key", type="password")

menu = st.sidebar.radio(
    "Navigation",
    [
        "📸 100% Detail AI Scanner",
        "📋 Orders Master Excel Sheet",
        "📦 Purchase & Stock Entry",
        "📊 Profit, GST & Audit Report",
    ],
)

if menu == "📸 100% Detail AI Scanner":
    st.title("📸 AI Smart Document & Label Scanner")
    st.caption("Shipping Label ya Invoice ki photo dalo — AI har ek single field accurately read karega!")

    col1, col2 = st.columns([1, 1])

    with col1:
        uploaded_file = st.file_uploader("Upload Image (JPG/PNG)", type=["jpg", "png", "jpeg"])
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Preview", use_container_width=True)

    with col2:
        if uploaded_file:
            scan_btn = st.button("⚡ Puri Details Extract Karo", use_container_width=True)
            if scan_btn:
                if not gemini_api_key:
                    st.error("Sidebar me API Key dalein!")
                else:
                    try:
                        with st.spinner("AI document se ek-ek detail read kar raha hai..."):
                            client = genai.Client(api_key=gemini_api_key)

                            prompt = """
Extract all shipping label and invoice details from this image in strict JSON format:
{
    "doc_type": "Shipping Label",
    "marketplace": "Meesho",
    "order_no": "",
    "sub_order_no": "",
    "invoice_no": "",
    "order_date": "",
    "invoice_date": "",
    "courier_name": "",
    "tracking_awb": "",
    "routing_code": "",
    "customer_name": "",
    "customer_phone": "",
    "customer_address": "",
    "customer_city": "",
    "customer_state": "",
    "customer_pincode": "",
    "return_seller_name": "",
    "return_address": "",
    "seller_gstin": "",
    "seller_enrolment": "",
    "sku": "",
    "product_name": "",
    "size": "",
    "color": "",
    "quantity": 1,
    "gross_amount": 0.0,
    "discount": 0.0,
    "taxable_amount": 0.0,
    "gst_rate": 0.0,
    "cgst": 0.0,
    "sgst": 0.0,
    "igst": 0.0,
    "tcs_amount": 0.0,
    "shipping_charges": 0.0,
    "other_charges": 0.0,
    "total_invoice_amount": 0.0,
    "payment_mode": "Prepaid",
    "notes": ""
}
All amounts must be numbers. Return ONLY pure raw JSON without markdown markers or backticks.
"""
                            response = client.models.generate_content(
                                model="gemini-2.5-flash",
                                contents=[prompt, image]
                            )

                            cleaned = response.text.strip()
                            if cleaned.startswith("```json"):
                                cleaned = cleaned[7:]
                            if cleaned.startswith("```"):
                                cleaned = cleaned[3:]
                            if cleaned.endswith("```"):
                                cleaned = cleaned[:-3]
                            data = json.loads(cleaned.strip())

                            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            cursor.execute("""
                            INSERT INTO master_orders (
                                scan_timestamp, doc_type, marketplace, order_no, sub_order_no, invoice_no,
                                order_date, invoice_date, courier_name, tracking_awb, routing_code,
                                customer_name, customer_phone, customer_address, customer_city, customer_state, customer_pincode,
                                return_seller_name, return_address, seller_gstin, seller_enrolment,
                                sku, product_name, size, color, quantity, gross_amount, discount,
                                taxable_amount, gst_rate, cgst, sgst, igst, tcs_amount, shipping_charges, other_charges,
                                total_invoice_amount, payment_mode, order_status, notes
                            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                            """, (
                                now_str,
                                str(data.get("doc_type", "")),
                                str(data.get("marketplace", "")),
                                str(data.get("order_no", "")),
                                str(data.get("sub_order_no", "")),
                                str(data.get("invoice_no", "")),
                                str(data.get("order_date", "")),
                                str(data.get("invoice_date", "")),
                                str(data.get("courier_name", "")),
                                str(data.get("tracking_awb", "")),
                                str(data.get("routing_code", "")),
                                str(data.get("customer_name", "")),
                                str(data.get("customer_phone", "")),
                                str(data.get("customer_address", "")),
                                str(data.get("customer_city", "")),
                                str(data.get("customer_state", "")),
                                str(data.get("customer_pincode", "")),
                                str(data.get("return_seller_name", "")),
                                str(data.get("return_address", "")),
                                str(data.get("seller_gstin", "")),
                                str(data.get("seller_enrolment", "")),
                                str(data.get("sku", "")),
                                str(data.get("product_name", "")),
                                str(data.get("size", "")),
                                str(data.get("color", "")),
                                int(data.get("quantity", 1) or 1),
                                float(data.get("gross_amount", 0.0) or 0.0),
                                float(data.get("discount", 0.0) or 0.0),
                                float(data.get("taxable_amount", 0.0) or 0.0),
                                float(data.get("gst_rate", 0.0) or 0.0),
                                float(data.get("cgst", 0.0) or 0.0),
                                float(data.get("sgst", 0.0) or 0.0),
                                float(data.get("igst", 0.0) or 0.0),
                                float(data.get("tcs_amount", 0.0) or 0.0),
                                float(data.get("shipping_charges", 0.0) or 0.0),
                                float(data.get("other_charges", 0.0) or 0.0),
                                float(data.get("total_invoice_amount", 0.0) or 0.0),
                                str(data.get("payment_mode", "Prepaid")),
                                "Dispatched",
                                str(data.get("notes", ""))
                            ))
                            conn.commit()

                            st.success("✅ Saari details successfully lock ho gayi!")
                            m1, m2, m3 = st.columns(3)
                            m1.metric("Order ID", data.get("order_no", "-"))
                            m2.metric("AWB / Tracking", data.get("tracking_awb", "-"))
                            m3.metric("Total Amount", f"₹{data.get('total_invoice_amount', 0.0)}")

                            with st.expander("👁️ Full Extracted Data Dekhein", expanded=True):
                                st.json(data)
                    except Exception as e:
                        st.error(f"Error: {e}")

elif menu == "📋 Orders Master Excel Sheet":
    st.title("📋 Master Orders Sheet")
    df_orders = pd.read_sql_query("SELECT * FROM master_orders ORDER BY id DESC", conn)

    if not df_orders.empty:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df_orders.to_excel(writer, index=False, sheet_name="Master_Orders")
        buffer.seek(0)

        st.download_button(
            label="📥 Download Master Excel Sheet (.xlsx)",
            data=buffer,
            file_name=f"ECom_Orders_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
        st.dataframe(df_orders, use_container_width=True)
    else:
        st.info("Abhi tak koi record scan nahi hua hai.")

elif menu == "📦 Purchase & Stock Entry":
    st.title("📦 Purchases & Stock")
    with st.form("purchase_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            p_date = st.date_input("Date", value=datetime.today())
            vendor = st.text_input("Vendor")
            item_name = st.text_input("Item Name")
        with c2:
            p_sku = st.text_input("SKU Code")
            qty = st.number_input("Quantity", min_value=1, value=10)
            rate = st.number_input("Rate per unit (₹)", min_value=0.0, step=10.0)
        with c3:
            gst_pc = st.number_input("GST %", min_value=0.0, max_value=28.0, value=0.0)
            p_total = (qty * rate) * (1 + (gst_pc / 100))
            st.metric("Total Amount", f"₹{p_total:,.2f}")
            p_notes = st.text_input("Notes")

        if st.form_submit_button("Purchase Record Save Karo"):
            cursor.execute("""
            INSERT INTO purchases (date, vendor, item_name, sku, quantity, purchase_rate, gst_percent, total_amount, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (str(p_date), vendor, item_name, p_sku, qty, rate, gst_pc, p_total, p_notes))
            conn.commit()
            st.success("✅ Purchase Saved!")
            st.rerun()

    df_p = pd.read_sql_query("SELECT * FROM purchases ORDER BY id DESC", conn)
    st.dataframe(df_p, use_container_width=True)

elif menu == "📊 Profit, GST & Audit Report":
    st.title("📊 Month-End Financial Audit")
    t_orders = cursor.execute("SELECT COUNT(*) FROM master_orders").fetchone()[0] or 0
    t_sales = cursor.execute("SELECT SUM(total_invoice_amount) FROM master_orders").fetchone()[0] or 0.0
    t_cost = cursor.execute("SELECT SUM(total_amount) FROM purchases").fetchone()[0] or 0.0

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Sales Volume", f"₹{t_sales:,.2f}")
    c2.metric("Total Purchase Cost", f"₹{t_cost:,.2f}")
    c3.metric("Net Margin", f"₹{(t_sales - t_cost):,.2f}")
                            
