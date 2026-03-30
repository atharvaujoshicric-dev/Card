import streamlit as st
import pdfplumber
import pandas as pd
from io import BytesIO
import re

st.set_page_config(page_title="HDFC Statement Pro", layout="wide")

st.title("💳 Universal HDFC Transaction Extractor")
st.write("Extracting Domestic & International transactions with Date/Time splitting.")

uploaded_file = st.file_uploader("Upload your 'Card Feb-26.pdf'", type="pdf")

if uploaded_file is not None:
    with st.spinner('Deep-scanning all pages...'):
        all_data = []
        
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                # Extracting raw text instead of tables to bypass border issues
                text = page.extract_text()
                if not text:
                    continue
                
                # Split text into individual lines
                lines = text.split('\n')
                
                for line in lines:
                    # Specific Regex for: Date (dd/mm/yyyy) + optional pipe | + Time (hh:mm)
                    # This matches "02/02/2026| 18:59" or "02/02/2026 18:59"
                    match = re.search(r'(\d{2}/\d{2}/\d{4})\s*[|]*\s*(\d{2}:\d{2})\s+(.*?)\s+([₹\d,+-]+\.\d{2})', line)
                    
                    if match:
                        date = match.group(1)
                        time = match.group(2)
                        description = match.group(3).strip()
                        amount = match.group(4)
                        
                        all_data.append([date, time, description, amount])

        if all_data:
            df = pd.DataFrame(all_data, columns=["Date", "Time", "Description", "Amount"])
            
            # Clean Amount: Remove currency symbols and formatting for Excel math
            df["Amount"] = (df["Amount"]
                            .str.replace('₹', '', regex=False)
                            .str.replace(',', '', regex=False)
                            .str.replace('+', '', regex=False)
                            .str.strip())
            
            st.success(f"Successfully extracted {len(df)} transactions!")
            st.dataframe(df, use_container_width=True)

            # Export to Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='All_Transactions')
            
            st.download_button(
                label="📥 Download Transactions Excel",
                data=output.getvalue(),
                file_name="HDFC_Extracted_Transactions.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("Still no transactions found. Please verify if the PDF text is selectable (not a scanned image).")
