import os
import tempfile
from pathlib import Path
import pandas as pd
import streamlit as st
import pdfplumber
import re
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class PropertyDetails:
    """Data class for stolen/involved property information"""
    sl_no: int
    property_type: Optional[str] = None
    item_description: Dict[str, Any] = None
    estimated_value: Optional[float] = None

@dataclass
class VictimDetails:
    """Data class for victim information"""
    sl_no: int
    name: Optional[str] = None
    address: Optional[str] = None
    injury_type: Optional[str] = None
    sex: Optional[str] = None
    age: Optional[int] = None
    occupation: Optional[str] = None

@dataclass
class FIRData:
    """Data class to store extracted FIR information"""
    district: Optional[str] = None
    circle_subdivision: Optional[str] = None
    police_station: Optional[str] = None
    crime_no: Optional[str] = None
    fir_date: Optional[datetime] = None
    act_section: Optional[str] = None
    offense_date: Optional[datetime] = None
    offense_time_from: Optional[str] = None
    offense_time_to: Optional[str] = None
    location: Optional[str] = None
    distance_ps: Optional[str] = None
    complainant_name: Optional[str] = None
    complainant_age: Optional[int] = None
    complainant_religion: Optional[str] = None
    complainant_caste: Optional[str] = None
    complainant_occupation: Optional[str] = None
    phone_number: Optional[str] = None
    nationality: Optional[str] = None
    sex: Optional[str] = None
    complainant_address: Optional[str] = None
    victim_details: List[VictimDetails] = None
    property_details: List[PropertyDetails] = None
    total_property_value: Optional[float] = None

    def __post_init__(self):
        if self.victim_details is None:
            self.victim_details = []
        if self.property_details is None:
            self.property_details = []

def safe_search(pattern: str, text: str, group_num: int = 1) -> Optional[str]:
    """Helper function to safely perform regex search and return the matched group or None."""
    try:
        match = re.search(pattern, text)
        return match.group(group_num).strip() if match else None
    except (AttributeError, IndexError):
        return None

