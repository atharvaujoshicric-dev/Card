import streamlit as st
import pdfplumber
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="HDFC Statement Extractor", layout="centered")

st.title("💳 Domestic Transactions to Excel")
st.write("Upload your HDFC 'Card Feb-26.pdf' to extract all domestic transactions.")

# FIX: Changed st.file_file_uploader to st.file_uploader
uploaded_file = st.file_uploader("Choose your PDF file", type="pdf")

if uploaded_file is not None:
    with st.spinner('Extracting transactions...'):
        all_transactions = []
        
        with pdfplumber.open(uploaded_file) as pdf:
            # Your statement is 16 pages [cite: 196]
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    df = pd.DataFrame(table)
                    
                    # Look for the Domestic Transactions header [cite: 94, 121]
                    if not df.empty and any(df.iloc[0].astype(str).str.contains("TRANSACTION DESCRIPTION", case=False, na=False)):
                        df.columns = df.iloc[0]
                        df = df[1:] 
                        all_transactions.append(df)

        if all_transactions:
            final_df = pd.concat(all_transactions, ignore_index=True)
            
            # Clean up empty rows and the repeated headers from different pages
            final_df = final_df[final_df["DATE & TIME"].notna()]
            final_df = final_df[final_df["DATE & TIME"] != "DATE & TIME"]
            
            st.success(f"Found {len(final_df)} transactions!")
            st.dataframe(final_df)

            # Convert to Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                final_df.to_excel(writer, index=False, sheet_name='Domestic_Transactions')
            
            processed_data = output.getvalue()

            st.download_button(
                label="📥 Download Transactions as Excel",
                data=processed_data,
                file_name="HDFC_Domestic_Transactions_Feb26.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("Could not find the 'Domestic Transactions' table. Ensure the PDF isn't password protected.")
