import io
import json
import sqlite3
from datetime import datetime
from google import genai
from google.genai import types
import pandas as pd
from PIL import Image
import streamlit as st

st.set_page_config(
    page_title="E-Commerce AI Master ERP",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------- DATABASE SETUP -----------------
conn = sqlite3.connect("business_data.db", check_same_thread=False)
cursor = conn.cursor()

# Comprehensive Master Table for Orders / Invoices / Shipping Labels
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

# Purchases Table (For Stock & Expenses)
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

# ----------------- CONFIGURATION -----------------
st.sidebar.title("⚙️ Setup & Settings")
gemini_api_key = st.secrets.get("GEMINI_API_KEY", "")
if not gemini_api_key:
  gemini_api_key = st.sidebar.text_input("Gemini API Key", type="password")

if gemini_api_key:
  st.sidebar.success("✅ API Key Connected")
else:
  st.sidebar.warning("⚠️ API Key missing! Secrets ya yahan add karein.")

# ----------------- NAVIGATION -----------------
menu = st.sidebar.radio(
    "Navigation",
    [
        "📸 100% Detail AI Scanner",
        "📋 Orders Master Excel Sheet",
        "📦 Purchase & Stock Entry",
        "📊 Profit, GST & Audit Report",
    ],
)

# ==============================================================================
# 1. AI SCANNER (ZERO DATA LOSS PROMPT)
# ==============================================================================
if menu == "📸 100% Detail AI Scanner":
  st.title("📸 AI Smart Document & Label Scanner")
  st.caption(
      "Shipping Label, Tax Invoice, Commercial Bill, ya Purchase Challan — AI"
      " har ek single field read karega!"
  )

  col1, col2 = st.columns([1, 1])

  with col1:
    uploaded_file = st.file_uploader(
        "Upload Image (JPG/PNG)", type=["jpg", "png", "jpeg"]
    )
    if uploaded_file:
      image = Image.open(uploaded_file)
      st.image(
          image, caption="Uploaded Document Preview", use_container_width=True
      )

  with col2:
    if uploaded_file:
      st.write("### 🔍 Scan Execution")
      scan_btn = st.button(
          "⚡ Puri Details Extract Karo", use_container_width=True
      )

      if scan_btn:
        if not gemini_api_key:
          st.error("Pehle API Key provide karo!")
        else:
          try:
            with st.spinner(
                "AI document ke har kone se data nikal raha hai (Barcodes,"
                " Courier, Items, Taxes)..."
            ):
              client = genai.Client(api_key=gemini_api_key)

              prompt = """
You are an expert Optical Character Recognition (OCR) and document parser specialized in Indian E-Commerce shipping labels, tax invoices, bills of supply, and logistics waybills (Meesho, Flipkart, Amazon, Delhivery, Ecom Express, Shadowfax, Valmo, etc.).

Analyze the provided image with extreme precision and extract EVERY piece of information into a valid, strict JSON object. Do not miss any text, code, numbers, or breakdown.

Output JSON format strictly matching this schema:
{
    "doc_type": "Shipping Label / Tax Invoice / Purchase Bill",
    "marketplace": "Meesho / Flipkart / Amazon / Direct / Other",
    "order_no": "Order No (e.g. 332867289910263040)",
    "sub_order_no": "Sub-Order No if any (e.g. 332867289910263040_1)",
    "invoice_no": "Invoice No (e.g. ndigr2738)",
    "order_date": "Order date (DD.MM.YYYY or as printed)",
    "invoice_date": "Invoice date",
    "courier_name": "Courier/Logistics company name (e.g. Valmo, Delhivery, Shadowfax)",
    "tracking_awb": "AWB / Tracking / Barcode number under the barcode (e.g. VL0085467605853)",
    "routing_code": "Routing / Hub / Sort codes (e.g. SJN-R0, N2/JFS, N2/KTHS, 6/CTC)",
    "customer_name": "Full customer name (e.g. raksha purohit)",
    "customer_phone": "Phone number if present, else empty",
    "customer_address": "Full delivery address including landmarks",
    "customer_city": "City / District / Town (e.g. chittorgarh)",
    "customer_state": "State (e.g. Rajasthan)",
    "customer_pincode": "Delivery Pincode (e.g. 312001)",
    "return_seller_name": "Return / Sold by name (e.g. D Gift Hamper Hub / Soheel khan)",
    "return_address": "Complete return address printed on label",
    "seller_gstin": "Seller GSTIN if mentioned",
    "seller_enrolment": "Seller Enrolment No (e.g. 082600128632ESB)",
    "sku": "Product SKU code (e.g. D08iBHFm)",
    "product_name": "Full product description/title printed in table",
    "size": "Size (e.g. Free Size, XL, M)",
    "color": "Color (e.g. Silver, Gold)",
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
    "payment_mode": "Prepaid / COD (e.g. if 'Prepaid: Do not collect cash' then 'Prepaid', else 'COD')",
    "notes": "Any other notes, instructions or codes found"
}

Ensure all numeric fields are numbers (not strings with Rs or symbols). If not present, use 0.0 for numbers and empty string "" for text. Return ONLY pure raw JSON without markdown markers or backticks.
"""

              response = client.models.generate_content(
                  model="gemini-2.5-flash", contents=[prompt, image]
              )

              cleaned_text = response.text.strip()
              if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
              if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
              if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
              cleaned_text = cleaned_text.strip()

              data = json.loads(cleaned_text)

              now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
              cursor.execute(
                  """
                            INSERT INTO master_orders (
                                scan_timestamp, doc_type, marketplace, order_no, sub_order_no, invoice_no,
                                order_date, invoice_date, courier_name, tracking_awb, routing_code,
                                customer_name, customer_phone, customer_address, customer_city, customer_state, customer_pincode,
                                return_seller_name, return_address, seller_gstin, seller_enrolment,
                                sku, product_name, size, color, quantity, gross_amount, discount,
                                taxable_amount, gst_rate, cgst, sgst, igst, tcs_amount, shipping_charges, other_charges,
                                total_invoice_amount, payment_mode, order_status, notes
                            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                            """,
                  (
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
                      str(data.get("notes", "")),
                  ),
              )
              conn.commit()

              st.success(
                  "🎉 Mubarak! Ek-ek detail database me successfully lock ho"
                  " gayi!"
              )

              st.write("#### 📌 Extracted Key Summary:")
              m1, m2, m3 = st.columns(3)
              m1.metric("Order ID", data.get("order_no", "-"))
              m2.metric("AWB / Tracking", data.get("tracking_awb", "-"))
              m3.metric(
                  "Total Amount", f"₹{data.get('total_invoice_amount', 0.0)}"
              )

              with st.expander(
                  "👁️ View All Extracted Fields (Full JSON)", expanded=True
              ):
                st.json(data)

          except Exception as e:
            st.error(f"Error aaya: {e}")

# ==============================================================================
# 2. ORDERS MASTER SHEET & EXCEL EXPORT
# ==============================================================================
elif menu == "📋 Orders Master Excel Sheet":
  st.title("📋 Master Orders & Invoices Sheet")
  st.caption(
      "Puri database ki detailed sheet. Yahan se 1-click me Excel download karo."
  )

  df_orders = pd.read_sql_query(
      "SELECT * FROM master_orders ORDER BY id DESC", conn
  )

  if not df_orders.empty:
    col_search1, col_search2 = st.columns(2)
    with col_search1:
      q_search = st.text_input("🔍 Search by SKU, Order No, Customer, ya City:")
    with col_search2:
      pay_filter = st.multiselect(
          "Payment Mode Filter:",
          options=list(df_orders["payment_mode"].unique()),
          default=list(df_orders["payment_mode"].unique()),
      )

    filtered_df = df_orders.copy()
    if q_search:
      filtered_df = filtered_df[
          filtered_df["sku"].str.contains(q_search, case=False, na=False)
          | filtered_df["order_no"].str.contains(
              q_search, case=False, na=False
          )
          | filtered_df["customer_name"].str.contains(
              q_search, case=False, na=False
          )
          | filtered_df["customer_city"].str.contains(
              q_search, case=False, na=False
          )
          | filtered_df["tracking_awb"].str.contains(
              q_search, case=False, na=False
          )
      ]
    if pay_filter:
      filtered_df = filtered_df[filtered_df["payment_mode"].isin(pay_filter)]

    # Excel Export Button
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
      filtered_df.to_excel(writer, index=False, sheet_name="Master_Orders")
    buffer.seek(0)

    st.download_button(
        label="📥 Download Filtered Master Excel Sheet (.xlsx)",
        data=buffer,
        file_name=(
            f"ECom_Master_Orders_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        ),
        mime=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        use_container_width=True,
    )

    st.write(f"Showing **{len(filtered_df)}** records:")
    st.dataframe(filtered_df, use_container_width=True)

  else:
    st.info("Abhi tak koi order scan nahi hua hai. Scanner tab se upload karein.")

# ==============================================================================
# 3. PURCHASES & EXPENSES
# ==============================================================================
elif menu == "📦 Purchase & Stock Entry":
  st.title("📦 Purchases & Stock Management")
  st.caption(
      "Khareed / Raw material / Stock add karo taaki month-end profit accurate"
      " calculate ho sake."
  )

  with st.form("manual_purchase_form"):
    p_col1, p_col2, p_col3 = st.columns(3)
    with p_col1:
      p_date = st.date_input("Purchase Date", value=datetime.today())
      vendor = st.text_input("Vendor / Supplier Name")
      item_name = st.text_input("Item Name / Description")
    with p_col2:
      p_sku = st.text_input("SKU Code (Matches sales)")
      qty = st.number_input("Quantity Purchased", min_value=1, value=10)
      rate = st.number_input("Rate per unit (₹)", min_value=0.0, step=10.0)
    with p_col3:
      gst_pc = st.number_input(
          "GST %", min_value=0.0, max_value=28.0, value=0.0
      )
      p_total = (qty * rate) * (1 + (gst_pc / 100))
      st.metric("Total Bill Amount", f"₹{p_total:,.2f}")
      p_notes = st.text_input("Remarks / Bill Ref No")

    if st.form_submit_button("Save Purchase Record"):
      cursor.execute(
          """
            INSERT INTO purchases (date, vendor, item_name, sku, quantity, purchase_rate, gst_percent, total_amount, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
          (
              str(p_date),
              vendor,
              item_name,
              p_sku,
              qty,
              rate,
              gst_pc,
              p_total,
              p_notes,
          ),
      )
      conn.commit()
      st.success("✅ Stock & Purchase Record Saved!")
      st.rerun()

  st.write("---")
  st.subheader("Purchase History")
  df_p = pd.read_sql_query("SELECT * FROM purchases ORDER BY id DESC", conn)
  st.dataframe(df_p, use_container_width=True)

# ==============================================================================
# 4. MONTH-END, PROFIT & AUDIT REPORT
# ==============================================================================
elif menu == "📊 Profit, GST & Audit Report":
  st.title("📊 Month-End Financial & Operational Audit")
  st.caption(
      "Month end me sab kuch check karne ke liye ek single consolidated screen."
  )

  total_orders = (
      cursor.execute("SELECT COUNT(*) FROM master_orders").fetchone()[0] or 0
  )
  total_sales_value = (
      cursor.execute(
          "SELECT SUM(total_invoice_amount) FROM master_orders WHERE"
          " order_status != 'Customer Cancelled'"
      ).fetchone()[0]
      or 0.0
  )
  total_purchase_cost = (
      cursor.execute("SELECT SUM(total_amount) FROM purchases").fetchone()[0]
      or 0.0
  )
  prepaid_count = (
      cursor.execute(
          "SELECT COUNT(*) FROM master_orders WHERE payment_mode LIKE"
          " '%Prepaid%'"
      ).fetchone()[0]
      or 0
  )
  cod_count = (
      cursor.execute(
          "SELECT COUNT(*) FROM master_orders WHERE payment_mode LIKE '%COD%'"
      ).fetchone()[0]
      or 0
  )

  gross_margin = total_sales_value - total_purchase_cost

  c1, c2, c3, c4 = st.columns(4)
  c1.metric("Total Sales Volume", f"₹{total_sales_value:,.2f}")
  c2.metric("Total Purchases / Cost", f"₹{total_purchase_cost:,.2f}")
  c3.metric(
      "Net Gross Margin",
      f"₹{gross_margin:,.2f}",
      delta="Profit" if gross_margin >= 0 else "Loss",
  )
  c4.metric("Total Dispatched Orders", total_orders)

  c5, c6, c7, c8 = st.columns(4)
  c5.metric("Prepaid Orders", prepaid_count)
  c6.metric("COD Orders", cod_count)
  c7.metric(
      "Active Sellers / Enrolments",
      cursor.execute(
          "SELECT COUNT(DISTINCT seller_enrolment) FROM master_orders"
      ).fetchone()[0]
      or 0,
  )
  c8.metric(
      "Unique Customer Cities",
      cursor.execute(
          "SELECT COUNT(DISTINCT customer_city) FROM master_orders"
      ).fetchone()[0]
      or 0,
  )

  st.write("---")
  col_chart1, col_chart2 = st.columns(2)

  df_mo = pd.read_sql_query("SELECT * FROM master_orders", conn)
  if not df_mo.empty:
    with col_chart1:
      st.write("#### 🏆 Top 10 Selling SKUs")
      st.bar_chart(df_mo["sku"].value_counts().head(10))

    with col_chart2:
      st.write("#### 📍 Top Customer Cities")
      st.bar_chart(df_mo["customer_city"].value_counts().head(10))
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
            
