import streamlit as st
import requests
import folium
from streamlit_folium import folium_static

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

import qrcode
from io import BytesIO
from streamlit_qrcode_scanner import qrcode_scanner

# Agregar estas constantes al inicio del archivo
ENCOUNTER_TYPES = {
    "AMB": "Ambulatory",
    "EMER": "Emergency",
    "HH": "Home Health",
    "IMP": "Inpatient",
    "ACUTE": "Acute Care",
    "NONAC": "Non-Acute",
    "OBSENC": "Observation Encounter",
    "PRENC": "Pre-Admission",
    "SS": "Short Stay"
}

def search_patient(patient_id):
    """
    Search for a patient using the given patient ID from the specified API endpoint.
    
    Args:
        patient_id (str): The unique identifier of the patient to search for
    
    Returns:
        dict or None: Patient data if found, None otherwise
    """
    try:
        # Construct the full URL with the patient ID
        url = f"https://ips-challenge.it.hs-heilbronn.de/fhir/Patient/{patient_id}"
        
        # Make a GET request to the API
        response = requests.get(url)
        
        # Check if the request was successful
        if response.status_code == 200:
            return response.json()
        else:
            return None
    
    except requests.RequestException as e:
        st.error(f"An error occurred: {e}")
        return None

def search_patient_conditions(patient_id):
    """
    Search for conditions associated with a patient.
    
    Args:
        patient_id (str): The patient's ID
    Returns:
        list: List of conditions or empty list if none found
    """
    try:
        url = f"https://ips-challenge.it.hs-heilbronn.de/fhir/Condition?patient={patient_id}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get('entry', [])
        return []
    except requests.RequestException as e:
        st.error(f"Error fetching conditions: {e}")
        return []

def search_patient_medications(patient_id):
    """
    Search for medication requests associated with a patient.
    
    Args:
        patient_id (str): The patient's ID
    Returns:
        list: List of medication requests or empty list if none found
    """
    try:
        url = f"https://ips-challenge.it.hs-heilbronn.de/fhir/MedicationRequest?patient={patient_id}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get('entry', [])
        return []
    except requests.RequestException as e:
        st.error(f"Error fetching medications: {e}")
        return []

def search_patient_resource(patient_id, resource_type):
    """
    Generic function to search for any FHIR resource associated with a patient.
    
    Args:
        patient_id (str): The patient's ID
        resource_type (str): The FHIR resource type to search for
    Returns:
        list: List of resources or empty list if none found
    """
    try:
        url = f"https://ips-challenge.it.hs-heilbronn.de/fhir/{resource_type}?patient={patient_id}"
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
        category = obs.get('category', [{}])[0].get('coding', [{}])[0].get('display', 'Other')
        
        if category not in grouped_observations:
            grouped_observations[category] = []
            
        grouped_observations[category].append({
            'Test': obs.get('code', {}).get('text', 
                   obs.get('code', {}).get('coding', [{}])[0].get('display', 'N/A')),
            'Value': f"{obs.get('valueQuantity', {}).get('value', 'N/A')} {obs.get('valueQuantity', {}).get('unit', '')}",
            'Date': obs.get('effectiveDateTime', 'N/A'),
            'Status': obs.get('status', 'N/A')
        })
    return grouped_observations

def create_clinical_event(patient_id, event_data):
    """
    Creates a new clinical event for a patient.
    
    Args:
        patient_id (str): Patient ID
        event_data (dict): Clinical event data
    Returns:
        bool: True if created successfully, False otherwise
    """
    try:
        url = "https://ips-challenge.it.hs-heilbronn.de/fhir/Encounter"
        
        # FHIR resource structure for encounter
        encounter_resource = {
            "resourceType": "Encounter",
            "status": "finished",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": event_data['encounter_type'],
                "display": event_data['encounter_type']
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "period": {
                "start": event_data['date'],
                "end": event_data['date']
            },
            "type": [{
                "text": event_data['description']
            }],
            "reasonCode": [{
                "text": event_data['reason']
            }]
        }
        
        # Make POST request
        response = requests.post(
            url,
            json=encounter_resource,
            headers={"Content-Type": "application/fhir+json"}
        )
        
        return response.status_code == 201
    except requests.RequestException as e:
        st.error(f"Error creating clinical event: {e}")
        return False

