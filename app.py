import streamlit as st
import pdfplumber
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="HDFC Statement Extractor", layout="centered")

st.title("💳 Domestic Transactions to Excel")
st.write("Upload your HDFC 'Card Feb-26.pdf' to extract transaction data.")

uploaded_file = st.file_file_uploader("Choose your PDF file", type="pdf")

if uploaded_file is not None:
    with st.spinner('Extracting transactions...'):
        all_transactions = []
        
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                # Extract tables from each page
                tables = page.extract_tables()
                for table in tables:
                    df = pd.DataFrame(table)
                    
                    # Identify the correct table by checking for header keywords
                    if any(df.iloc[0].astype(str).str.contains("TRANSACTION DESCRIPTION", case=False, na=False)):
                        # Set the first row as header
                        df.columns = df.iloc[0]
                        df = df[1:] 
                        all_transactions.append(df)

        if all_transactions:
            # Combine all found tables into one
            final_df = pd.concat(all_transactions, ignore_index=True)
            
            # Basic Cleaning: Remove rows that are just headers or empty
            final_df = final_df[final_df["DATE & TIME"].notna()]
            
            st.success(f"Found {len(final_df)} transactions!")
            st.dataframe(final_df)

            # Convert to Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                final_df.to_excel(writer, index=False, sheet_name='Domestic_Transactions')
            
            processed_data = output.getvalue()

            # Download Button
            st.download_button(
                label="📥 Download Transactions as Excel",
                data=processed_data,
                file_name="HDFC_Domestic_Transactions_Feb26.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("Could not find the 'Domestic Transactions' table structure in this PDF.")
