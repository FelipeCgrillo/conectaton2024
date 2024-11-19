import streamlit as st
from menu import menu_with_redirect
import pandas as pd
import plotly.express as px
import requests
from fhir.resources.composition import Composition

patient_id = st.session_state.pop('patient_id', None)

# Funktion zum Abrufen der Daten
def fetch_fhir_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Fehler beim Abrufen der Daten: {response.status_code}")
        return None

def search_for_clinical_data(request):
    """
    Search for medication requests associated with a patient.
    
    Args:
        patient_id (str): The patient's ID
    Returns:
        list: List of medication requests or empty list if none found
    """
    try:
        url = f"https://ips-challenge.it.hs-heilbronn.de/fhir/{request}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()

        return []
    except requests.RequestException as e:
        st.error(f"Error fetching medications: {e}")
        return []

# Daten für Zeitstrahl extrahieren für Results Summary
def extract_timeline_data_observation(timeline_data, title, clinical_data):
    # extract date
    date = clinical_data["effectiveDateTime"]

    timeline_data[title].append({
        "Date": date,
        "Laboratory": clinical_data["code"]["coding"][0]["display"],
        "Value": str(clinical_data["valueQuantity"]["value"]) + clinical_data["valueQuantity"]["code"]
    })

# Daten für Zeitstrahl extrahieren für Medication Summary
def extract_timeline_data_encounter(timeline_data, title, clinical_data):
    # extract date
    date = clinical_data["authoredOn"]
    concept = clinical_data["medicationCodeableConcept"]

    timeline_data[title].append({
        "Date": date,
        "Condition": concept["coding"][0]["display"]

    })

# Daten für Zeitstrahl extrahieren für Problems Summary
def extract_timeline_data_condition(timeline_data, title, clinical_data):
    # extract date
    date = clinical_data["onsetDateTime"]
    code = clinical_data["code"]

    timeline_data[title].append({
        "Date": date,
        "Diagnosis": code["coding"][0]["display"]
    })

# Streamlit App
#st.title("FHIR IPS Composition Zeitstrahl")

# Daten abrufen
composition_data = fetch_fhir_data(f"https://ips-challenge.it.hs-heilbronn.de/fhir/Composition?patient={patient_id}")
resource = composition_data["entry"][0]["resource"]
st.title(resource["title"])

timeline_data = {
        "Medication Summary": [],
        "Problems Summary": [],
        "Results Summary": []
    }

for section in resource["section"]:
    if section["title"] == "Medication Summary" or section["title"] == "Problems Summary" or section["title"] == "Results Summary":
        for entry in section["entry"]:
            clinical_data = search_for_clinical_data(entry["reference"]) # clinical data ist nun ein json aus EINER observation
            if section["title"] == "Medication Summary":
                extract_timeline_data_encounter(timeline_data, section["title"], clinical_data) # füge diese observation in die timeline ein
            if section["title"] == "Problems Summary":
                extract_timeline_data_condition(timeline_data, section["title"], clinical_data)
            if section["title"] == "Results Summary":
                extract_timeline_data_observation(timeline_data, section["title"], clinical_data)


#st.write(composition_data)
# ressource['title']
# UC4-Patient


# Zeitstrahl für jede Kategorie
for category in ["Medication Summary", "Problems Summary", "Results Summary"]:
    st.header(category)
    
    # Daten in DataFrame formatieren
    data = pd.DataFrame(timeline_data[category])
    if not data.empty:
        st.write(data)
        
        # Zeitstrahl plotten
        st.line_chart(data.set_index("Date"))
    else:
        st.write("Keine Daten verfügbar.")