import streamlit as st
import pdfplumber
import pandas as pd
from io import BytesIO
import re

st.set_page_config(page_title="HDFC Statement Converter", layout="wide")

st.title("💳 Transaction Extractor (Date & Time Split)")
st.write("Extracting Domestic Transactions from HDFC 'Card Feb-26.pdf'.")

uploaded_file = st.file_uploader("Upload Statement PDF", type="pdf")

if uploaded_file is not None:
    with st.spinner('Processing 16 pages...'):
        all_data = []
        
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    for row in table:
                        # Clean cells and remove None values
                        clean_row = [str(item).strip() if item is not None else "" for item in row]
                        
                        if clean_row and len(clean_row) >= 3:
                            raw_date_time = clean_row[0]
                            
                            # Regex to find "dd/mm/yyyy| hh:mm" or "dd/mm/yyyy hh:mm"
                            # Handles cases with and without the "|" pipe symbol
                            match = re.search(r'(\d{2}/\d{2}/\d{4})[|\s]*(\d{2}:\d{2})', raw_date_time)
                            
                            if match:
                                date = match.group(1)
                                time = match.group(2)
                                description = clean_row[1].replace('\n', ' ')
                                amount = clean_row[2]
                                
                                all_data.append([date, time, description, amount])

        if all_data:
            # Define 4 columns now that Time is separate
            df = pd.DataFrame(all_data, columns=["Date", "Time", "Description", "Amount"])
            
            # Clean Amount column for numerical use in Excel
            df["Amount"] = (df["Amount"]
                            .str.replace('₹', '', regex=False)
                            .str.replace(',', '', regex=False)
                            .str.replace('+', '', regex=False)
                            .str.strip())
            
            st.success(f"Extracted {len(df)} transactions with separate Time column.")
            st.dataframe(df, use_container_width=True)

            # Excel Conversion
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Domestic_Transactions')
            
            st.download_button(
                label="📥 Download Excel",
                data=output.getvalue(),
                file_name="HDFC_Transactions_Split.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("No transactions found. Ensure the layout matches the standard HDFC digital statement.")
