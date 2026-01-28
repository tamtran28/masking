import streamlit as st
import pandas as pd
import hashlib
import random
import string
import io

# ================= CONFIG =================
st.set_page_config(page_title="Data Masking Tool", layout="centered")
st.title("🔐 Tool tự động ẩn dữ liệu nhạy cảm")

# ================= FUNCTIONS =================
def mask_string(val):
    if pd.isna(val):
        return val
    return "*" * len(str(val))

def mask_number(val):
    if pd.isna(val):
        return val
    val_str = str(val)
    return "".join(random.choices(string.digits, k=len(val_str)))

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

# ================= UPLOAD FILE =================
uploaded_file = st.file_uploader(
    "📂 Upload file cần xử lý (CSV / XLSX / XLS)",
    type=["csv", "xlsx", "xls"]
)

if uploaded_file is not None:
    try:
        file_name = uploaded_file.name.lower()

        # ---------- READ FILE ----------
        if file_name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)

        elif file_name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file, engine="openpyxl")

        elif file_name.endswith(".xls"):
            df = pd.read_excel(uploaded_file, engine="xlrd")

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
                st.success(f"✅ Đã tìm thấy cột `{column_name}`")

                masking_type = st.selectbox(
                    "🔧 Chọn cách ẩn dữ liệu",
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
                    elif masking_type == "Random số":
                        df_masked[column_name] = df_masked[column_name].apply(mask_number)

                    st.subheader("✅ Preview dữ liệu sau khi ẩn")
                    st.dataframe(df_masked.head())

                    # ---------- EXPORT ----------
                    output = io.BytesIO()

                    if file_name.endswith(".csv"):
                        df_masked.to_csv(output, index=False)
                        out_name = "masked_data.csv"

                    elif file_name.endswith(".xlsx"):
                        df_masked.to_excel(output, index=False)
                        out_name = "masked_data.xlsx"

                    else:  # .xls
                        df_masked.to_excel(output, index=False, engine="xlwt")
                        out_name = "masked_data.xls"

                    st.download_button(
                        "⬇️ Download file đã ẩn dữ liệu",
                        data=output.getvalue(),
                        file_name=out_name,
                        mime="application/octet-stream"
                    )

    except Exception as e:
        st.error("❌ Có lỗi xảy ra khi xử lý file")
        st.exception(e)
