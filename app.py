import streamlit as st
import pdfplumber
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="HDFC Statement Extractor", layout="wide")

st.title("💳 Domestic Transactions to Excel")
st.write("Extracting transactions from your HDFC statement.")

uploaded_file = st.file_uploader("Choose your PDF file", type="pdf")

if uploaded_file is not None:
    with st.spinner('Parsing 16 pages...'):
        all_rows = []
        
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    for row in table:
                        # Clean out None and filter for rows with actual data
                        clean_row = [str(item).strip() if item is not None else "" for item in row]
                        
                        # Identify transaction rows by date pattern (e.g., 01/02/2026)
                        if clean_row and len(clean_row) >= 2:
                            # Look for the date at the start of the row [cite: 95, 116]
                            if "/" in clean_row[0] and any(char.isdigit() for char in clean_row[0]):
                                # Ensure we only take the first 3 relevant columns
                                all_rows.append(clean_row[:3])

        if len(all_rows) > 0:
            # Safely create DataFrame
            df = pd.DataFrame(all_rows, columns=["Date & Time", "Description", "Amount"])
            
            # Final Clean-up
            # FIX: Added .str before .strip() to avoid AttributeError
            df["Description"] = df["Description"].str.replace('\n', ' ')
            df["Amount"] = df["Amount"].str.replace('₹', '').str.replace(',', '').str.replace('+', '').str.strip()
            
            st.success(f"Successfully extracted {len(df)} transactions.")
            st.dataframe(df, use_container_width=True)

            # Excel Export
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Domestic_Transactions')
            
            st.download_button(
                label="📥 Download Excel File",
                data=output.getvalue(),
                file_name="HDFC_Domestic_Transactions.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("No transactions found. Check if the PDF is the standard HDFC layout.")
