import streamlit as st
from utils.ui import page_header, section

user = st.session_state.get("user")
page_header("🚚 Theo dõi nhập kho", "")
section("Tính năng đang cập nhật")
st.info("Tính năng này đang được cập nhật. Vui lòng quay lại sau.")
