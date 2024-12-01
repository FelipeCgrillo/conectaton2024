import streamlit as st

import requests
import re

import qrcode
from io import BytesIO
from streamlit_qrcode_scanner import qrcode_scanner
import calculation_data

# Set page title and icon
st.set_page_config(page_title="Patient Search", page_icon="🩺")

#Initialize session states
if "patient_id" not in st.session_state:
    st.session_state.patient_id = None
if "fhir_server_url" not in st.session_state:
    st.session_state.fhir_server_url = None



def search_patient(fhir_server_url, patient_id):
    """
    Search for a patient using the given patient ID from the specified API endpoint.
    
    Args:
        patient_id (str): The unique identifier of the patient to search for
    
    Returns:
        dict or None: Patient data if found, None otherwise
    """
    try:
        # Construct the full URL with the patient ID
        #url = f"https://ips-challenge.it.hs-heilbronn.de/fhir/Patient/{patient_id}"
        regex = r"(https:\/\/[^\/]+\/fhir\/)"
        res = re.match(regex, fhir_server_url)
        if not res:
            st.warning("FHIR Server URL not valid.")
            return None
        
        url = fhir_server_url + "Patient/" + patient_id
        
        # Make a GET request to the API
        response = requests.get(url)
        
        # Check if the request was successful
        if response.status_code == 200:
            st.session_state.fhir_server_url = fhir_server_url
            st.session_state.patient_id = patient_id
            return response.json()
        else:
            st.session_state.fhir_server_url = None
            st.session_state.patient_id = None
            st.warning(f"FHIR Server returned status code {response.status_code}.")
            return None
    
    except requests.RequestException as e:
        st.error(f"An error occurred: {e}")
        return None


def search_patient_resource(fhir_server_url, patient_id, resource_type):
    """
    Generic function to search for any FHIR resource associated with a patient.
    
    Args:
        patient_id (str): The patient's ID
        resource_type (str): The FHIR resource type to search for
    Returns:
        list: List of resources or empty list if none found
    """
    try:
        #url = f"https://ips-challenge.it.hs-heilbronn.de/fhir/{resource_type}?patient={patient_id}"
        url = fhir_server_url + resource_type + "?patient=" + patient_id
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get('entry', [])
        return []
    except requests.RequestException as e:
        st.error(f"Error fetching {resource_type}: {e}")
        return []

def process_observations(observations):
    """Process and group observations by category"""
    grouped_observations = {}
    for entry in observations:
        obs = entry.get('resource', {})
        category = obs.get('category', [{}])[0].get('coding', [{}])[0].get('code', 'Other')
        
        if category not in grouped_observations:
            grouped_observations[category] = []
            
        grouped_observations[category].append({
            'Test': obs.get('code', {}).get('text', 
                   obs.get('code', {}).get('coding', [{}])[0].get('display', 'N/A')),
            'Value': f"{obs.get('valueQuantity', {}).get('value', 'N/A')} {obs.get('valueQuantity', {}).get('unit', '')}",
            'Date': obs.get('effectiveDateTime', 'N/A'),
            'Status': obs.get('status', 'N/A')
        })
    #sort by date ascending
    for category in grouped_observations.keys():
        grouped_observations[category] = sorted(grouped_observations[category], key=lambda d: d['Date'], reverse=True)

    return grouped_observations

def get_location_coordinates(address_str):
    """
    Get coordinates for an address using Nominatim geocoder.
    
    Args:
        address_str (str): Address string to geocode
    
    Returns:
        tuple: (latitude, longitude) or None if geocoding fails
    """
    try:
        import ssl
        import certifi
        
        ctx = ssl.create_default_context(cafile=certifi.where())
        geolocator = Nominatim(
            user_agent="patient_search_portal",
            ssl_context=ctx
        )
        
        location = geolocator.geocode(address_str, timeout=10)
        if location:
            return location.latitude, location.longitude
        return None
    except (GeocoderTimedOut, GeocoderUnavailable) as e:
        st.warning(f"Geocoding error: {e}")
        return None
    except Exception as e:
        st.warning(f"Error getting coordinates: {e}")
        return None


def generate_patient_qr(fhir_server_url, patient_id):
    """
    Generate QR code for a patient ID
    
    Args:
        patient_id (str): The patient's ID
    Returns:
        BytesIO: QR code image in bytes
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(fhir_server_url + "Patient/" + patient_id)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

def main():
    """
    Main Streamlit application function
    """
    st.title("Patient Search Portal")

    # Create tabs for different search methods
    search_method = st.radio(
        "Choose search method:",
        ["Manual ID Entry", "QR Code Scanner", "Generate QR"]
    )

    if search_method == "Manual ID Entry":
        # Input for FHIR Server URL
        fhir_server_url = st.text_input("Enter FHIR Server URL", value="https://ips-challenge.it.hs-heilbronn.de/fhir/")
        # Input for Patient ID
        patient_id = st.text_input("Enter Patient ID", value="UC4-Patient")
        
        # Search button
        if st.button("Search Patient"):
            if not fhir_server_url:
                st.warning("Please enter a FHIR Server URL")
            if not patient_id:
                st.warning("Please enter a Patient ID")
                
            
            with st.spinner('Searching for patient...'):
                patient_data = search_patient(fhir_server_url,patient_id)
                if patient_data:
                    st.rerun()
                else:
                    st.error("Patient not found.")
                #display_patient_info(patient_data)

    elif search_method == "QR Code Scanner":
        st.write("Scan QR Code")
        st.write("QR Code should contain link to FHIR Patient resource, for example https://ips-challenge.it.hs-heilbronn.de/fhir/Patient/UC4-Patient")
        qr_code = qrcode_scanner()
        
        if qr_code:
            with st.spinner('Searching for patient...'):
                regex = r"(https:\/\/[^/]+\/fhir\/)(Patient\/[^/]+)"
                match = re.match(regex, qr_code)
                if not len(match.groups()):
                    st.error(f"QR Code link is invalidly formatted: {qr_code}")
                fhir_server_url = match.groups()[0]
                patient_id = match.groups()[1].replace("Patient/","")
                patient_data = search_patient(fhir_server_url,patient_id)
                if patient_data:
                    st.rerun()
                else:
                    st.error("Patient not found.")

    elif search_method == "Generate QR":
        fhir_server_url = st.text_input("Enter FHIR Server URL for QR Generation", value="https://ips-challenge.it.hs-heilbronn.de/fhir/")
        patient_id = st.text_input("Enter Patient ID for QR Generation", 
                                    placeholder="Enter a valid Patient ID", value="UC4-Patient")
        
        if st.button("Generate QR"):
            if not fhir_server_url:
                st.warning("Please enter a FHIR Server URL")
            elif not patient_id:
                st.warning("Please enter a Patient ID")
            else:
                # Generate and display QR code
                qr_image = generate_patient_qr(fhir_server_url, patient_id)
                st.image(qr_image, caption=f"QR Code for Patient {patient_id}")
                
                # Add download button
                st.download_button(
                    label="Download QR Code",
                    data=qr_image,
                    file_name=f"patient_{patient_id}_qr.png",
                    mime="image/png"
                )
    if st.session_state.patient_id:
        st.success("Patient found!")

# Run the Streamlit app
if __name__ == "__page__":
    main()