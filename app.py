import streamlit as st
import pdfplumber
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="HDFC Statement Extractor", layout="wide")

st.title("💳 Domestic Transactions to Excel")
st.write("Extracting domestic transactions for billing period: **02 Feb, 2026 - 01 Mar, 2026**.")

uploaded_file = st.file_uploader("Choose your PDF file", type="pdf")

if uploaded_file is not None:
    with st.spinner('Parsing 16 pages of transactions...'):
        all_rows = []
        
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    for row in table:
                        # Clean out None values from the row list
                        clean_row = [str(item).strip() if item is not None else "" for item in row]
                        
                        # Identify transaction rows by date pattern (e.g., 01/02/2026)
                        if clean_row and any(char.isdigit() for char in clean_row[0]):
                            if "/" in clean_row[0] and "DATE" not in clean_row[0].upper():
                                # We only want the Date, Description, and Amount
                                # HDFC usually has these in indices 0, 1, and 2
                                all_rows.append(clean_row[:3])

        if all_rows:
            # Create DataFrame with flexible column handling
            df = pd.DataFrame(all_rows, columns=["Date & Time", "Description", "Amount"])
            
            # Data Cleaning for Excel usability
            # 1. Remove currency symbols and commas from Amount 
            df["Amount"] = df["Amount"].str.replace('₹', '').str.replace(',', '').str.replace('+', '')
            
            # 2. Clean up multi-line Meta/Facebook descriptions [cite: 116, 132]
            df["Description"] = df["Description"].str.replace('\n', ' ')

            st.success(f"Extracted {len(df)} transactions.")
            st.dataframe(df, use_container_width=True)

            # Generate Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Domestic_Transactions')
            
            st.download_button(
                label="📥 Download Excel File",
                data=output.getvalue(),
                file_name="HDFC_Domestic_Feb26.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("No transactions detected. Verify the PDF is a standard HDFC Credit Card statement.")
