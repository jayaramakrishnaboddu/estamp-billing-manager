import streamlit as st
import requests
import io
import pandas as pd
from PIL import Image
from streamlit_paste_button import paste_image_button
import time
from alerts import floating_drop_message
BACKEND_URL = "http://127.0.0.1:8000"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_role" not in st.session_state:
    st.session_state.user_role = None

if "username" not in st.session_state:
    st.session_state.username = None
if not st.session_state.logged_in:

    st.title("🔐 E-Stamp Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        response = requests.post(
            f"{BACKEND_URL}/login/",
            json={
                "username": username,
                "password": password
            }
        )

        if response.status_code == 200:

            data = response.json()

            st.session_state.logged_in = True
            st.session_state.user_role = data["role"]
            user_role = data["role"]
            st.session_state.username = data["username"]

            st.rerun()

        else:
            st.error("Invalid username or password")

    st.stop()
    
user_role = st.session_state.user_role
username = st.session_state.username

headers = {
    "X-User-Role": user_role.lower()
} 
st.set_page_config(page_title="E-Stamp Studio", page_icon="📄", layout="wide")

# App-wide UI configuration injector
st.markdown("""<style>
.block-container { padding-top: 1rem; padding-bottom: 0rem; }
header[data-testid="stHeader"] { display: none; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
</style>""", unsafe_allow_html=True)

# ==========================================
# ROLE SELECTION AND SIDEBAR GATEKEEPING
# ==========================================
header_col1, header_col2 = st.columns([6,1])

with header_col1:
    st.markdown("## E-Stamp Billing Management")

with header_col2:
    st.write(f"👤 {st.session_state.username}")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.session_state.username = None
        st.rerun()
if user_role == "admin":
    tab_list = [
        "📥 Stamp Processing",
        "👥 Khata Ledger Statement",
        "📊 Daily Metrics Overview",
        "📋 Transaction Logs Management",
        "👤 User Management"
    ]
else:
    tab_list = [
        "📥 Stamp Processing",
        "👥 Khata Ledger Statement",
        "📊 Daily Metrics Overview",
        "📋 Transaction Logs Management"
    ]
tabs = st.tabs(tab_list)

# Fetch universal customer master array references
try:
    c_res = requests.get(f"{BACKEND_URL}/customers/")
    customers = c_res.json() if c_res.status_code == 200 else []
except Exception:
    customers = []

# ==========================================
# TAB 1: STAMP PROCESSING PIPELINE
# ==========================================
with tabs[0]:
    left_col, right_col = st.columns([1, 1], gap="medium")
    with left_col:
        st.subheader("📥 Process New E-Stamp")
        pasted_img = paste_image_button(label="📋 Click Here & Paste Screenshot (Ctrl + V)", background_color="#FF4B4B", hover_background_color="#E03A3A")
        if pasted_img.image_data is not None:
            st.image(
                pasted_img.image_data,
                caption="Captured E-Stamp Preview",
                use_container_width=True
            )
        
        if "cert_num" not in st.session_state: st.session_state.cert_num = ""
        if "stamp_amt" not in st.session_state: st.session_state.stamp_amt = 10

        if pasted_img.image_data is not None:
            with st.spinner("⚡ Running Extraction..."):
                try:
                    img_obj = pasted_img.image_data
                    byte_arr = io.BytesIO()
                    img_obj.convert("RGB").save(
                        byte_arr, format="PNG", quality=75, optimize=True
                    )
                    raw_bytes = byte_arr.getvalue()
                    files = {"file": ("screenshot.png", raw_bytes, "image/png")}
                    response = requests.post(f"{BACKEND_URL}/process-stamp/", files=files)
                    st.write("Status:", response.status_code)
                    st.write("Response:", response.text)
                    if response.status_code == 200:
                        extracted = response.json()
                        st.session_state.cert_num = extracted["certificate_number"]
                        st.session_state.stamp_amt = extracted["stamp_duty"]
                        st.success("✅ Parameters Extracted!")
                except Exception as e: st.error(f"Backend Offline: {str(e)}")

    with right_col:
        st.subheader("✏️ Entry Verification")
        cert_input = st.text_input("Verified Certificate Number:", value=st.session_state.cert_num)
        amt_input = st.number_input("Face Value Stamp Duty (₹):", value=int(st.session_state.stamp_amt), step=10)

        # Hiding pricing breakdown calculations dynamically from standard workers
        fee_map = {
            10: 20,
            50: 20,
            100: 30,
            200: 60,
            500: 100,
            1000: 100
        }

        local_fee = fee_map.get(
            amt_input,
            20
        )
        if user_role == "Admin":
            st.info(f"💰 Surcharge: **+₹{local_fee}** | Total Bill: **₹{amt_input + local_fee}**")
        else:
            st.warning(f"Total Amount to Collect from Customer: **₹{amt_input + local_fee}**")

        pay_mode = st.radio("Payment Method:", ["Cash", "PhonePe / Online", "Debt (Khata Ledger)"])
        selected_cust_id = None
        if pay_mode == "Debt (Khata Ledger)" and customers:
            chosen_name = st.selectbox("Assign Debt Account Profile:", [c["name"] for c in customers])
            selected_cust_id = next(c["id"] for c in customers if c["name"] == chosen_name)

        if st.button("🚀 Confirm & Record Entry", use_container_width=True):
            if cert_input.strip():
                payload = {
                    "certificate_number": cert_input.strip(), "stamp_duty": int(amt_input),
                    "payment_mode": "Debt" if "Debt" in pay_mode else ("PhonePe" if "PhonePe" in pay_mode else "Cash"),
                    "customer_id": selected_cust_id,
                    "processed_by": st.session_state.username
                }
                res = requests.post(f"{BACKEND_URL}/transactions/", json=payload)
                if res.status_code == 201:
                    floating_drop_message("🚀 SUCCESS: Entry Recorded!", bg_color="#EE0101", text_color="#FFFFFF")
                    time.sleep(2)
                    st.session_state.cert_num = ""
                    st.session_state.stamp_amt = 10
                    st.rerun()

