import streamlit as st
import pdfplumber
import pandas as pd
from io import BytesIO
import re

st.set_page_config(page_title="Universal Statement Extractor", layout="wide")

st.title("💳 Universal Transaction Extractor")
st.write("Upload any Credit Card PDF to extract transaction data into Excel.")

uploaded_file = st.file_uploader("Choose your PDF file", type="pdf")

if uploaded_file is not None:
    with st.spinner('Deep-scanning PDF structure...'):
        all_data = []
        
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                # Switching to extract_words to bypass table border issues
                words = page.extract_words()
                
                # Group words into lines based on their vertical position (top)
                lines = {}
                for word in words:
                    top = round(word['top'], 0)
                    lines.setdefault(top, []).append(word)
                
                for top in sorted(lines.keys()):
                    line_text = " ".join([w['text'] for w in sorted(lines[top], key=lambda x: x['x0'])])
                    
                    # Pattern for Date (DD/MM/YYYY or DD/MM/YY) 
                    date_match = re.search(r'(\d{2}/\d{2}/\d{2,4})', line_text)
                    
                    if date_match:
                        # Logic: If it starts with a date, it's likely a transaction [cite: 95, 121]
                        # We split the line and try to separate Date, Description, and Amount
                        parts = line_text.split()
                        if len(parts) >= 3:
                            date = parts[0]
                            # Amount is usually at the end, often with ₹ or commas [cite: 116, 127]
                            amount = parts[-1]
                            description = " ".join(parts[1:-1])
                            
                            # Validating that the 'Amount' actually contains numbers
                            if any(char.isdigit() for char in amount):
                                all_data.append([date, description, amount])

        if all_data:
            df = pd.DataFrame(all_data, columns=["Date", "Description", "Amount"])
            
            # Cleaning the Amount column for Excel [cite: 116, 127]
            df["Amount"] = (df["Amount"]
                            .str.replace('₹', '', regex=False)
                            .str.replace(',', '', regex=False)
                            .str.replace('+', '', regex=False)
                            .str.strip())
            
            # Filter out common non-transaction lines like "Page X of Y" [cite: 96, 117, 122]
            df = df[~df["Description"].str.contains("Page|Statement|Date", case=False)]

            st.success(f"Successfully extracted {len(df)} rows!")
            st.dataframe(df, use_container_width=True)

            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Transactions')
            
            st.download_button(
                label="📥 Download Excel",
                data=output.getvalue(),
                file_name="Extracted_Transactions.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("No transactions found. This usually happens if the PDF is a scanned image (OCR required) rather than a digital document.")
