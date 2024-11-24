import streamlit as st
import requests

patient_id = st.session_state.get("patient_id", None)

def search_for_clinical_data(request):
    try:
        url = f"https://ips-challenge.it.hs-heilbronn.de/fhir/{request}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()

        return []
    except requests.RequestException as e:
        st.error(f"Error fetching medications: {e}")
        return []

# Funktion zum Abrufen der Daten
def fetch_fhir_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Fehler beim Abrufen der Daten: {response.status_code}")
        return None

# Daten für Zeitstrahl extrahieren für Results Summary
def extract_timeline_data_observation(timeline_data, title, clinical_data):
    # extract date
    date = clinical_data["effectiveDateTime"]
    observation_name = clinical_data["code"]["coding"][0]["display"]
    symbol = ""

    # Überprüfen, ob der Name "Glucose" oder "Hemoglobin" ist
    if "Glucose" in observation_name:
        symbol = "Glucose Level"  # Glucose
    elif "Hemoglobin" in observation_name:
        symbol = "Hemoglobin in Blood"  # Hämoglobin

    timeline_data.append({
        "Title": "Observation" + " - " + symbol,
        "Name": observation_name,
        "Date": date,
        "Value": str(clinical_data["valueQuantity"]["value"]) + clinical_data["valueQuantity"]["code"]
    })

# Daten für Zeitstrahl extrahieren für Medication Summary
def extract_timeline_data_encounter(timeline_data, title, clinical_data):
    # extract date
    date = clinical_data["authoredOn"]
    concept = clinical_data["medicationCodeableConcept"]
    encounter_name = concept["coding"][0]["display"]

    timeline_data.append({
        "Title": "Medication Request",
        "Name": encounter_name,
        "Date": date

    })

# Daten für Zeitstrahl extrahieren für Problems Summary
def extract_timeline_data_condition(timeline_data, title, clinical_data):
    # extract date
    date = clinical_data["onsetDateTime"]
    code = clinical_data["code"]
    condition_name= code["coding"][0]["display"]

    timeline_data.append({
        "Title": "Condition",
        "Name": condition_name,
        "Date": date
    })