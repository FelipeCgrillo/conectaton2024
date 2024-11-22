import streamlit as st
from menu import menu_with_redirect
from fhir_web import search_patient_resource

menu_with_redirect()



# Conditions Section
with st.expander("🏥 Conditions", expanded=True):
    conditions = search_patient_resource(st.session_state.fhir_server_url, st.session_state.patient_id, "Condition")
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
    medications = search_patient_resource(st.session_state.fhir_server_url, st.session_state.patient_id, "MedicationRequest")
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
    allergies = search_patient_resource(st.session_state.fhir_server_url, st.session_state.patient_id, "AllergyIntolerance")
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
    immunizations = search_patient_resource(st.session_state.fhir_server_url, st.session_state.patient_id, "Immunization")
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