def safe_parse_date(date_str: Optional[str], format_str: str = "%d/%m/%Y") -> Optional[datetime]:
    """Safely parse date string to datetime object."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, format_str)
    except ValueError:
        return None

def safe_parse_int(value: Optional[str]) -> Optional[int]:
    """Safely parse string to integer."""
    if not value:
        return None
    try:
        return int(re.sub(r'[^\d]', '', value))
    except ValueError:
        return None

def safe_parse_float(amount_str: Optional[str]) -> Optional[float]:
    """Safely parse string to float, handling commas in numbers."""
    if not amount_str:
        return None
    try:
        return float(amount_str.replace(',', ''))
    except ValueError:
        return None

def extract_property_details(text: str) -> List[PropertyDetails]:
    properties = []
    
    # Find all property entries using registration numbers as anchor points
    reg_numbers = re.finditer(r"Reg No:\s*(KA\d+[A-Z]+\d+)", text)
    reg_positions = [(m.group(1), m.start()) for m in reg_numbers]
    
    if not reg_positions:
        return properties
    
    for idx, (reg_no, start_pos) in enumerate(reg_positions):
        end_pos = reg_positions[idx + 1][1] if idx < len(reg_positions) - 1 else len(text)
        property_text = text[start_pos:end_pos]
        
        item_desc = {
            "reg_no": reg_no,
            "make": safe_search(r"Make:?\s*([^\n]+?)(?=\s*Model|$)", property_text),
            "model": safe_search(r"Model:?\s*([^\n]+?)(?=\s*Engine|$)", property_text),
            "engine_no": safe_search(r"Engine No:?\s*([^\n]+?)(?=\s*Chassis|$)", property_text),
            "chassis_no": safe_search(r"Chassis No:?\s*([^\n]+?)(?=\n|$)", property_text)
        }
        
        value_str = safe_search(r"Estimated Value\s*\([^)]*\)\s*\n*\s*([\d,]+)", text)
        estimated_value = safe_parse_float(value_str) or 0
        
        properties.append(PropertyDetails(
            sl_no=idx + 1,
            property_type="Automobile",
            item_description=item_desc,
            estimated_value=estimated_value
        ))
    
    return properties

def extract_fir_data(pdf_path: str) -> FIRData:
    """Extract relevant information from FIR PDF document with error handling"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = " ".join([page.extract_text() for page in pdf.pages])
            
            # Basic FIR details
            district = safe_search(r"District\s*:\s*([^:\n]+?)(?=\s+Circle/Sub Division|$)", text)
            circle = safe_search(r"Circle/Sub Division\s*:\s*([^:\n]+?)(?=\s+PS|$)", text)
            ps = safe_search(r"PS\s*:\s*([^:\n]+?)(?=\s*$|\s*\n)", text)
            crime_no = safe_search(r"Crime No\s*:\s*([^:\n]+?)(?=\s+FIR Date|$)", text)
            
            # Dates and times
            fir_date_str = safe_search(r"FIR Date\s*:\s*(\d{2}/\d{1,2}/\d{4})", text)
            fir_date = safe_parse_date(fir_date_str)
            
            offense_date_str = safe_search(r"From Date\s*:\s*(\d{2}/\d{2}/\d{4})", text)
            offense_date = safe_parse_date(offense_date_str)
            
            time_from = safe_search(r"From Time\s*:\s*(\d{2}:\d{2}:\d{2})", text)
            time_to = safe_search(r"To Time\s*:\s*(\d{2}:\d{2}:\d{2})", text)
            
            # Location and distance
            location = safe_search(r"Place of occurence with full address\s*(.*?)(?=\(b\))", text, re.DOTALL)
            distance_match = re.search(r"(?:(Tow(?:ards|ords)\s+\w+)\s*([\d\.]+)\s*(K\s*M|KM|Km|KMs|Meters|M)?)|(?:([\d\.]+)\s*(K\s*M|KM|Km|KMs|Meters|M)?\s*(Tow(?:ards|ords)\s+\w+))", text, re.IGNORECASE)
            
            distance_ps = None
            if distance_match:
                direction = (distance_match.group(1) or distance_match.group(6) or "").strip()
                distance_value = (distance_match.group(2) or distance_match.group(4) or "").strip()
                distance_unit = (distance_match.group(3) or distance_match.group(5) or "").strip()
                if direction and distance_value:
                    distance_ps = f"{direction}, {distance_value} {distance_unit}".strip()
            
            # Complainant details
            complainant_name = safe_search(r"Name\s*:\s*([^:\n]+?)(?=\s+Father)", text)
            complainant_age_str = safe_search(r"Age\s*:\s*(\d+)", text)
            complainant_age = safe_parse_int(complainant_age_str)
            complainant_religion = safe_search(r"Religion\s*:\s*([^:\n]+?)(?=\s*(?:\([e-z]\)|$))", text)
            complainant_caste = safe_search(r"Caste\s*:\s*([^:\n]+?)(?=\s*(?:\([f-z]\)|$))", text)
            complainant_occupation = safe_search(r"Occupation\s*:\s*([^\n]*)", text)
            phone_number = safe_search(r"Phone No\.\s*:\s*(\d+)", text)
            nationality = safe_search(r"Nationality\s*:\s*([^:\n]+?)(?=\s|$)", text)
            sex = safe_search(r"Sex:\s*([^:\n]+?)(?=\s|$)", text)
            
            # Address extraction
            address_match = safe_search(r"\(k\)\s*Address\s*:\s*([\s\S]*?)(?=\([m-z]\)|Whether complainant|$)", text)
            complainant_address = None
            if address_match:
                address_text = address_match
                sex_pattern = r"\(l\)\s*Sex:\s*[A-Za-z]+\s*"
                address_text = re.sub(sex_pattern, "", address_text)
                complainant_address = " ".join(line.strip() for line in address_text.split('\n') if line.strip())
            
            # Property details
            property_details = extract_property_details(text)
            
            # Total value
            total_value_str = safe_search(r"Total Value[^:]*:?\s*(?:Rs\.?)?\s*(\d+,?\d*)", text)
            total_property_value = safe_parse_float(total_value_str)
            
            act_section = safe_search(r"Act & Section\s*:\s*([^:\n]+)", text)
            
            return FIRData(
                district=district,
                circle_subdivision=circle,
                police_station=ps,
                crime_no=crime_no,
                fir_date=fir_date,
                act_section=act_section,
                offense_date=offense_date,
                offense_time_from=time_from,
                offense_time_to=time_to,
                location=location,
                distance_ps=distance_ps,
                complainant_name=complainant_name,
                complainant_age=complainant_age,
                complainant_religion=complainant_religion,
                complainant_caste=complainant_caste,
                complainant_occupation=complainant_occupation,
                phone_number=phone_number,
                nationality=nationality,
                sex=sex,
                complainant_address=complainant_address,
                victim_details=[],
                property_details=property_details,
                total_property_value=total_property_value
            )
            
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
        return FIRData()

