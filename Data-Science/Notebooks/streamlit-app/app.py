import streamlit as st
import os
from fir_scraper import scrape_firs
from data_extractor import extract_data


config_dir = os.path.expanduser("~/.streamlit")
config_file = os.path.join(config_dir, "config.toml")

if not os.path.exists(config_dir):
    os.makedirs(config_dir)

with open(config_file, "w") as f:
    f.write("[theme]\nbase = 'dark'\n")


st.title("FIR Scraper and Data Extractor")
st.markdown("""
Welcome to the Karnataka State Police FIR Scraper and Data Extractor app!
""")
menu = st.radio("Select", ["Scrape FIRs", "Extract Data"])

if menu == "Scrape FIRs":
    st.header("Step 1: Scrape FIRs")

    district_id = st.text_input("Enter District ID", "5")
    fir_start = st.number_input("Enter FIR Start Number", min_value=1, value=1)
    fir_end = st.number_input("Enter FIR End Number", min_value=1, value=5)
    year = st.text_input("Enter Year", "2024")
    output_dir = st.text_input("Output Directory for FIRs", "./output")

    if st.button("Scrape FIRs"):
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            with st.spinner("Scraping FIRs..."):
                scrape_firs(district_id, fir_start, fir_end, year, output_dir)
            st.success("FIR scraping completed successfully!")
        except Exception as e:
            st.error(f"An error occurred: {e}")

    if "stop_scraping" not in st.session_state:
        st.session_state.stop_scraping = False

    if st.button("Stop Scraping"):
        st.session_state.stop_scraping = True
        st.info("Scraping process will stop after the current iteration.")

elif menu == "Extract Data":
    st.header("Step 2: Extract Data from FIRs")
    
    input_method = st.radio(
        "Choose input method",
        ["Upload Files", "Process Directory"]
    )
    
    csv_output_path = st.text_input("CSV Output File Path", "./output/fir_data.csv")
    
    if input_method == "Upload Files":
        uploaded_files = st.file_uploader("Upload FIR PDFs", accept_multiple_files=True)
        input_source = uploaded_files
    else:
        input_dir = st.text_input("Input Directory", "./output")
        input_source = input_dir

    if st.button("Extract Data"):
        try:
            if (input_method == "Upload Files" and not uploaded_files) or \
               (input_method == "Process Directory" and not input_dir):
                st.warning("Please provide input files or directory.")
            else:
                with st.spinner("Extracting data..."):
                    processed_count = extract_data(input_source, csv_output_path)
                    if processed_count > 0:
                        st.success(f"Successfully processed {processed_count} files! Data saved to {csv_output_path}")
                    else:
                        st.error("No files were successfully processed.")
        except Exception as e:
            st.error(f"An error occurred: {e}")
