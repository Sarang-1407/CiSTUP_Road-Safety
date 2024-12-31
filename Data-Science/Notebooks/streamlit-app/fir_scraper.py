import requests, os
from bs4 import BeautifulSoup
import streamlit as st

def scrape_firs(district_id, fir_start, fir_end, year, output_dir):
    url = "https://ksp.karnataka.gov.in/"
    stations_url = f"https://ksp.karnataka.gov.in/myform/ajax/{district_id}?unit_name={district_id}"

    try:
        stations = requests.get(stations_url).json()
    except Exception as e:
        print(f"Error fetching stations data: {e}")
        return
    
    if not stations:
        print(f"No stations found for district {district_id}")
        return

    ps_ids = [obj.get("station_id") for obj in stations if "station_id" in obj]

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0",
    }

    data = {
        "district_id": district_id,
        "knen": "en",
        "random_captcha": "LOL",
        "captcha": "LOL",
        "year": year,  
    }

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for ps_id in ps_ids:
        for num in range(fir_start, fir_end + 1):
            if st.session_state.stop_scraping:
                st.session_state.stop_scraping = False 
                print(f"Scraping stopped by user after processing FIR {data['fir_num']}")
                return
            
            data.update({"ps_id": ps_id, "fir_num": f"{num:04}"})
            
            try:
                response = requests.post("https://ksp.karnataka.gov.in/fir_search_new_s.php", headers=headers, data=data)
                response.raise_for_status()  
            except requests.exceptions.RequestException as e:
                print(f"Error fetching FIR {data['fir_num']} for station {ps_id}: {e}")
                continue

            if "FIR Not Found!" in response.text:
                print(f"FIR not found for station {ps_id} and FIR number {data['fir_num']}")
                continue

            soup = BeautifulSoup(response.content, "html.parser")
            a_tag = soup.find("a")

            if not a_tag or "href" not in a_tag.attrs:
                print(f"Error: PDF link not found for station {ps_id}, FIR {data['fir_num']}")
                continue
            
            pdf_url = url + a_tag["href"]

            ps_path = os.path.join(output_dir, str(ps_id))
            os.makedirs(ps_path, exist_ok=True)

            try:
                with open(f"{ps_path}/fir_{data['fir_num']}.pdf", "wb") as f:
                    f.write(requests.get(pdf_url).content)
                print(f"FIR {data['fir_num']} saved successfully for station {ps_id}")
            except Exception as e:
                print(f"Error saving FIR {data['fir_num']} for station {ps_id}: {e}")
