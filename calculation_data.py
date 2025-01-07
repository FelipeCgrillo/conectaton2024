import streamlit as st
import requests

def search_for_clinical_data(request):
    """
    This method gets the json of the clinical data
        :param request: reference to e.g. observation
        :return: clinical data as json
    """
    try:
        url = f"https://ips-challenge.it.hs-heilbronn.de/fhir/{request}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return []
    except requests.RequestException as e:
        st.error(f"Error fetching data: {e}")
        return []

def fetch_fhir_data(url):
    """
    Get the data from a specific URL
    :param url: url of fhir data
    :return: json
    """
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        st.error(f"Error while reading the data: {response.status_code}")
    except requests.RequestException as e:
        st.error(f"Error fetching data: {e}")
    return None

def extract_timeline_data_observation(timeline_data, clinical_data):
    """
    Extract the information of an observation from the clinical data
    :param timeline_data: json to save the specific data and later print the timelines
    :param clinical_data: extended data of the patient
    """
    date = clinical_data.get("effectiveDateTime", "N/A")
    code = clinical_data.get("code", {}).get("coding", [{}])[0]
    observation_name = code.get("display", "Unknown Observation")
    loinc = code.get("code", "N/A")

    symbol = ""
    if loinc == "14749-6":
        symbol = " - Glucose Level"
    elif loinc == "4548-4":
        symbol = " - Ac1-Test"

    value = clinical_data.get("valueQuantity", {}).get("value", "N/A")
    unit = clinical_data.get("valueQuantity", {}).get("code", "")
    value = f"{value} {unit}" if value != "N/A" else "No value"

    timeline_data.append({
        "Title": f"Results{symbol}",
        "Name": observation_name,
        "Date": date,
        "Value": value
    })

def extract_timeline_data_encounter(timeline_data, clinical_data):
    """
    Extract the information of an encounter from the clinical data
    :param timeline_data: json to save the specific data and later print the timelines
    :param clinical_data: extended data of the patient
    """
    date = "N/A"
    title = "Unknown"

    if clinical_data.get("resourceType") == "MedicationRequest":
        date = clinical_data.get("authoredOn", "N/A")
        title = "Medication Requests"
    elif clinical_data.get("resourceType") == "MedicationStatement":
        date = clinical_data.get("effectiveDateTime", "N/A")
        title = "Medication Statements"
    elif clinical_data.get("resourceType") == "MedicationAdministration":
        date = clinical_data.get("effectiveDateTime", "N/A")
        title = "Medication Administrations"

    concept = clinical_data.get("medicationCodeableConcept", {}).get("coding", [{}])[0]
    encounter_name = concept.get("display", "Unknown Medication")

    timeline_data.append({
        "Title": title,
        "Name": encounter_name,
        "Date": date
    })

    if clinical_data.get("resourceType") == "MedicationDispense":
        date = clinical_data.get("whenPrepared", "N/A")
        encounter_name = clinical_data.get("medicationCodeableConcept", {}).get("coding", [{}])[0].get("display", "Unknown Medication")

        timeline_data.append({
            "Title": "Medication Dispenses",
            "Name": encounter_name,
            "Date": date
        })

def extract_timeline_data_condition(timeline_data, clinical_data):
    """
    Extract the information of a condition from the clinical data
    :param timeline_data: json to save the specific data and later print the timelines
    :param clinical_data: extended data of the patient
    """
    date = clinical_data.get("onsetDateTime", "N/A")
    code = clinical_data.get("code", {}).get("coding", [{}])[0]
    condition_name = code.get("display", "Unknown Condition")

    timeline_data.append({
        "Title": "Problems",
        "Name": condition_name,
        "Date": date
    })

def extract_timeline_data_intolerance(timeline_data, clinical_data):
    """
    Extract the information of an intolerance from the clinical data
    :param timeline_data: json to save the specific data and later print the timelines
    :param clinical_data: extended data of the patient
    """
    date = clinical_data.get("onsetDateTime", "N/A")
    code = clinical_data.get("code", {}).get("coding", [{}])[0]
    intolerance_name = code.get("display", "Unknown Allergy")

    reaction = clinical_data.get("reaction", [{}])[0].get("manifestation", [{}])[0].get("coding", [{}])[0].get("display", "No reaction")
    criticality = clinical_data.get("criticality", "Unknown")

    timeline_data.append({
        "Title": "Allergy Intolerance",
        "Name": intolerance_name,
        "Date": date,
        "Reaction": reaction,
        "Criticality": criticality
    })

def extract_timeline_data_vital(timeline_data, clinical_data):
    """
    Extract the information of vital data from the clinical data
    :param timeline_data: json to save the specific data and later print the timelines
    :param clinical_data: extended data of the patient
    """
    date = clinical_data.get("effectiveDateTime", "N/A")
    code = clinical_data.get("code", {}).get("coding", [{}])[0]
    vital_name = code.get("display", "Unknown Vital Sign")

    value = clinical_data.get("valueQuantity", {}).get("value", "N/A")
    unit = clinical_data.get("valueQuantity", {}).get("code", "")
    value = f"{value} {unit}" if value != "N/A" else "No Value"

    if value == "No Value":
        components = clinical_data.get("component", [])
        if components:
            vital_data = {"Title": "Vital Signs", "Date": date}
            for idx, component in enumerate(components, start=1):
                component_code = component.get("code", {}).get("coding", [{}])[0]
                vital_data[f"Name {idx}"] = component_code.get("display", "Unknown Component")
                vital_data[f"Value {idx}"] = f"{component.get('valueQuantity', {}).get('value', 'N/A')} {component.get('valueQuantity', {}).get('code', '')}"
            timeline_data.append(vital_data)
        else:
            timeline_data.append({
                "Title": "Vital Signs",
                "Name": vital_name,
                "Date": date,
                "Value": "No Value"
            })
    else:
        timeline_data.append({
            "Title": "Vital Signs",
            "Name": vital_name,
            "Date": date,
            "Value": value
        })

def extract_timeline_data_history(timeline_data, clinical_data):
    """
    Extract the information of the social history from the clinical data
    :param timeline_data: json to save the specific data and later print the timelines
    :param clinical_data: extended data of the patient
    """
    date = clinical_data.get("effectiveDateTime", "N/A")
    history_name = "Observation - Other"

    value = clinical_data.get("valueCodeableConcept", {}).get("coding", [{}])[0].get("display", "No value")
    note = clinical_data.get("note", [{}])[0].get("text", "No Note")
    method = clinical_data.get("method", {}).get("coding", [{}])[0].get("display", "No Method")

    timeline_data.append({
        "Title": "Social History",
        "Name": history_name,
        "Date": date,
        "Value": value,
        "Note": note,
        "Method": method
    })
