import streamlit as st
import requests

st.markdown("### 📝 Register New Clinical Event")

def validate(fhir_server_url, resource_type, payload):
    """
    Uses the POST resource_type/$validate request to validate before posting new events to FHIR server.

    Args:
        fhir_server_url (str): FHIR Server URL
        resource_type (str): FHIR Resource Type
        payload (json): Resource payload to be validated
    """
    url = fhir_server_url + resource_type + "/$validate"
    response = requests.post(
        url,
        json=payload,
        headers={"accept": "application/fhir+json", "Content-Type": "application/fhir+json"}
    )
    print(payload)
    #st.write(response.json())
    val_res = response.json()
    problematic_severities = set(["error","fatal"])
    actual_severities = set([entry['severity']for entry in val_res['issue']])
    feedback = []
    if problematic_severities & actual_severities:
        st.error("Validation error")
        for issue in val_res.get('issue', []):
            severity = issue.get('severity', 'unknown')
            if severity in problematic_severities:
                diagnostics = issue.get('diagnostics', 'No diagnostic information')
                location = issue.get('location', 'No location information')

                feedback.append({
                    "severity": severity,
                    "diagnostics": diagnostics,
                    "location": location
                })
        st.write(feedback)
        return False
    return True

def add_to_composition(fhir_server_url, patient_id, res, resource_name, section_title):
    resource_id = res.json()["id"]
    url = f"{fhir_server_url}Composition?patient={patient_id}"
    print(f"add_to_composition url: {url}")
    # Get Composition
    response = requests.get(url)
    if response.status_code == 200:
        composition_bundle = response.json()
        
        # Extract composition resource
        composition_data = composition_bundle["entry"][0]["resource"]
        
        # New reference
        new_reference = {"reference": f"{resource_name}/{resource_id}"}
        
        # Add new reference in the appropriate section
        for section in composition_data.get("section", []):
            if section.get("title") == section_title:
                if "entry" not in section:  # if "entry" does not exist
                    section["entry"] = []  # initialize as empty list
                if new_reference not in section["entry"]:
                    section["entry"].append(new_reference)  # Add reference
                else:
                    print("The reference already exists.")
                    break

        # URL für die Aktualisierung der Composition
        update_url = f"{fhir_server_url}Composition/{composition_data['id']}"
        headers = {"Content-Type": "application/json"}
        
        # PUT-Request für die aktualisierte Composition
        update_response = requests.put(update_url, headers=headers, json=composition_data)


        if update_response.status_code == 200:
            print("Composition updated successfully.")
            return True
        else:
            print(f"Error updating composition: {update_response.status_code}, {update_response.text}")
            return False
    else:
        print(f"Error fetching composition: {response.status_code}")
        return False

def create_encounter(fhir_server_url, patient_id, event_data):
    """
    Creates a new clinical event for a patient.
    
    Args:
        patient_id (str): Patient ID
        event_data (dict): Clinical event data
    Returns:
        bool: True if created successfully, False otherwise
    """
    try:
        url = fhir_server_url + "Encounter"
        
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
        if not validate(fhir_server_url, "Encounter", encounter_resource):
            return False
        # Make POST request
        response = requests.post(
            url,
            json=encounter_resource,
            headers={"Content-Type": "application/fhir+json"}
        )
        
        return response.status_code == 201
    except requests.RequestException as e:
        st.error(f"Error creating clinical event: {str(e)}")
        return False

def create_condition(fhir_server_url, patient_id, condition_data):
    """
    Creates a new condition for a patient.
    """
    try:
        url = fhir_server_url + "Condition"
        
        condition_resource = {
            "resourceType": "Condition",
            "clinicalStatus": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": condition_data['status'],
                    "display": condition_data['status']
                }]
            },
            "code": {
                "coding":[
                    {
                        "system": "http://snomed.info/sct",
                        "code": condition_data["snomed_code"],
                        "display": condition_data["snomed_display"]
                    }
                ],
                "text": condition_data['condition']
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "onsetDateTime": condition_data['onset_date']
        }
        if not validate(fhir_server_url, "Condition", condition_resource):
            return False
        response = requests.post(
            url,
            json=condition_resource,
            headers={"Content-Type": "application/fhir+json"}
        )

        if response.status_code != 201:
            return False
        print(f"created condition with id: {response.json()['id']}")
        composition_success = add_to_composition(fhir_server_url, patient_id, response, "Condition", "Problems Summary")
        if not composition_success:
            return False
        return True
    except requests.RequestException as e:
        st.error(f"Error creating condition: {str(e)}")
        return False

