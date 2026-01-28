import streamlit as st
import pandas as pd
import hashlib
import random
import string
import io

st.set_page_config(page_title="Data Masking Tool", layout="centered")
st.title("🔐 Tool tự động ẩn dữ liệu nhạy cảm")

# ---------- FUNCTIONS ----------
def mask_string(val):
    if pd.isna(val):
        return val
    return "*" * len(str(val))

def mask_number(val):
    if pd.isna(val):
        return val
    length = len(str(int(val)))
    return "".join(random.choices(string.digits, k=length))

def mask_email(val):
    if pd.isna(val) or "@" not in str(val):
        return val
    domain = str(val).split("@")[1]
    return f"user_{random.randint(1000,9999)}@{domain}"

def hash_value(val):
    if pd.isna(val):
        return val
    return hashlib.sha256(str(val).encode()).hexdigest()[:10]

def auto_mask(series):
    if series.dtype == "object":
        # email detection
        if series.astype(str).str.contains("@").any():
            return series.apply(mask_email)
        else:
            return series.apply(mask_string)
    else:
        return series.apply(mask_number)

# ---------- UPLOAD FILE ----------
uploaded_file = st.file_uploader(
    "📂 Upload file (CSV hoặc Excel)",
    type=["csv", "xlsx"]
)

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.subheader("📄 Preview dữ liệu ban đầu")
    st.dataframe(df.head())

    column_name = st.text_input(
        "✏️ Nhập tên cột cần ẩn dữ liệu (phải đúng 100%)"
    )

    if column_name:
        if column_name not in df.columns:
            st.error(f"❌ Không tìm thấy cột `{column_name}`")
        else:
            st.success(f"✅ Đã tìm thấy cột `{column_name}`")

            masking_type = st.selectbox(
                "🔧 Chọn cách ẩn dữ liệu",
                [
                    "Tự động (khuyến nghị)",
                    "Mask toàn bộ (****)",
                    "Hash (ẩn không khôi phục)",
                    "Random số"
                ]
            )

            if st.button("🚀 Thực hiện ẩn dữ liệu"):
                df_masked = df.copy()

                if masking_type == "Tự động (khuyến nghị)":
                    df_masked[column_name] = auto_mask(df_masked[column_name])
                elif masking_type == "Mask toàn bộ (****)":
                    df_masked[column_name] = df_masked[column_name].apply(mask_string)
                elif masking_type == "Hash (ẩn không khôi phục)":
                    df_masked[column_name] = df_masked[column_name].apply(hash_value)
                elif masking_type == "Random số":
                    df_masked[column_name] = df_masked[column_name].apply(mask_number)

                st.subheader("✅ Dữ liệu sau khi ẩn")
                st.dataframe(df_masked.head())

                output = io.BytesIO()
                if uploaded_file.name.endswith(".csv"):
                    df_masked.to_csv(output, index=False)
                    file_name = "masked_data.csv"
                else:
                    df_masked.to_excel(output, index=False)
                    file_name = "masked_data.xlsx"

                st.download_button(
                    "⬇️ Download file đã ẩn dữ liệu",
                    data=output.getvalue(),
                    file_name=file_name,
                    mime="application/octet-stream"
                )
