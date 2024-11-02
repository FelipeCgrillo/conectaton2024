import streamlit as st
import requests
import folium
from streamlit_folium import folium_static

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

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

def display_patient_info(patient_data):
    if not patient_data:
        st.warning("No patient data found.")
        return
    
    st.success("Patient Found!")
    patient_id = patient_data.get('id')
    
    # Create tabs for different categories of information
    tabs = st.tabs(["Demographics", "Clinical", "Encounters & Procedures", "Reports & Results"])
    
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

def get_location_coordinates(address_str):
    """
    Get coordinates for an address using Nominatim geocoder.
    
    Args:
        address_str (str): Address string to geocode
    
    Returns:
        tuple: (latitude, longitude) or None if geocoding fails
    """
    try:
        geolocator = Nominatim(user_agent="patient_search_portal")
        location = geolocator.geocode(address_str, timeout=10)
        if location:
            return location.latitude, location.longitude
        return None
    except (GeocoderTimedOut, GeocoderUnavailable) as e:
        st.warning(f"Geocoding error: {e}")
        return None

def main():
    """
    Main Streamlit application function
    """
    # Set page title and icon
    st.set_page_config(page_title="Patient Search", page_icon="🩺")
    
    # Title of the application
    st.title("Patient Search Portal")
    
    # Input for Patient ID
    patient_id = st.text_input("Enter Patient ID", placeholder="Enter a valid Patient ID")
    
    # Search button
    if st.button("Search Patient"):
        # Validate input
        if not patient_id:
            st.warning("Please enter a Patient ID")
            return
        
        # Show loading spinner while searching
        with st.spinner('Searching for patient...'):
            # Search for patient
            patient_data = search_patient(patient_id)
            
            # Display patient information
            display_patient_info(patient_data)

# Run the Streamlit app
if __name__ == "__main__":
    main()