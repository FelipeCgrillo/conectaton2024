import streamlit as st
from menu import menu_with_redirect
import pandas as pd
import plotly.express as px

import requests

# Try print IPS
def get_ips_for_patient(patient_id):
    """
    Retrieve the IPS (International Patient Summary) for a given patient ID.
    
    Args:
        patient_id (str): The unique identifier of the patient
    
    Returns:
        dict or None: IPS data as JSON if available, None otherwise
    """

    try:
        # URL für die IPS-Abfrage (Composition-Ressource)
        url = f"https://ips-challenge.it.hs-heilbronn.de/fhir/Composition?patient={patient_id}"
        
        # GET-Anfrage senden
        response = requests.get(url)

        # Prüfen, ob die Antwort erfolgreich war
        if response.status_code == 200:
            data = response.json()
            # Rückgabe der Composition-Daten
            return data
        else:
            print(f"No IPS found. Status: {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"Ein Fehler ist aufgetreten: {e}")
        return None

if 'patient_id' in st.session_state:
    patient_id = st.session_state['patient_id']
    ips = get_ips_for_patient(patient_id)
else:
    print(f"No Patient-ID found.")

menu_with_redirect()

# Verify the user's role
if not st.session_state.found_patient:
    st.warning("No patient found.")
    st.stop()

st.title("Clinical timeline")

# Sample FHIR resource data
data = [
    {"resource_type": "Condition", "date": "2023-01-10", "details": "Hypertension"},
    {"resource_type": "Immunization", "date": "2023-03-05", "details": "COVID-19 Vaccine"},
    {"resource_type": "MedicationRequest", "date": "2023-06-15", "details": "Atorvastatin 20mg"},
    {"resource_type": "Condition", "date": "2023-09-10", "details": "Diabetes Type 2"},
    {"resource_type": "MedicationRequest", "date": "2023-10-12", "details": "Metformin 500mg"},
]

# Convert data into a DataFrame
df = pd.DataFrame(data)
df['date'] = pd.to_datetime(df['date'])

# Initialize session state for selected data if it doesn't exist
if "selected_data_index" not in st.session_state:
    st.session_state.selected_data_index = None

# Sidebar-Filter hinzufügen (Zeitraum)
st.sidebar.header("Filter Options")

# Zeitraum-Filter (Start- und Enddatum)
start_date = st.sidebar.date_input("Start Date", value=df['date'].min().date())
end_date = st.sidebar.date_input("End Date", value=df['date'].max().date())

# Validierung des Zeitraums
if start_date > end_date:
    st.sidebar.error("Start Date must be earlier than End Date.")
    st.stop()

# Ressourcenfilter (z. B. nach Condition, MedicationRequest, etc.)
resource_types = df['resource_type'].unique()
selected_resources = st.sidebar.multiselect(
    "Filter by Resource Type", options=resource_types, default=resource_types
)

# Nach Zeitraum und Ressourcentyp filtern
filtered_df = df[
    (df['date'] >= pd.Timestamp(start_date)) &
    (df['date'] <= pd.Timestamp(end_date)) &
    (df['resource_type'].isin(selected_resources))
]

# Plotly Timeline Diagramm erstellen
if not filtered_df.empty:
    fig = px.scatter(
        filtered_df,
        x="date",
        y="resource_type",
        text="resource_type",
        title="FHIR Resource Timeline",
        labels={"date": "Date", "resource_type": "Resource Type"},
        hover_data=["details"]
    )
    fig.update_traces(marker=dict(size=12, opacity=0.7), mode="markers+text", textposition="top center")
    fig.update_layout(clickmode="event+select")

    # Zeitstrahl in Streamlit anzeigen
    st.plotly_chart(fig)
else:
    st.warning("No data available for the selected filters.")