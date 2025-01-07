import streamlit as st
import requests
import re
import qrcode
from io import BytesIO
from datetime import datetime
from streamlit_qrcode_scanner import qrcode_scanner
import calculation_data
import numpy as np

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
            # Actualizar el estado de la sesión
            st.session_state.fhir_server_url = fhir_server_url
            st.session_state.patient_id = patient_id
            
            # Obtener los datos del paciente
            patient_data = response.json()
            print(patient_data)
            
            # Mostrar mensaje de éxito si no estamos en medio de una recarga
            #if not st.session_state.get('_is_reloading'):
            st.session_state.patient_name = f"{patient_data.get('name', [{}])[0].get('given', [''])[0]} {patient_data.get('name', [{}])[0].get('family', '')}"
            #st.success(f"Patient found: {patient_name}")
            
            return patient_data
        else:
            st.session_state.fhir_server_url = None
            st.session_state.patient_id = None
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

def calculate_patient_data(patient_id):
    """
    Get all the data from the IPS Composition of the given patient
    Needed for timeline and laboratory results
    Args:
        patient_id (str): The patient's ID
    """
    # get data
    if patient_id:

        resource = {}
        composition_data = {}

        # if there is the history version to visualize diabetes data (just valued in code (manual))
        if st.session_state.history and patient_id == "UC4-Patient":
            resource = {}
            composition_data = calculation_data.fetch_fhir_data(f"https://ips-challenge.it.hs-heilbronn.de/fhir/Composition?patient={patient_id}")
            try:
                composition_data = calculation_data.fetch_fhir_data("https://ips-challenge.it.hs-heilbronn.de/fhir/Composition/UC4-Composition/_history/51")
            except Exception:
                print("No history data of the patients composition available.")
            if not composition_data:
                st.error("No data found for the patient. Please check the patient ID or data source.")
                st.stop()

            if "entry" in composition_data:
                resource = composition_data["entry"][0]["resource"]
            else:
                resource = composition_data

            if not resource:
                st.error("No data found for the patient. Please check the patient ID or data source.")
                st.stop()
        # else: other patient or we dont want to see the history version
        else:
            composition_data = calculation_data.fetch_fhir_data(f"https://ips-challenge.it.hs-heilbronn.de/fhir/Composition?patient={patient_id}")
            if not composition_data or "entry" not in composition_data:
                st.error("No data found for the patient. Please check the patient ID or data source.")
                st.stop()

            resource = composition_data["entry"][0]["resource"]

        timeline_data = []

        # Loinc Code:             ...["code"]["Coding"][0]["code"]

        # Medication Summary:      10160-0 MedicationStatement | MedicationRequest | MedicationAdministration | MedicationDispense
        # Allergies Summary:       48765-2 Allergy Intollerance
        # Problems Summary:  	   11450-4 Condition
        # Results Summary:         30954-2 Observation | DiagnosticReport
        # Vital Signs Summary:     8716-3  Observation
        # Social History Summary:  29762-2 Observation

        # Immunizations:           ?       Immunizations
        # History of Procedures:   47519-4  (?) Procedures
        # Medical Devices:         ?       DeviceUseStatement
        # Advance Directives:      42348-3  (?) Consent
        # Alerts:                  104605-1 (?) Flag
        # Functional Status:       8671-0   (?) Condition | ClinicalImpression
        # History of Past Illness: 11349-8  (?) Condition
        # History of Pregnancy:    67471-3  (?) Observation
        # Patient Story:           -
        # Plan of Care:            ?       CarePlan

        for section in resource["section"]:
            if section["code"]["coding"][0]["code"] == "10160-0" or\
                section["code"]["coding"][0]["code"] == "11450-4" or\
                section["code"]["coding"][0]["code"] == "30954-2" or\
                section["code"]["coding"][0]["code"] == "48765-2" or\
                section["code"]["coding"][0]["code"] == "8716-3" or\
                section["code"]["coding"][0]["code"] == "29762-2":
                for entry in section["entry"]:
                    if "reference" in entry:
                        clinical_data = calculation_data.search_for_clinical_data(entry["reference"])
                        if section["code"]["coding"][0]["code"] == "10160-0": # Medication
                            # MedicationStatement | MedicationRequest | MedicationAdministration | MedicationDispense
                            calculation_data.extract_timeline_data_encounter(timeline_data, clinical_data)
                        if section["code"]["coding"][0]["code"] == "11450-4": # Problems
                            # Condition
                            calculation_data.extract_timeline_data_condition(timeline_data, clinical_data)
                        if section["code"]["coding"][0]["code"] == "30954-2": # Results
                            # Observation | DiagnosticReport
                            calculation_data.extract_timeline_data_observation(timeline_data, clinical_data)
                        if section["code"]["coding"][0]["code"] == "48765-2": # Allergies
                            # Allergy Intollerance
                            calculation_data.extract_timeline_data_intolerance(timeline_data, clinical_data)
                        if section["code"]["coding"][0]["code"] == "8716-3": # Vital
                            # Observation
                            calculation_data.extract_timeline_data_vital(timeline_data, clinical_data)
                        if section["code"]["coding"][0]["code"] == "29762-2": # Social
                            # Observation
                            calculation_data.extract_timeline_data_history(timeline_data, clinical_data)

        st.session_state['laboratory_data'] = timeline_data

