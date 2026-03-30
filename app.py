import streamlit as st
import pdfplumber
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Statement Extractor", layout="wide")

st.title("💳 Transaction Extractor")
st.write("Upload your HDFC 'Card Feb-26.pdf' to extract Domestic Transactions into Excel.")

uploaded_file = st.file_uploader("Choose your PDF file", type="pdf")

if uploaded_file is not None:
    with st.spinner('Scanning all 16 pages...'):
        all_rows = []
        
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    for row in table:
                        # Clean each cell to remove None and extra spaces
                        clean_row = [str(item).strip() if item is not None else "" for item in row]
                        
                        # Identify transaction rows by date pattern (e.g., 02/02/2026)
                        if clean_row and len(clean_row) >= 3:
                            first_cell = clean_row[0]
                            # Check for the date format common in your file
                            if "/" in first_cell and any(char.isdigit() for char in first_cell):
                                # Skip header repetitions found on multiple pages
                                if "DATE" not in first_cell.upper():
                                    all_rows.append(clean_row[:3])

        if all_rows:
            # Create DataFrame
            df = pd.DataFrame(all_rows, columns=["Date & Time", "Description", "Amount"])
            
            # Clean data for Excel: Remove symbols and handle multi-line text
            df["Description"] = df["Description"].str.replace('\n', ' ', regex=True)
            df["Amount"] = (df["Amount"]
                            .str.replace('₹', '', regex=True)
                            .str.replace(',', '', regex=True)
                            .str.replace('+', '', regex=True)
                            .str.strip())

            st.success(f"Found {len(df)} transactions!")
            st.dataframe(df, use_container_width=True)

            # Export to Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Domestic_Transactions')
            
            st.download_button(
                label="📥 Download Excel File",
                data=output.getvalue(),
                file_name="HDFC_Domestic_Transactions_Feb26.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("No transactions found. Ensure the PDF is not password protected.")