def create_observation(fhir_server_url, patient_id, observation_data):
    """
    Creates a new observation for a patient.
    """
    try:
        url = fhir_server_url + "Observation"
        
        observation_resource = {
            "resourceType": "Observation",
            "status": "final",
            "category": [ {
                "coding": [ {
                "code": "laboratory"
                } ]
            } ],
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "code": {
                "coding":[
                    {
                        "system": "http://loinc.org",
                        "code": observation_data["loinc_code"],
                        "display": observation_data["loinc_display"]
                    }
                ],
                "text": observation_data['type']
            },
            "valueQuantity": {
                "value": observation_data['value'],
                "system": "http://unitsofmeasure.org",
                "code": observation_data['unit']
            },
            "effectiveDateTime": observation_data['date']
        }
        if not validate(fhir_server_url, "Observation", observation_resource):
            return False

        print(observation_resource)
        response = requests.post(
            url,
            json=observation_resource,
            headers={"Content-Type": "application/fhir+json"}
        )
        if response.status_code != 201:
            return False
        print(f"created observation with id: {response.json()['id']}")
        composition_success = add_to_composition(fhir_server_url, patient_id, response, "Observation", "Results Summary")
        if not composition_success:
            return False
        return True
    except requests.RequestException as e:
        st.error(f"Error creating observation: {str(e)}")
        return False

def create_diagnostic_report(fhir_server_url, patient_id, report_data):
    """
    Creates a new diagnostic report for a patient.
    """
    try:
        url = fhir_server_url + "DiagnosticReport"
        
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
        if not validate(fhir_server_url, "DiagnosticReport", report_resource):
            return False
        response = requests.post(
            url,
            json=report_resource,
            headers={"Content-Type": "application/fhir+json"}
        )
        return response.status_code == 201
    except requests.RequestException as e:
        st.error(f"Error creating diagnostic report: {str(e)}")
        return False

