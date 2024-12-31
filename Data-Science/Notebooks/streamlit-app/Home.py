import streamlit as st
from fir_scraper import scrape_firs
st.title("FIR Scraper and Data Extractor")
st.markdown("""
Welcome to the FIR Scraper and Data Extractor app.
Use the sidebar to navigate between scraping FIRs and extracting data.
""")

if st.button("Go to Step 1: Scrape FIRs"):
    st.experimental_set_query_params(page="Step1_Scrape_FIRs")
    st.header("Step 1: Scrape FIRs")
    district_id = st.text_input("Enter District ID (e.g., 5)", "5")
    fir_start = st.number_input("Enter FIR Start Number", min_value=1, value=1)
    fir_end = st.number_input("Enter FIR End Number", min_value=1, value=5)
    output_dir = st.text_input("Output Directory for FIRs", "./output")

    if st.button("Scrape FIRs"):
        try:
            scrape_firs(district_id, fir_start, fir_end, output_dir)
            st.success("FIR scraping completed successfully!")
        except Exception as e:
            st.error(f"An error occurred: {e}")

if st.button("Go to Step 2: Extract Data"):
    st.experimental_set_query_params(page="Step2_Extract_Data")
    st.header("Step 2: Extract Data from FIRs")
    uploaded_files = st.file_uploader("Upload FIR PDFs", accept_multiple_files=True)
    csv_output_path = st.text_input("CSV Output File Path", "./output/fir_data.csv")

    if st.button("Extract Data"):
        try:
            if not uploaded_files:
                st.warning("Please upload at least one FIR PDF.")
            else:
                extract_fir_data(uploaded_files, csv_output_path)
                st.success(f"Data extraction completed! Saved to {csv_output_path}")
        except Exception as e:
            st.error(f"An error occurred: {e}")