# ==========================================
# TAB 2: ADVANCED KHATA STATEMENT LOOKUP
# ==========================================
with tabs[1]:
    st.subheader("👥 Khata Customer Balance Records")
    search_customer = st.text_input(
    "🔍 Search Customer",
    placeholder="Name or Phone"
    )
    if search_customer:

        customers = [
            c for c in customers
            if search_customer.lower() in c["name"].lower()
            or search_customer.lower() in str(c.get("phone", "")).lower()
        ]
    if not customers:
        st.info("No credit profiles registered yet.")
    else:
        # 1. Individual Statement Selector Dropdown
        selected_khata_name = st.selectbox("Select Customer Profile to View Detailed Statement Ledger:", [c["name"] for c in customers])
        target_id = next(c["id"] for c in customers if c["name"] == selected_khata_name)
        
        # Pull live detailed logs for this exact client from our new statement endpoint
        try:
            stmt_res = requests.get(f"{BACKEND_URL}/customers/{target_id}/statement/")
            if stmt_res.status_code == 200:
                stmt_data = stmt_res.json()
                
                # Show outstanding balance summary profile banner cards
                st.metric(label=f"🔴 Total Outstanding Dues Owed by {stmt_data['customer_name']}", value=f"₹{stmt_data['balance_due']:,}")
                payment_amount = st.number_input(
                     "Receive Payment (₹)",
                      min_value=1,
                      step=10
                )
                if st.button(
                    "💰 Record Payment",
                    key="record_payment"
                ):
                    response=requests.post(
                        f"{BACKEND_URL}/payments/",
                        json={"customer_id": target_id, "amount": payment_amount}
                    )
                    if response.status_code == 200:
                        st.success("Payment recorded successfully!")
                        st.rerun()
                    else:
                        st.error(response.json().get("detail", "Failed to record payment."))
                col1, col2 = st.columns(2)

                with col1:

                    st.write("#### 📜 Historical Stamp Credit Logs")

                    if stmt_data["history"]:

                        stmt_df = pd.DataFrame(
                            stmt_data["history"]
                        )

                        stmt_df = stmt_df[
                            [
                                "id",
                                "certificate_number",
                                "stamp_duty",
                                "total_collected",
                                "timestamp"
                            ]
                        ]

                        stmt_df.columns = [
                            "Tx ID",
                            "Certificate Number",
                            "Stamp Value",
                            "Amount Added",
                            "Date"
                        ]

                        st.dataframe(
                            stmt_df,
                            use_container_width=True,
                            hide_index=True
                        )

                    else:
                        st.info(
                            "No debt transactions found."
                        )

                with col2:

                    st.write("#### 💵 Payment History")

                    pay_res = requests.get(
                        f"{BACKEND_URL}/customers/{target_id}/payments/"
                    )

                    if pay_res.status_code == 200:

                        pay_data = pay_res.json()

                        if pay_data:

                            pay_df = pd.DataFrame(
                                pay_data
                            )

                            st.dataframe(
                                pay_df,
                                use_container_width=True,
                                hide_index=True
                            )

                        else:
                            st.info(
                                "No payments recorded yet."
                            )
        except Exception as e:
            st.error(f"Failed to fetch customer specific statement trail: {str(e)}")
            
    st.write("---")
    st.markdown("### Create New Khata Account Profile Entry")
    new_cust_name = st.text_input("New Client Account Name:", placeholder="e.g., Ramesh Kumar Advocate")
    if st.button("➕ Register Profile Account", use_container_width=True):
        if new_cust_name.strip():
            requests.post(f"{BACKEND_URL}/customers/", json={"name": new_cust_name.strip()})
            st.success("Registered profile successfully!")
            st.rerun()
            
    if user_role == "admin":

        st.write("---")
        st.markdown("### 🗑️ Delete Khata Holder")

        delete_customer_name = st.selectbox(
            "Select Customer",
            [c["name"] for c in customers],
            key="delete_customer"
        )

        confirm_delete = st.checkbox(
            "I understand this action is permanent"
        )

        if st.button(
            "Delete Customer",
            width="stretch"
        ):

            if not confirm_delete:
                st.warning("Please confirm deletion.")
            else:

                customer_id = next(
                    c["id"]
                    for c in customers
                    if c["name"] == delete_customer_name
                )

                response = requests.delete(
                    f"{BACKEND_URL}/customers/{customer_id}/"
                )

                if response.status_code == 200:
                    st.success("Customer deleted successfully")
                    st.rerun()
                else:
                    st.error(
                        response.json().get("detail")
                    )
