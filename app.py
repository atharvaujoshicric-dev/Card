import streamlit as st
import pdfplumber
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="HDFC Statement Extractor", layout="centered")

st.title("💳 Domestic Transactions to Excel")
st.write("Upload your HDFC Credit Card statement to extract transaction data.")

uploaded_file = st.file_uploader("Choose your PDF file", type="pdf")

if uploaded_file is not None:
    with st.spinner('Scanning all pages...'):
        all_rows = []
        
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    for row in table:
                        # Only keep rows that look like transactions (starting with a date)
                        # Your dates look like '31/01/2026' or '01/02/2026'
                        if row[0] and any(char.isdigit() for char in str(row[0])):
                            # Ignore the header row itself if it's captured
                            if "DATE" not in str(row[0]).upper():
                                all_rows.append(row)

        if all_rows:
            # Manually define columns based on your statement structure
            columns = ["DATE & TIME", "TRANSACTION DESCRIPTION", "AMOUNT PI"]
            
            # Create DataFrame
            final_df = pd.DataFrame(all_rows)
            
            # If the PDF extraction returned extra columns, trim them to match our 3 headers
            final_df = final_df.iloc[:, :3] 
            final_df.columns = columns
            
            # Clean up the 'AMOUNT PI' column - remove currency symbols and commas
            final_df["AMOUNT PI"] = final_df["AMOUNT PI"].astype(str).str.replace('₹', '').str.replace(',', '').str.strip()
            
            st.success(f"Successfully extracted {len(final_df)} transaction rows!")
            st.dataframe(final_df)

            # Convert to Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                final_df.to_excel(writer, index=False, sheet_name='Domestic_Transactions')
            
            st.download_button(
                label="📥 Download Transactions as Excel",
                data=output.getvalue(),
                file_name="HDFC_Transactions_Extracted.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("No transactions found. Please ensure this is the correct HDFC statement format.")