def create_flat_dict(fir: FIRData) -> Dict[str, Any]:
    """Convert FIR data to a flat dictionary suitable for CSV export"""
    flat_dict = {
        'district': fir.district,
        'circle_subdivision': fir.circle_subdivision,
        'police_station': fir.police_station,
        'crime_no': fir.crime_no,
        'fir_date': fir.fir_date.strftime('%d/%m/%Y') if fir.fir_date else None,
        'act_section': fir.act_section,
        'offense_date': fir.offense_date.strftime('%d/%m/%Y') if fir.offense_date else None,
        'offense_time_from': fir.offense_time_from,
        'offense_time_to': fir.offense_time_to,
        'location': fir.location,
        'distance_ps': fir.distance_ps,
        'complainant_name': fir.complainant_name,
        'complainant_age': fir.complainant_age,
        'complainant_religion': fir.complainant_religion,
        'complainant_caste': fir.complainant_caste,
        'complainant_occupation': fir.complainant_occupation,
        'phone_number': fir.phone_number,
        'nationality': fir.nationality,
        'sex': fir.sex,
        'complainant_address': fir.complainant_address,
        'total_property_value': fir.total_property_value
    }

    # Add property details
    if fir.property_details:
        for i, prop in enumerate(fir.property_details, 1):
            prefix = f'property_{i}_'
            flat_dict[f'{prefix}type'] = prop.property_type
            flat_dict[f'{prefix}value'] = prop.estimated_value
            if prop.item_description:
                for key, value in prop.item_description.items():
                    flat_dict[f'{prefix}{key}'] = value

    return flat_dict

def process_uploaded_files(uploaded_files, csv_output_path: str) -> int:
    """Process uploaded files through Streamlit's file uploader"""
    all_data = []
    progress_bar = st.progress(0)
    
    for i, uploaded_file in enumerate(uploaded_files):
        progress = (i + 1) / len(uploaded_files)
        progress_bar.progress(progress)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_file_path = tmp_file.name
        
        try:
            fir = extract_fir_data(tmp_file_path)
            flat_data = create_flat_dict(fir)
            flat_data['file_name'] = uploaded_file.name
            all_data.append(flat_data)
        except Exception as e:
            st.warning(f"Failed to process {uploaded_file.name}: {str(e)}")
        finally:
            os.unlink(tmp_file_path)
    
    if all_data:
        df = pd.DataFrame(all_data)
        os.makedirs(os.path.dirname(csv_output_path), exist_ok=True)
        df.to_csv(csv_output_path, index=False, encoding='utf-8')
        return len(all_data)
    return 0

def process_directory_files(input_dir: str, csv_output_path: str) -> int:
    """Process FIR PDFs from the directory structure"""
    all_data = []
    pdf_files = []
    
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))
    
    if not pdf_files:
        st.warning(f"No PDF files found in {input_dir}")
        return 0
    
    progress_bar = st.progress(0)
    for i, pdf_file in enumerate(pdf_files):
        progress = (i + 1) / len(pdf_files)
        progress_bar.progress(progress)
        
        try:
            fir = extract_fir_data(pdf_file)
            flat_data = create_flat_dict(fir)
            flat_data['file_name'] = os.path.basename(pdf_file)
            all_data.append(flat_data)
        except Exception as e:
            st.warning(f"Failed to process {os.path.basename(pdf_file)}: {str(e)}")
    
    if all_data:
        df = pd.DataFrame(all_data)
        os.makedirs(os.path.dirname(csv_output_path), exist_ok=True)
        df.to_csv(csv_output_path, index=False, encoding='utf-8')
        return len(all_data)
    return 0

def extract_data(input_source, csv_output_path: str) -> int:
    """
    Extract data from FIR PDFs and save to CSV.
    
    Args:
        input_source: Either list of uploaded files or directory path
        csv_output_path: Path where the CSV file will be saved
        
    Returns:
        int: Number of successfully processed files
    """
    try:
        # Handle uploaded files
        if isinstance(input_source, list):
            return process_uploaded_files(input_source, csv_output_path)
            
        # Handle directory processing
        elif isinstance(input_source, str):
            return process_directory_files(input_source, csv_output_path)
            
        else:
            st.error("Invalid input source")
            return 0
            
    except Exception as e:
        st.error(f"Error during data extraction: {str(e)}")
        return 0

if __name__ == "__main__":
    # Example usage
    input_dir = "./output"  # Folder containing FIR PDFs
    output_file = "./output/fir_dataset.csv"  # Where to save the CSV
    
    processed_count = process_directory_files(input_dir, output_file)
    print(f"Successfully processed {processed_count} files")