# ==========================================
# TAB 3: ADMIN DAILY METRICS OVERVIEW (HIDDEN FROM WORKER)
# ==========================================
with tabs[2]:
    st.subheader("📊 Live Daily Reconciliation Ledger (Admin Oversight)")
    try:
        analytics_res = requests.get(f"{BACKEND_URL}/analytics/daily-summary/", headers=headers)
        if analytics_res.status_code == 200:
            m = analytics_res.json()
            m_col1, m_col2 = st.columns(2)
            
            # Left Column: Visible to ALL users
            with m_col1:
                st.metric(label="💵 Counter Cash Expected (In-Hand)", value=f"₹{m['cash_expected']:,}")
                st.metric(label="📱 PhonePe / UPI Bank Transfers", value=f"₹{m['phonepe_verified']:,}")
                st.metric(label="📝 Outstanding New Debt Registered", value=f"₹{m['debt_incurred']:,}")
                
            # Right Column: Role-restricted metrics
            with m_col2:
                if user_role == "admin":
                    st.metric(
                        label="💰 NET PROFIT EARNED TODAY (COMMISSIONS)", 
                        value=f"₹{m['net_profit']:,}", 
                        delta=f"{m['stamp_count']} Stamps Formatted"
                    )
                else:
                    st.info("accounts.")
        else:
            st.error("Access Prohibited: Server denied validation context.")
    except Exception: 
        st.error("Error connecting to live administration accounting API.")
        
    st.write("---")
    
    # Cleanly separated inside tabs[2] (No longer stuck inside the columns or try blocks)
    st.subheader("📥 Export Reports")

    if st.button("📊 Download Excel Report", use_container_width=True):
        response = requests.get(f"{BACKEND_URL}/export/daily-report/")
        if response.status_code == 200:
            st.download_button(
                label="⬇️ Click to Save Excel File",
                data=response.content,
                file_name="daily_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.error(f"Failed. Status Code: {response.status_code}")
            st.write(response.text)
            
    st.write("---")

    with st.expander("💾 Database Backup"):
        if st.button("📥 Create Backup", use_container_width=True):
            response = requests.get(f"{BACKEND_URL}/backup/")
            if response.status_code == 200:
                st.success("✅ Database backup created successfully")
                st.download_button(
                    label="⬇ Download Backup",
                    data=response.content,
                    file_name="backup.sql",
                    mime="application/sql",
                    use_container_width=True
                )
            else:
                st.error("Backup generation failed")
                
        st.write("---")
        st.subheader("📤 Restore Backup")

        restore_file = st.file_uploader("Select SQL Backup File", type=["sql"])

        if st.button("Restore Database", use_container_width=True):
            if restore_file:
                response = requests.post(
                    f"{BACKEND_URL}/restore/",
                    files={"file": (restore_file.name, restore_file.getvalue())}
                )
                if response.status_code == 200:
                    st.success("✅ Database restored successfully")
                else:
                    st.error(f"Restore failed: {response.text}")

# ==========================================
# TAB 4: TRANSACTION HISTORY LOG & SECURE DELETIONS
# ==========================================
# Map active routing variables based on access role profiles
# ==========================================
# TAB 4: TRANSACTION HISTORY LOG & SECURE DELETIONS
# ==========================================
# Automatically finds the exact positional index of the Audit log tab
history_tab_index = tab_list.index("📋 Transaction Logs Management")

with tabs[history_tab_index]:
    st.subheader("📋 Core Audit Trail History")
    try:
        
        response = requests.get(f"{BACKEND_URL}/transactions/", headers=headers)
        if response.status_code == 200:
            tx_list = response.json()
            selected_date = st.date_input(
                 "📅 Select Date"
             )
            search_tx = st.text_input(
                "🔍 Search Certificate",
                placeholder="Certificate Number",
                key="audit_search_input"
            )
            
            filtered_transactions = tx_list

            # Date Filter
            if selected_date:
                filtered_transactions = [
                    t for t in filtered_transactions
                    if t.get("timestamp", "")[:10] == str(selected_date)
                ]

            # Certificate Search
            if search_tx.strip():
                clean_query = search_tx.strip().lower()

                filtered_transactions = [
                    t for t in filtered_transactions
                    if clean_query in str(
                        t.get("certificate_number", "")
                    ).strip().lower()
                ]

            if filtered_transactions:
                st.caption(f"Showing {len(filtered_transactions)} records")
                df = pd.DataFrame(filtered_transactions)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.warning("No matching certificate found")    
            
            # Secure administrative deletion execution engine panel
            if user_role == "admin":
                st.write("---")
                st.markdown("### 🛠️ Revoke Entry Errors (Admin Deletion Console)")
                delete_id = st.number_input("Enter exact Transaction ID to delete following a worker mistake:", min_value=1, step=1)
                if st.button("🗑️ Permanently Delete Record & Readjust Balances", use_container_width=True):
                    del_res = requests.delete(f"{BACKEND_URL}/transactions/{delete_id}/", headers=headers)
                    if del_res.status_code == 200:
                        st.warning(f"Record #{delete_id} dropped completely.")
                        st.rerun()
                    else:
                        st.error(f"Deletion failed: {del_res.json().get('detail')}")
        else:
            st.info("No transaction histories logged today yet.")
            
    except Exception as e:
        st.error(f"Error drawing database record matrices: {str(e)}")
        
# ==========================================
# TAB 5: USER MANAGEMENT
# ==========================================
if user_role == "admin":
    with tabs[4]:

        st.subheader("👤 User Management")

        users_response = requests.get(
            f"{BACKEND_URL}/users/"
        )

        if users_response.status_code == 200:

            users = users_response.json()

            st.dataframe(
                users,
                width="stretch"
            )

        else:
            st.error("Failed to load users")
            
        with st.expander("➕ Create User"):

            new_username = st.text_input("Username")

            new_password = st.text_input(
                "Password",
                type="password"
            )

            new_role = st.selectbox(
                "Role",
                ["staff", "admin"]
            )

            if st.button("Create User"):

                response = requests.post(
                    f"{BACKEND_URL}/users/",
                    json={
                        "username": new_username,
                        "password_hash": new_password,
                        "role": new_role
                    }
                )

                if response.status_code == 200:
                    st.success("✅ User created successfully")
                    st.rerun()

                else:
                    st.error(response.text)

        with st.expander("🗑 Delete User"):

            user_options = {
                f"{u['username']} ({u['role']})": u["id"]
                for u in users
            }

            selected_delete = st.selectbox(
                "Select User",
                list(user_options.keys()),
                key="delete_user"
            )
            confirm_delete = st.checkbox("I understand this action cannot be undone")   
            if st.button("Delete User"):
                if not confirm_delete:
                    st.warning("Please confirm deletion.")
                else:
                    user_id = user_options[selected_delete]

                    response = requests.delete(
                        f"{BACKEND_URL}/users/{user_id}"
                    )

                    if response.status_code == 200:
                        st.success("✅ User deleted successfully")
                        st.rerun()

                    else:
                        st.error(response.text)
        with st.expander("🔑 Change Password"):

            user_options = {
                f"{u['username']} ({u['role']})": u["id"]
                for u in users
            }

            selected_user = st.selectbox(
                "Select User",
                list(user_options.keys()),
                key="password_user"
            )

            old_password = st.text_input(
                "Current Password",
                type="password"
            )

            new_password = st.text_input(
                "New Password",
                type="password"
            )

            confirm_password = st.text_input(
                "Confirm Password",
                type="password"
            )

            if st.button("Update Password"):

                if new_password != confirm_password:
                    st.error("Passwords do not match")

                else:

                    response = requests.put(
                        f"{BACKEND_URL}/users/password/",
                        json={
                            "user_id": user_options[selected_user],
                            "old_password": old_password,
                            "new_password": new_password
                        }
                    )

                    if response.status_code == 200:
                        st.success("✅ Password updated successfully")

                    else:
                        st.error(response.text)