def create_condition(patient_id, condition_data):
    """
    Creates a new condition for a patient.
    """
    try:
        url = "https://ips-challenge.it.hs-heilbronn.de/fhir/Condition"
        
        condition_resource = {
            "resourceType": "Condition",
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "clinicalStatus": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": condition_data['status'],
                    "display": condition_data['status']
                }]
            },
            "code": {
                "text": condition_data['condition']
            },
            "onsetDateTime": condition_data['onset_date']
        }
        
        response = requests.post(
            url,
            json=condition_resource,
            headers={"Content-Type": "application/fhir+json"}
        )
        return response.status_code == 201
    except requests.RequestException as e:
        st.error(f"Error creating condition: {e}")
        return False

def create_observation(patient_id, observation_data):
    """
    Creates a new observation for a patient.
    """
    try:
        url = "https://ips-challenge.it.hs-heilbronn.de/fhir/Observation"
        
        observation_resource = {
            "resourceType": "Observation",
            "status": "final",
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "code": {
                "text": observation_data['type']
            },
            "valueQuantity": {
                "value": observation_data['value'],
                "unit": observation_data['unit']
            },
            "effectiveDateTime": observation_data['date']
        }
        
        response = requests.post(
            url,
            json=observation_resource,
            headers={"Content-Type": "application/fhir+json"}
        )
        return response.status_code == 201
    except requests.RequestException as e:
        st.error(f"Error creating observation: {e}")
        return False

def create_diagnostic_report(patient_id, report_data):
    """
    Creates a new diagnostic report for a patient.
    """
    try:
        url = "https://ips-challenge.it.hs-heilbronn.de/fhir/DiagnosticReport"
        
        report_resource = {
            "resourceType": "DiagnosticReport",
            "status": "final",
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "code": {
                "text": report_data['type']
            },
            "effectiveDateTime": report_data['date'],
            "conclusion": report_data['conclusion']
        }
        
        response = requests.post(
            url,
            json=report_resource,
            headers={"Content-Type": "application/fhir+json"}
        )
        return response.status_code == 201
    except requests.RequestException as e:
        st.error(f"Error creating diagnostic report: {e}")
        return False