def create_medication_request(fhir_server_url, patient_id, medication_request_data):
    """
    Creates a new medication request for a patient.
    """
    try:
        url = fhir_server_url + "MedicationRequest"

        medication_request_resource = {
            "resourceType": "MedicationRequest",
            "status": medication_request_data["status"],
            "intent": "order",
            "medicationCodeableConcept": {
                "coding": [{
                    "system": "http://snomed.info/sct",
                    "code": medication_request_data["snomed_code"],
                    "display": medication_request_data["snomed_display"]
                }]
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "authoredOn": medication_request_data["date"]
        }
        if not validate(fhir_server_url, "MedicationRequest", medication_request_resource):
            return False

        print(medication_request_resource)
        response = requests.post(
            url,
            json=medication_request_resource,
            headers={"Content-Type": "application/fhir+json"}
        )
        if response.status_code != 201:
            return False
        print(f"created medication request with id: {response.json()['id']}")
        composition_success = add_to_composition(fhir_server_url, patient_id, response, "MedicationRequest", "Medication Summary")
        if not composition_success:
            return False
        return True
    except requests.RequestException as e:
        st.error(f"Error creating medication request: {str(e)}")
        return False

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

MEDICATION_REQUEST_STATI = ["active", "on-hold", "cancelled", "completed", "entered-in-error", "stopped", "draft", "unknown"]

# Códigos LOINC comunes relacionados con glucosa
GLUCOSE_LOINC_CODES = {
    "14749-6": "Glucosa en Suero o Plasma",
    "2339-0": "Glucosa en Sangre",
    "2345-7": "Glucosa en Orina",
    "41653-7": "Glucosa en Sangre Estimada por Glucómetro",
    "71596-5": "Glucosa en Sangre Total por Glucómetro",
    "2344-0": "Glucosa 2 horas post 75g de glucosa oral",
    "1558-6": "Glucosa en Sangre Capilar",
    "14771-0": "Glucosa en Líquido Cefalorraquídeo",
    "77145-5": "Glucosa en Sangre por Monitor Continuo",
    "56109-4": "Hemoglobina A1c en Sangre por HPLC"
}

# Códigos SNOMED comunes relacionados con diabetes y glucosa
DIABETES_SNOMED_CODES = {
    "73211009": "Diabetes mellitus",
    "44054006": "Diabetes mellitus tipo 2",
    "46635009": "Diabetes mellitus tipo 1",
    "4855003": "Retinopatía diabética",
    "422088007": "Hipoglucemia",
    "80394007": "Hiperglucemia",
    "33747003": "Glucosa en sangre anormal",
    "271737000": "Anormalidad de prueba de tolerancia a la glucosa",
    "190447002": "Diabetes con complicaciones renales",
    "190416008": "Diabetes con complicaciones neurológicas"
}

event_type = st.radio(
    "Event Type",
    #["Encounter", "Condition", "Observation", "Diagnostic Report"]
    ["Condition","Laboratory result","Medication Request"]
)

with st.form("new_clinical_event"):
    if event_type == "Encounter":
        encounter_type = st.selectbox("Encounter Type",options=list(ENCOUNTER_TYPES.keys()),format_func=lambda x: f"{x} - {ENCOUNTER_TYPES[x]}")
        description = st.text_area("Event Description",placeholder="Describe the clinical event...")
        reason = st.text_input("Reason",placeholder="Reason for encounter")
        date = st.date_input("Event Date")
        
    elif event_type == "Condition":
        condition = st.text_input("Condition", placeholder="e.g., Diabetes decompensation", value="Diabetic retinopathy")
        status = st.selectbox("Clinical Status", ["active", "recurrence", "resolved"])
        onset_date = st.date_input("Onset Date")
        
        # Agregar selector de códigos SNOMED comunes para diabetes
        st.write("Códigos SNOMED comunes para diabetes y glucosa:")
        selected_snomed = st.selectbox(
            "Seleccione un código SNOMED predefinido",
            options=list(DIABETES_SNOMED_CODES.keys()),
            format_func=lambda x: f"{x} - {DIABETES_SNOMED_CODES[x]}"
        )
        
        st.write("O busque un código SNOMED personalizado:")
        st.page_link("https://browser.ihtsdotools.org/?", label="SNOMED")
        snomed_code = st.text_input("SNOMED code (SCTID)", value=selected_snomed)
        snomed_display = st.text_input("SNOMED condition display text", value=DIABETES_SNOMED_CODES.get(selected_snomed, ""))
        
    elif event_type == "Laboratory result":
        obs_type = st.text_input("Observation Type", placeholder="e.g., Blood Glucose")
        value = st.number_input("Value")
        unit = st.text_input("Unit", placeholder="e.g., mg/dL")
        
        # Agregar selector de códigos LOINC comunes para glucosa
        st.write("Códigos LOINC comunes para glucosa:")
        selected_loinc = st.selectbox(
            "Seleccione un código LOINC predefinido",
            options=list(GLUCOSE_LOINC_CODES.keys()),
            format_func=lambda x: f"{x} - {GLUCOSE_LOINC_CODES[x]}"
        )
        
        st.write("O busque un código LOINC personalizado:")
        st.page_link("http://search.loinc.org", label="LOINC")
        loinc_code = st.text_input("LOINC code", value=selected_loinc)
        loinc_display = st.text_input("LOINC display text", value=GLUCOSE_LOINC_CODES.get(selected_loinc, ""))
        obs_date = st.date_input("Observation Date")
        
    elif event_type == "Diagnostic Report":
        report_type = st.text_input("Report Type", placeholder="e.g., Lab Results")
        conclusion = st.text_area("Conclusion")
        report_date = st.date_input("Report Date")
    
    elif event_type == "Medication Request":
        medication_request_status = st.selectbox("Medication Request Status", options=MEDICATION_REQUEST_STATI)
        st.write("Look up the SNOMED code")
        st.page_link("https://browser.ihtsdotools.org/?", label="SNOMED")
        snomed_code = st.text_input("SNOMED code (SCTID)", value="1197765009")
        snomed_display = st.text_input("SNOMED drug display text", value="Glucagon 5 mg/mL solution for injection")
        medication_request_date = st.date_input("Medication Request Date")

    
    submitted = st.form_submit_button("Register Event")
    
    if submitted:
        success = False
        if event_type == "Encounter":
            success = create_encounter(st.session_state.fhir_server_url, st.session_state.patient_id, {
                "encounter_type": encounter_type,
                "description": description,
                "reason": reason,
                "date": date.isoformat()
            })
        elif event_type == "Condition":
            success = create_condition(st.session_state.fhir_server_url, st.session_state.patient_id, {
                "condition": condition,
                "status": status,
                "onset_date": onset_date.isoformat(),
                "snomed_code": snomed_code,
                "snomed_display": snomed_display
            })
        elif event_type == "Laboratory result":
            success = create_observation(st.session_state.fhir_server_url, st.session_state.patient_id, {
                "type": obs_type,
                "value": value,
                "unit": unit,
                "loinc_code": loinc_code,
                "loinc_display": loinc_display,
                "date": obs_date.isoformat()
            })
        elif event_type == "Diagnostic Report":
            success = create_diagnostic_report(st.session_state.fhir_server_url, st.session_state.patient_id, {
                "type": report_type,
                "conclusion": conclusion,
                "date": report_date.isoformat()
            })
        elif event_type == "Medication Request":
            success = create_medication_request(st.session_state.fhir_server_url, st.session_state.patient_id, {
                "status": medication_request_status,
                "snomed_code": snomed_code,
                "snomed_display": snomed_display,
                "date": medication_request_date.isoformat()
            })
        
        if success:
            st.success(f"{event_type} registered successfully")
        else:
            st.error(f"Error registering {event_type}")