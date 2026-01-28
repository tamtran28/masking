import streamlit as st
import pandas as pd
import hashlib
import random
import string
import io

import pyexcel as pe

# ================= CONFIG =================
st.set_page_config(page_title="Data Masking Tool", layout="centered")
st.title("🔐 Tool tự động ẩn dữ liệu nhạy cảm (hỗ trợ XLS hàng loạt)")

# ================= FUNCTIONS =================
def mask_string(val):
    if pd.isna(val):
        return val
    return "*" * len(str(val))

def mask_number(val):
    if pd.isna(val):
        return val
    return "".join(random.choices(string.digits, k=len(str(val))))

def mask_email(val):
    if pd.isna(val):
        return val
    val = str(val)
    if "@" not in val:
        return mask_string(val)
    domain = val.split("@")[1]
    return f"user_{random.randint(1000,9999)}@{domain}"

def hash_value(val):
    if pd.isna(val):
        return val
    return hashlib.sha256(str(val).encode()).hexdigest()[:12]

def auto_mask(series):
    if series.astype(str).str.contains("@").any():
        return series.apply(mask_email)
    if pd.api.types.is_numeric_dtype(series):
        return series.apply(mask_number)
    return series.apply(mask_string)

def read_xls_with_pyexcel(uploaded_file):
    sheet = pe.get_sheet(file_type="xls", file_content=uploaded_file.read())
    data = sheet.to_array()
    return pd.DataFrame(data[1:], columns=data[0])

# ================= UPLOAD =================
uploaded_file = st.file_uploader(
    "📂 Upload file (CSV / XLSX / XLS – xử lý tự động)",
    type=["csv", "xlsx", "xls"]
)

if uploaded_file:
    file_name = uploaded_file.name.lower()

    # ---------- READ FILE ----------
    if file_name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)

    elif file_name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file, engine="openpyxl")

    elif file_name.endswith(".xls"):
        df = read_xls_with_pyexcel(uploaded_file)
        st.info("ℹ️ File .xls đã được tự động convert sang DataFrame")

    else:
        st.error("❌ Định dạng file không được hỗ trợ")
        st.stop()

    st.subheader("📄 Preview dữ liệu ban đầu")
    st.dataframe(df.head())

    # ---------- COLUMN INPUT ----------
    column_name = st.text_input(
        "✏️ Nhập TÊN CỘT cần ẩn dữ liệu (đúng 100%)"
    )

    if column_name:
        if column_name not in df.columns:
            st.error(f"❌ Không tìm thấy cột `{column_name}`")
        else:
            masking_type = st.selectbox(
                "🔧 Cách ẩn dữ liệu",
                (
                    "Tự động (khuyến nghị)",
                    "Mask toàn bộ (****)",
                    "Hash (không khôi phục)",
                    "Random số"
                )
            )

            if st.button("🚀 Thực hiện ẩn dữ liệu"):
                df_masked = df.copy()

                if masking_type == "Tự động (khuyến nghị)":
                    df_masked[column_name] = auto_mask(df_masked[column_name])
                elif masking_type == "Mask toàn bộ (****)":
                    df_masked[column_name] = df_masked[column_name].apply(mask_string)
                elif masking_type == "Hash (không khôi phục)":
                    df_masked[column_name] = df_masked[column_name].apply(hash_value)
                else:
                    df_masked[column_name] = df_masked[column_name].apply(mask_number)

                st.subheader("✅ Preview sau khi ẩn")
                st.dataframe(df_masked.head())

                # ---------- EXPORT ----------
                output = io.BytesIO()
                df_masked.to_excel(output, index=False)

                st.download_button(
                    "⬇️ Download file đã ẩn dữ liệu (XLSX)",
                    data=output.getvalue(),
                    file_name="masked_data.xlsx",
                    mime="application/octet-stream"
                )