def display_patient_info(patient_data):
    if not patient_data:
        st.warning("No patient data found.")
        return
    
    st.success("Patient Found!")
    patient_id = patient_data.get('id')
    
    # Update tab names to English
    tabs = st.tabs(["Demographics", "Clinical", "Encounters & Procedures", "Reports & Results", "New Event"])
    
    with tabs[0]:  # Demographics
        # Basic Information Section
        st.markdown("### 👤 Basic Info")
        name = patient_data.get('name', [{}])[0].get('given', ['N/A'])[0] + " " + \
               patient_data.get('name', [{}])[0].get('family', 'N/A')
        gender = patient_data.get('gender', 'N/A')
        birthdate = patient_data.get('birthDate', 'N/A')
        
        st.markdown(f"**Name:** {name}")
        st.markdown(f"**Gender:** {gender}")
        st.markdown(f"**Birthdate:** {birthdate}")

        # Add some spacing
        st.markdown("---")

        # Contact Information Section
        st.markdown("### 📞 Contact Info")
        telecom = patient_data.get('telecom', [])
        for contact in telecom:
            system = contact.get('system', 'N/A')
            value = contact.get('value', 'N/A')
            st.markdown(f"**{system.title()}:** {value}")

        # Add some spacing
        st.markdown("---")

        # Address Information Section
        st.markdown("### 📍 Address")
        
        # Create two columns for address and map
        addr_col, map_col = st.columns([1, 1])
        
        address = patient_data.get('address', [{}])[0]
        if address:
            with addr_col:
                line = address.get('line', ['N/A'])[0]
                city = address.get('city', 'N/A')
                state = address.get('state', 'N/A')
                country = address.get('country', 'N/A')
                
                st.markdown(f"**Street:** {line}")
                st.markdown(f"**City:** {city}")
                st.markdown(f"**State:** {state}")
                st.markdown(f"**Country:** {country}")
            
            # Create address string for geocoding
            address_parts = []
            if line != 'N/A':
                address_parts.append(line)
            if city != 'N/A':
                address_parts.append(city)
            if state != 'N/A':
                address_parts.append(state)
            if country != 'N/A':
                address_parts.append(country)
            
            if address_parts:
                address_str = ", ".join(address_parts)
                coordinates = get_location_coordinates(address_str)
                
                if coordinates:
                    with map_col:
                        # Create the map with improved styling
                        m = folium.Map(
                            location=coordinates,
                            zoom_start=15,
                            width='100%',
                            height='100%'
                        )
                        
                        # Add a marker with a popup containing the address
                        folium.Marker(
                            coordinates,
                            popup=folium.Popup(address_str, max_width=300),
                            tooltip="Patient's Location",
                            icon=folium.Icon(
                                color='red',
                                icon='info-sign',
                                prefix='fa'
                            )
                        ).add_to(m)
                        
                        # Add a circle around the location
                        folium.Circle(
                            coordinates,
                            radius=100,
                            color='red',
                            fill=True,
                            fillOpacity=0.2
                        ).add_to(m)
                        
                        # Display the map with custom size
                        folium_static(m, width=400, height=300)  # Adjusted size for column
                else:
                    with map_col:
                        st.info("Location could not be displayed on map")

        # Add some spacing
        st.markdown("---")

        # Rest of the sections (Identifiers, Extensions, etc.)
        st.markdown("### 🆔 Identifiers")
        if 'identifier' in patient_data:
            identifiers_data = []
            for identifier in patient_data['identifier']:
                identifiers_data.append({
                    'System': identifier.get('system', 'N/A'),
                    'Value': identifier.get('value', 'N/A'),
                    'Type': identifier.get('type', {}).get('text', 'N/A')
                })
            if identifiers_data:
                st.table(identifiers_data)

        # Extensions Table
        if 'extension' in patient_data:
            st.markdown("### 📑 Extensions")
            extensions_data = []
            for extension in patient_data['extension']:
                extensions_data.append({
                    'URL': extension.get('url', 'N/A'),
                    'Value': str(extension.get('valueString', extension.get('valueCode', 'N/A')))
                })
            if extensions_data:
                st.table(extensions_data)

        # Communication Preferences
        if 'communication' in patient_data:
            st.markdown("### 🗣️ Communication Preferences")
            comm_data = []
            for comm in patient_data['communication']:
                language = comm.get('language', {}).get('text', 'N/A')
                preferred = comm.get('preferred', False)
                comm_data.append({
                    'Language': language,
                    'Preferred': '✓' if preferred else '✗'
                })
            if comm_data:
                st.table(comm_data)

    with tabs[1]:  # Clinical
        # Conditions Section
        with st.expander("🏥 Conditions", expanded=True):
            conditions = search_patient_resource(patient_id, "Condition")
            if conditions:
                conditions_data = []
                for entry in conditions:
                    condition = entry.get('resource', {})
                    
                    # Get clinical status properly
                    clinical_status = condition.get('clinicalStatus', {}).get('coding', [{}])[0]
                    status = clinical_status.get('code', 'N/A')
                    
                    # Convert status codes to more readable format
                    status_display = {
                        'active': 'Ongoing',
                        'resolved': 'Finished',
                        'inactive': 'Inactive',
                        'remission': 'In Remission',
                        'recurrence': 'Recurrence'
                    }.get(status, status)
                    
                    conditions_data.append({
                        'Condition': condition.get('code', {}).get('text', 
                                     condition.get('code', {}).get('coding', [{}])[0].get('display', 'N/A')),
                        'Status': status_display,
                        'Onset': condition.get('onsetDateTime', 'N/A'),
                        'Recorded Date': condition.get('recordedDate', 'N/A')
                    })
                    
                # Sort conditions by date, with ongoing conditions first
                conditions_data.sort(key=lambda x: (
                    x['Status'] != 'Ongoing',  # Ongoing conditions first
                    x['Onset'] if x['Onset'] != 'N/A' else ''
                ), reverse=False)
                
                st.table(conditions_data)
                
                # Display count of ongoing conditions
                ongoing_count = sum(1 for c in conditions_data if c['Status'] == 'Ongoing')
                st.markdown(f"*Active conditions: {ongoing_count} of {len(conditions_data)}*")
            else:
                st.info("No conditions recorded")

        # Medications Section
        with st.expander("💊 Medications", expanded=True):
            medications = search_patient_resource(patient_id, "MedicationRequest")
            if medications:
                medications_data = []
                for entry in medications:
                    medication = entry.get('resource', {})
                    med_code = medication.get('medicationCodeableConcept', {})
                    medications_data.append({
                        'Medication': med_code.get('text', 
                                      med_code.get('coding', [{}])[0].get('display', 'N/A')),
                        'Status': medication.get('status', 'N/A'),
                        'Intent': medication.get('intent', 'N/A'),
                        'Authored': medication.get('authoredOn', 'N/A')
                    })
                if medications_data:
                    st.table(medications_data)
            else:
                st.info("No medications recorded")

        # Allergies Section
        with st.expander("⚠️ Allergies", expanded=True):
            allergies = search_patient_resource(patient_id, "AllergyIntolerance")
            if allergies:
                allergies_data = []
                for entry in allergies:
                    allergy = entry.get('resource', {})
                    allergies_data.append({
                        'Allergy': allergy.get('code', {}).get('text', 'N/A'),
                        'Type': allergy.get('type', 'N/A'),
                        'Category': ', '.join(allergy.get('category', [])),
                        'Criticality': allergy.get('criticality', 'N/A')
                    })
                st.table(allergies_data)
            else:
                st.info("No allergies recorded")

        # Immunizations Section
        with st.expander("💉 Immunizations", expanded=True):
            immunizations = search_patient_resource(patient_id, "Immunization")
            if immunizations:
                immunizations_data = []
                for entry in immunizations:
                    immunization = entry.get('resource', {})
                    # Get vaccine code details
                    vaccine_code = immunization.get('vaccineCode', {})
                    # Try to get the vaccine name from coding array first
                    vaccine_name = 'N/A'
                    if 'coding' in vaccine_code:
                        for coding in vaccine_code['coding']:
                            # Check for display name or specific COVID-19 vaccine codes
                            if coding.get('display'):
                                vaccine_name = coding.get('display')
                                break
                            # If no display name, try to get the code
                            elif coding.get('code'):
                                vaccine_name = f"Code: {coding.get('code')}"
                                break
                    # Fallback to text if no coding found
                    elif vaccine_code.get('text'):
                        vaccine_name = vaccine_code.get('text')
                    
                    # Get manufacturer if available
                    manufacturer = immunization.get('manufacturer', {}).get('display', 'N/A')
                    
                    # Get lot number
                    lot_number = immunization.get('lotNumber', 'N/A')
                    
                    immunizations_data.append({
                        'Vaccine': vaccine_name,
                        'Manufacturer': manufacturer,
                        'Lot Number': lot_number,
                        'Date': immunization.get('occurrenceDateTime', 'N/A'),
                        'Status': immunization.get('status', 'N/A'),
                        'Dose': immunization.get('protocolApplied', [{}])[0].get('doseNumber', {}).get('value', 'N/A')
                    })
                
                # Sort immunizations by date
                immunizations_data.sort(key=lambda x: x['Date'], reverse=True)
                st.table(immunizations_data)
                
                # Display total count
                st.markdown(f"*Total immunizations: {len(immunizations_data)}*")
            else:
                st.info("No immunizations recorded")

    with tabs[2]:  # Encounters & Procedures
        # Encounters Section
        with st.expander("🏥 Encounters", expanded=True):
            encounters = search_patient_resource(patient_id, "Encounter")
            if encounters:
                encounters_data = []
                for entry in encounters:
                    encounter = entry.get('resource', {})
                    
                    # Get encounter type from coding
                    encounter_type = 'N/A'
                    type_codings = encounter.get('type', [{}])[0].get('coding', [])
                    for coding in type_codings:
                        if coding.get('display'):
                            encounter_type = coding.get('display')
                            break
                        elif coding.get('code'):
                            encounter_type = f"Code: {coding.get('code')}"
                            break
                    
                    # Get encounter class
                    class_code = encounter.get('class', {})
                    encounter_class = class_code.get('code', 'N/A')
                    if class_code.get('display'):
                        encounter_class = class_code.get('display')
                    
                    # Get service type if available
                    service_type = 'N/A'
                    if 'serviceType' in encounter:
                        service_codings = encounter['serviceType'].get('coding', [])
                        for coding in service_codings:
                            if coding.get('display'):
                                service_type = coding.get('display')
                                break
                    
                    # Get service provider - handle both reference and display
                    service_provider = 'N/A'
                    provider_info = encounter.get('serviceProvider', {})
                    if 'display' in provider_info:
                        service_provider = provider_info['display']
                    elif 'reference' in provider_info:
                        service_provider = provider_info['reference'].split('/')[-1]
                    
                    # Get period start and end dates
                    period = encounter.get('period', {})
                    start_date = period.get('start', 'N/A')
                    end_date = period.get('end', 'N/A')
                    
                    encounters_data.append({
                        'Type': encounter_type,
                        'Class': encounter_class,
                        'Service': service_type,
                        'Provider': service_provider,
                        'Start Date': start_date,
                        'End Date': end_date,
                        'Status': encounter.get('status', 'N/A')
                    })
                
                # Sort encounters by start date
                encounters_data.sort(key=lambda x: x['Start Date'] if x['Start Date'] != 'N/A' else '', reverse=True)
                st.table(encounters_data)
                
                # Display total count
                st.markdown(f"*Total encounters: {len(encounters_data)}*")
            else:
                st.info("No encounters recorded")

        # Procedures Section
        with st.expander("⚕️ Procedures", expanded=True):
            procedures = search_patient_resource(patient_id, "Procedure")
            if procedures:
                procedures_data = []
                for entry in procedures:
                    procedure = entry.get('resource', {})
                    
                    # Get performed period if available
                    performed_period = procedure.get('performedPeriod', {})
                    start_date = performed_period.get('start', procedure.get('performedDateTime', 'N/A'))
                    end_date = performed_period.get('end', 'N/A')
                    
                    procedures_data.append({
                        'Procedure': procedure.get('code', {}).get('text', 'N/A'),
                        'Start Date': start_date,
                        'End Date': end_date,
                        'Status': procedure.get('status', 'N/A')
                    })
                    
                # Sort procedures by start date
                procedures_data.sort(key=lambda x: x['Start Date'] if x['Start Date'] != 'N/A' else '', reverse=True)
                st.table(procedures_data)
                
                # Display total count
                st.markdown(f"*Total procedures: {len(procedures_data)}*")
            else:
                st.info("No procedures recorded")

    with tabs[3]:  # Reports & Results
        # Observations Section
        observations = search_patient_resource(patient_id, "Observation")
        grouped_obs = process_observations(observations)
        
        for category, obs_data in grouped_obs.items():
            with st.expander(f"📊 {category} Observations", expanded=True):
                st.table(obs_data)
        
        if not grouped_obs:
            st.info("No observations recorded")

        # Diagnostic Reports Section
        with st.expander("📋 Diagnostic Reports", expanded=True):
            reports = search_patient_resource(patient_id, "DiagnosticReport")
            if reports:
                reports_data = []
                for entry in reports:
                    report = entry.get('resource', {})
                    reports_data.append({
                        'Report': report.get('code', {}).get('text', 'N/A'),
                        'Date': report.get('effectiveDateTime', 'N/A'),
                        'Status': report.get('status', 'N/A'),
                        'Category': report.get('category', [{}])[0].get('text', 'N/A')
                    })
                st.table(reports_data)
            else:
                st.info("No diagnostic reports recorded")

    with tabs[4]:  # New Event form
        st.markdown("### 📝 Register New Clinical Event")
        
        event_type = st.radio(
            "Event Type",
            ["Encounter", "Condition", "Observation", "Diagnostic Report"]
        )
        
        with st.form("new_clinical_event"):
            if event_type == "Encounter":
                encounter_type = st.selectbox(
                    "Encounter Type",
                    options=list(ENCOUNTER_TYPES.keys()),
                    format_func=lambda x: f"{x} - {ENCOUNTER_TYPES[x]}"
                )
                
                description = st.text_area(
                    "Event Description",
                    placeholder="Describe the clinical event..."
                )
                
                reason = st.text_input(
                    "Reason",
                    placeholder="Reason for encounter"
                )
                
                date = st.date_input(
                    "Event Date"
                )
                
            elif event_type == "Condition":
                condition = st.text_input("Condition", placeholder="e.g., Diabetes decompensation")
                status = st.selectbox("Clinical Status", ["active", "recurrence", "resolved"])
                onset_date = st.date_input("Onset Date")
                
            elif event_type == "Observation":
                obs_type = st.text_input("Observation Type", placeholder="e.g., Blood Glucose")
                value = st.number_input("Value")
                unit = st.text_input("Unit", placeholder="e.g., mg/dL")
                obs_date = st.date_input("Observation Date")
                
            elif event_type == "Diagnostic Report":
                report_type = st.text_input("Report Type", placeholder="e.g., Lab Results")
                conclusion = st.text_area("Conclusion")
                report_date = st.date_input("Report Date")
            
            submitted = st.form_submit_button("Register Event")
            
            if submitted:
                success = False
                if event_type == "Encounter":
                    success = create_clinical_event(patient_id, {
                        "encounter_type": encounter_type,
                        "description": description,
                        "reason": reason,
                        "date": date.isoformat()
                    })
                elif event_type == "Condition":
                    success = create_condition(patient_id, {
                        "condition": condition,
                        "status": status,
                        "onset_date": onset_date.isoformat()
                    })
                elif event_type == "Observation":
                    success = create_observation(patient_id, {
                        "type": obs_type,
                        "value": value,
                        "unit": unit,
                        "date": obs_date.isoformat()
                    })
                elif event_type == "Diagnostic Report":
                    success = create_diagnostic_report(patient_id, {
                        "type": report_type,
                        "conclusion": conclusion,
                        "date": report_date.isoformat()
                    })
                
                if success:
                    st.success(f"{event_type} registered successfully")
                    st.experimental_rerun()
                else:
                    st.error(f"Error registering {event_type}")

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

