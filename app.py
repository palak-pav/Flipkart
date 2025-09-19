
import streamlit as st
import requests
import pandas as pd
import json
from datetime import date, datetime
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import matplotlib.pyplot as plt
from streamlit_cookies_manager import EncryptedCookieManager


# MUST be first Streamlit command
st.set_page_config(
    page_title="AdgamaDigital",
    layout="centered",
    page_icon="https://github.com/anmol-varshney/Logo/blob/main/company_logo.png?raw=true"
)
st.write()

# =====Local======
HEADERS = {
    "Fk-Affiliate-Id": "bh7162",
    "Fk-Affiliate-Token": "1e3be35caea748378cdd98e720ea06b3"
}

# ===================== CONFIG(server) =====================
URL = "https://affiliate-api.flipkart.net/affiliate/report/orders/detail/json"

# Affiliate Link Generator Settings
AFFILIATE_ID = "bh7162"
KEEP_PARAMS = [
    "marketplace", "iid", "ppt", "lid", "srno", "pid",
    "store", "ssid", "otracker1", "ppn", "spotlightTagId"
]
ORDER = [
    "marketplace", "iid", "ppt", "lid", "srno",
    "pid", "affid", "store", "ssid", "otracker1",
    "ppn", "spotlightTagId"
]

# ===================== COOKIES =====================
cookies = EncryptedCookieManager(
    prefix="flipkart_testing_app",
    password="u8#sK92!dLxA0@vF9mZrQwT"  # change this to a strong secret key
)
if not cookies.ready():
    st.stop()

# ===================== HELPERS =====================
def load_credentials():
    with open("credentials.json", "r") as file:
        return json.load(file)

def fetch_data(start_date, end_date, status, aff_ext_param1, page_number):
    params = {
        "startDate": start_date,
        "endDate": end_date,
        "status": status,
        "offset": 0,
        "pageNumber": page_number,
        "affExtParam1": aff_ext_param1
    }
    response = requests.get(URL, headers=HEADERS, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to fetch data: {response.status_code}")
        return None


def generate_affiliate_link(url: str) -> str:
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)

    # Add affiliate id
    query_params["affid"] = [AFFILIATE_ID]

    # Decide if it's a product page or listing page
    is_product = "/p/" in parsed.path

    # Keep only necessary params
    keep_keys_product = ["pid", "lid", "marketplace", "store", "srno", "iid", 
                         "ppt", "ppn", "ssid", "otracker1"]
    keep_keys_listing = ["sid", "sort", "iid", "ctx", "cid", "otracker1", "p[]"]

    if is_product:
        filtered = {k: v for k, v in query_params.items() if k in keep_keys_product or k == "affid"}
        # Order matters for product pages
        order = ["marketplace", "iid", "ppt", "lid", "srno", "pid", "affid", 
                 "store", "ssid", "otracker1", "ppn"]
    else:
        filtered = {k: v for k, v in query_params.items() if k in keep_keys_listing or k == "affid"}
        # Order for listing pages
        order = ["affid", "p[]", "sort", "iid", "ctx", "otracker1", "sid", "cid"]

    # Reorder params
    ordered_params = []
    for k in order:
        if k in filtered:
            for val in filtered[k]:
                ordered_params.append((k, val))

    # Build final query string
    final_query = urlencode(ordered_params, doseq=True)

    # Rebuild final URL
    final_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", final_query, ""))
    return final_url


def shorten_with_tinyurl(url: str) -> str:
    api_url = f"http://tinyurl.com/api-create.php?url={url}"
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.text.strip()
    else:
        st.error(f"TinyURL API failed: {response.status_code}")
        return url

def visualize_data(df):
    st.markdown("## 📊 Data Insights")

    total_sales = df["effectivePrice"].sum()
    total_commission = df["commission"].sum()
    total_orders = len(df)

    col1, col2, col3 = st.columns(3)
    col1.metric("📦 Total Orders", total_orders)
    col2.metric("","")#"💰 Total Sales", f"₹{total_sales:,.2f}")
    col3.metric("","")#"🏆 Total Commission", f"₹{total_commission:,.2f}")

    st.markdown("---")
    st.subheader("🏅 Top Products by Sales")
    top_products = df.groupby("productTitle")["effectivePrice"].sum().sort_values(ascending=False).head(5)
    st.dataframe(top_products.reset_index())

# ===================== AUTH =====================
def login():
    col1, col2, col3 = st.columns([1, 2, 1])  
    with col2:  
        st.image("https://github.com/anmol-varshney/Logo/blob/main/company_logo.png?raw=true")
    st.write(" ")
    st.title("🔑 Login Page")
    
    credentials = load_credentials()
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_clicked = st.button("Login")

    if login_clicked:
        if username in credentials and credentials[username][0] == password:
            # Save in cookies
            cookies["username"] = username
            cookies["aff_ext_param1"] = credentials[username][1]
            cookies.save()

            # Update session state
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.session_state["aff_ext_param1"] = credentials[username][1]
            st.rerun()
        else:
            st.error("Invalid username or password")

def restore_login():
    """Restore login state from cookies"""
    if cookies.get("username") and cookies.get("aff_ext_param1"):
        st.session_state["logged_in"] = True
        st.session_state["username"] = cookies["username"]
        st.session_state["aff_ext_param1"] = cookies["aff_ext_param1"]


