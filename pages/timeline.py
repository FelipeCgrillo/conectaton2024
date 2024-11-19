import streamlit as st
from menu import menu_with_redirect
import pandas as pd
import plotly.express as px
import requests
from fhir.resources.composition import Composition

patient_id = st.session_state.get('patient_id', None)

def print_timeline(data):
    menu_with_redirect()

    # Verify the user's role
    if not st.session_state.found_patient:
        st.warning("No patient found.")
        st.stop()

    st.title("Clinical Timeline")

    # Convert data into a DataFrame
    df = pd.DataFrame(data)
    df['Date'] = pd.to_datetime(df['Date'])

    # Initialize session state for selected data if it doesn't exist
    if "selected_data_index" not in st.session_state:
        st.session_state.selected_data_index = None

    # Sidebar-Filter hinzufügen (Zeitraum)
    st.sidebar.header("Filter Options")

    # Zeitraum-Filter (Start- und Enddatum)
    start_date = st.sidebar.date_input("Start Date", value=df['Date'].min().date())
    end_date = st.sidebar.date_input("End Date", value=df['Date'].max().date())

    # Validierung des Zeitraums
    if start_date > end_date:
        st.sidebar.error("Start Date must be earlier than End Date.")
        st.stop()

    # Ressourcenfilter (z. B. nach Condition, MedicationRequest, etc.)
    resource_types = df['Title'].unique()
    selected_resources = st.sidebar.multiselect(
        "Filter by Resource Type", options=resource_types, default=resource_types
    )

    # Nach Zeitraum und Ressourcentyp filtern
    filtered_df = df[
        (df['Date'] >= pd.Timestamp(start_date)) &
        (df['Date'] <= pd.Timestamp(end_date)) &
        (df['Title'].isin(selected_resources))
    ]

    # Plotly Timeline Diagramm erstellen
    if not filtered_df.empty:
        fig = px.scatter(
            filtered_df,
            x="Date",
            y="Title",
            text="Name",
            labels={"Date": "Date", "Title": "Resource Type"},
            hover_data=["Details"]
        )
        fig.update_traces(marker=dict(size=12, opacity=0.7), mode="markers+text", textposition="top center")
        fig.update_layout(clickmode="event+select")

        # Zeitstrahl in Streamlit anzeigen
        st.plotly_chart(fig)
    else:
        st.warning("No data available for the selected filters.")

    # Glucose values chart
    glucose_df = df[df['Title'] == "Observation"]
    glucose_df = glucose_df[glucose_df['Name'].str.contains("Glucose", case=False)]

    if not glucose_df.empty:
        glucose_df['Value'] = glucose_df['Value'].str.extract('(\d+\.?\d*)').astype(float)  # Extract numeric values
        glucose_df['Status'] = glucose_df['Value'].apply(
            lambda x: 'Normal' if 70 <= x <= 140 else 'Abnormal'
        )

        fig_glucose = px.line(
            glucose_df,
            x="Date",
            y="Value",
            color="Status",
            color_discrete_map={"Normal": "green", "Abnormal": "red"},
            markers=True,
            labels={"Value": "Glucose Level", "Date": "Date"},
            title="Glucose Levels Over Time"
        )
        fig_glucose.update_layout(showlegend=True)
        st.plotly_chart(fig_glucose)
    else:
        st.info("No Glucose data available.")

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

    timeline_data.append({
        "Title": "Observation",
        "Name": clinical_data["code"]["coding"][0]["display"],
        "Date": date,
        "Details": clinical_data["code"]["coding"][0]["display"],
        "Value": str(clinical_data["valueQuantity"]["value"]) + clinical_data["valueQuantity"]["code"]
    })

# Daten für Zeitstrahl extrahieren für Medication Summary
def extract_timeline_data_encounter(timeline_data, title, clinical_data):
    # extract date
    date = clinical_data["authoredOn"]
    concept = clinical_data["medicationCodeableConcept"]

    timeline_data.append({
        "Title": "Medication Request",
        "Name": concept["coding"][0]["display"],
        "Date": date,
        "Details": concept["coding"][0]["display"]

    })

# Daten für Zeitstrahl extrahieren für Problems Summary
def extract_timeline_data_condition(timeline_data, title, clinical_data):
    # extract date
    date = clinical_data["onsetDateTime"]
    code = clinical_data["code"]

    timeline_data.append({
        "Title": "Condition",
        "Name": code["coding"][0]["display"],
        "Date": date,
        "Details": code["coding"][0]["display"]
    })

# Streamlit App
#st.title("FHIR IPS Composition Zeitstrahl")

# Daten abrufen
composition_data = fetch_fhir_data(f"https://ips-challenge.it.hs-heilbronn.de/fhir/Composition?patient={patient_id}")
if not composition_data or "entry" not in composition_data:
    st.error("No data found for the patient. Please check the patient ID or data source.")
    st.stop()

resource = composition_data["entry"][0]["resource"]
st.title(resource["title"])

timeline_data = []

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

print_timeline(timeline_data)

# Zeitstrahl für jede Kategorie
#for category in ["Medication Summary", "Problems Summary", "Results Summary"]:
#    st.header(category)
    
    # Daten in DataFrame formatieren
#    data = pd.DataFrame(timeline_data[category])
#    if not data.empty:
#        st.write(data)
        
        # Zeitstrahl plotten
#        st.line_chart(data.set_index("Date"))
#    else:
#        st.write("Keine Daten verfügbar.")