def generate_patient_qr(patient_id):
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
    qr.add_data(patient_id)
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
    # Set page title and icon
    st.set_page_config(page_title="Patient Search", page_icon="🩺")
    
    # Title of the application
    st.title("Patient Search Portal")
    
    # Create tabs for different search methods
    search_method = st.radio(
        "Choose search method:",
        ["Manual ID Entry", "QR Code Scanner", "Generate QR"]
    )
    
    if search_method == "Manual ID Entry":
        # Input for Patient ID
        patient_id = st.text_input("Enter Patient ID", placeholder="Enter a valid Patient ID")
        
        # Search button
        if st.button("Search Patient"):
            if not patient_id:
                st.warning("Please enter a Patient ID")
                return
            
            with st.spinner('Searching for patient...'):
                patient_data = search_patient(patient_id)
                display_patient_info(patient_data)
    
    elif search_method == "QR Code Scanner":
        st.write("Scan QR Code")
        qr_code = qrcode_scanner()
        
        if qr_code:
            with st.spinner('Searching for patient...'):
                patient_data = search_patient(qr_code)
                if patient_data:
                    display_patient_info(patient_data)
                else:
                    st.error("Patient not found")
    
    elif search_method == "Generate QR":
        patient_id = st.text_input("Enter Patient ID for QR Generation", 
                                 placeholder="Enter a valid Patient ID")
        
        if st.button("Generate QR"):
            if not patient_id:
                st.warning("Please enter a Patient ID")
                return
            
            # Generate and display QR code
            qr_image = generate_patient_qr(patient_id)
            st.image(qr_image, caption=f"QR Code for Patient {patient_id}")
            
            # Add download button
            st.download_button(
                label="Download QR Code",
                data=qr_image,
                file_name=f"patient_{patient_id}_qr.png",
                mime="image/png"
            )

# Run the Streamlit app
if __name__ == "__main__":
    main()