def logout():
    # Clear cookies properly
    cookies["username"] = ""
    cookies["aff_ext_param1"] = ""
    cookies.save()

    # Clear session state
    for key in ["logged_in", "username", "aff_ext_param1"]:
        if key in st.session_state:
            del st.session_state[key]

    st.success("✅ Logged out successfully")
    st.rerun()



# ===================== MAIN =====================
def main():

    # Restore session from cookies if not already set
    if not st.session_state.get("logged_in", False):
        restore_login()

    if not st.session_state.get("logged_in", False):
        login()
        return
    
    # Title
    st.markdown(
        """
        <div class="title-container" style="background-color:#0d47a1; color:white; padding:2em; text-align:center; border-radius:8px; margin-bottom:2em;">
            <h1>📊 Flipkart Affiliate Order Report</h1>
            <p><b>Welcome to the Flipkart Affiliate Order Dashboard!<br>
            Track your affiliate orders and their status with ease. Use the filters below to customize the data you wish to view.</b></p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Sidebar
    with st.sidebar:
        st.markdown(
            """
            <div class="nav-logo">
                <img src="https://github.com/anmol-varshney/Logo/blob/main/company_logo.png?raw=true" width="100"/>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.write("")
        if "username" in st.session_state:
            st.markdown(
                f"""
                <div style="background:#ffffff; border:2px solid #0288d1; border-radius:8px; padding:0.8em; margin-bottom:1em; text-align:center; font-weight:bold;">
                    Logged in as: {st.session_state['username']}
                </div>
                """,
                unsafe_allow_html=True
            )

        st.header("🔍 Filter Options")
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")
        status = st.selectbox("Order Status", ["approved", "tentative", "cancelled"])
        
        fetch_button = st.button("Fetch Data", key="fetch_data_button", use_container_width=True)
        
        if st.button("Logout", key="logout_button", use_container_width=True):
            logout()
    
    if fetch_button:
        aff_ext_param1 = st.session_state["aff_ext_param1"]
        data = fetch_data(start_date, end_date, status, aff_ext_param1, 1)
        if data and 'paginationContext' in data:
            full_data = []
            total_pages = data['paginationContext']['totalPages']
            for i in range(total_pages):
                page_data = fetch_data(start_date, end_date, status, aff_ext_param1, i+1)
                if page_data and 'orderList' in page_data:
                    full_data.extend(page_data['orderList'])
            req_data = []
            for sample in full_data:
                if str(sample['affExtParam1']).startswith(str(aff_ext_param1)):
                    mapped_row = {
                        "orderItemUnitId": sample.get("affiliateOrderItemId", ""),
                        "orderItemUnitStatus": sample.get("status", ""),
                        "orderDate": sample.get("orderDate", ""),
                        "partnerId": AFFILIATE_ID,
                        "effectivePrice": sample.get("price", 0),
                        "commission": sample.get("tentativeCommission", {}).get("amount", 0),
                        "commissionRuleTitle": sample.get("category", ""),
                        "commissionRate": sample.get("commissionRate", 0),
                        "productId": sample.get("productId", ""),
                        "productTitle": sample.get("title", ""),
                        "extParam1": sample.get("affExtParam1", ""),
                        "extParam2": sample.get("affExtParam2", ""),
                        "updatedAt": sample.get("updatedAt", ""),
                        "orderTimeStamp": sample.get("orderTimeStamp", "")
                    }
                    req_data.append(mapped_row)

            st.markdown("<div style='text-align: center;'><h2>📌 Order Report 📌</h2></div>", unsafe_allow_html=True)
            if req_data:
                df = pd.DataFrame(req_data).reset_index(drop=True)
                df.index = df.index + 1
                st.dataframe(df, use_container_width=True)
                visualize_data(df)
            else:
                st.warning("No data found for the given criteria.")

    # ===================== AFFILIATE LINK GENERATOR =====================
    st.markdown(
    """
    <div style="text-align: center; margin-top: 30px;">
        <h2>🔗 Flipkart Affiliate Link Generator</h2>
        <p><b>Paste a product link below and generate your affiliate link instantly.</b></p>
    </div>
    """,
    unsafe_allow_html=True
    )

    original_url = st.text_input("Enter Flipkart Product URL:")
    subid_input = st.text_input("Enter your Unique ID:")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Generate Affiliate Link"):
            if original_url.strip():
                affiliate_link = generate_affiliate_link(original_url)
                affiliate_link = f"{affiliate_link}&affExtParam1={st.session_state['aff_ext_param1']}"
                tiny_link = shorten_with_tinyurl(affiliate_link)
                st.success("✅ Normal Affiliate Link Generated")
                st.code(tiny_link, language="text")
            else:
                st.warning("Please enter a valid Flipkart URL.")

    with col2:
        if st.button("Generate Affiliate Link with Unique ID"):
            if original_url.strip():
                if not subid_input.strip():
                    st.warning("Please enter your unique ID.")
                else:
                    affiliate_link = generate_affiliate_link(original_url)
                    if "?" in original_url:
                        subid_link = f"{affiliate_link}&affExtParam1={st.session_state['aff_ext_param1']}&affExtParam2={subid_input}"
                    else:
                        subid_link = f"{affiliate_link}?affExtParam1={st.session_state['aff_ext_param1']}&affExtParam2={subid_input}"
                    tiny_subid_link = shorten_with_tinyurl(subid_link)
                    st.success("✅ Unique Affiliate Link Generated")
                    st.code(tiny_subid_link, language="text")
            else:
                st.warning("Please enter a valid Flipkart URL.")

# ===================== RUN =====================
if __name__ == "__main__":
    main()