def main():
    """Main function to run the Streamlit app"""
    st.title("Patient Search Portal")
    
    # Verificar si acabamos de cargar un paciente
    if st.session_state.get('patient_id') and not st.session_state.get('_is_reloading'):
        patient_name = st.session_state.get('patient_name', '')
        st.success(f"Patient found: {patient_name}")
        #st.session_state._is_reloading = True
    
    # Radio buttons for search method
    search_method = st.radio("Choose search method:", 
                           ["Manual ID Entry", "QR Code Scanner", "Generate QR"])

    if search_method == "Manual ID Entry":
        fhir_server_url = st.text_input("Enter FHIR Server URL", "https://ips-challenge.it.hs-heilbronn.de/fhir/")
        patient_id = st.text_input("Enter Patient ID")
        if st.button("Search"):
            if patient_id:
                with st.spinner('Searching for patient...'):
                    st.session_state._is_reloading = True
                    patient_data = search_patient(fhir_server_url, patient_id)
                    if patient_data:
                        calculate_patient_data(patient_id)
                        # Recargar la página sin mostrar el mensaje de éxito
                        # El mensaje se mostrará en la siguiente carga
                        st.session_state._is_reloading = False
                        st.rerun()
                    else:
                        st.error("Patient not found")
            else:
                st.warning("Please enter a patient ID")

    elif search_method == "QR Code Scanner":
        qr_code = qrcode_scanner()
        if qr_code:
            with st.spinner('Searching for patient...'):
                # Extract patient ID from QR code URL
                match = re.search(r"Patient/([^/]+)$", qr_code)
                if match:
                    patient_id = match.group(1)
                    # Extract FHIR server URL
                    fhir_server_url = qr_code[:qr_code.index("Patient/")]
                    patient_data = search_patient(fhir_server_url, patient_id)
                    if patient_data:
                        calculate_patient_data(patient_id)
                        # Recargar la página sin mostrar el mensaje de éxito
                        st.rerun()
                    else:
                        st.error("Patient not found")
                else:
                    st.error("Invalid QR code format")

    else:  # Generate QR
        st.subheader("Generate QR Code and Consent")
        fhir_server_url = st.text_input("Enter FHIR Server URL for QR Generation", "https://ips-challenge.it.hs-heilbronn.de/fhir/")
        patient_id = st.text_input("Enter Patient ID for QR Generation")
        
        # Add digital signature canvas
        st.write("Digital Signature:")
        st.write("Please sign below to provide your consent:")
        
        from streamlit_drawable_canvas import st_canvas
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",
            stroke_width=2,
            stroke_color="#000000",
            background_color="#ffffff",
            height=150,
            drawing_mode="freedraw",
            key="signature_canvas"
        )
        
        if st.button("Accept Consent and Generate QR"):
            if not patient_id:
                st.warning("Please enter a Patient ID")
                return
            
            if canvas_result.image_data is None or not np.any(canvas_result.image_data):
                st.error("Please sign the document before proceeding")
                return
                
            try:
                # Verify if patient exists
                patient_data = search_patient(fhir_server_url, patient_id)
                if not patient_data:
                    st.error("Patient not found with the provided ID")
                    return
                
                # Get patient name if available
                patient_name = f"{patient_data.get('name', [{}])[0].get('given', [''])[0]} {patient_data.get('name', [{}])[0].get('family', '')}"
                
                # Data for consent
                patient_info = {
                    'name': patient_name.strip(),
                    'id': patient_id
                }
                
                # Generate QR
                qr_image = generate_patient_qr(fhir_server_url, patient_id)
                
                # QR data
                qr_data = f"FHIR Server: {fhir_server_url}\nPatient ID: {patient_id}\nDate: {datetime.now().strftime('%B %d, %Y')}"
                
                # Generate PDF
                from views.consent import generate_consent_pdf
                pdf_buffer = generate_consent_pdf(patient_info, canvas_result.image_data, qr_data, qr_image)
                
                # Download button
                st.download_button(
                    label="Download Consent and QR Code",
                    data=pdf_buffer,
                    file_name=f"consent_qr_{patient_id}.pdf",
                    mime="application/pdf"
                )
                
                st.success("QR code and consent form generated successfully")
                
            except Exception as e:
                st.error(f"An error occurred while generating the consent: {str(e)}")

# Run the Streamlit app
if __name__ == "__page__":
    main()