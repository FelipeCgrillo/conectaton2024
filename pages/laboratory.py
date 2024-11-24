import streamlit as st
from menu import menu_with_redirect
import pandas as pd
import plotly.express as px
import requests
from fhir.resources.composition import Composition

patient_id = st.session_state.get('patient_id', None)
timeline_data = st.session_state.get('laboratory_data', None)
menu_with_redirect()

st.title("Laboratory Results")

def print_diagrams(data):

    # Convert data into a DataFrame
    df = pd.DataFrame(data)
    df['Date'] = pd.to_datetime(df['Date'])

    # Add color
    df['Color'] = "Neutral"
    # Add symbol
    df['Symbol'] = "circle"

    # Glucose values chart
    glucose_df = df[df['Title'] == "Observation - Glucose Level"]
    glucose_df = glucose_df[glucose_df['Name'].str.contains("Glucose", case=False)]
    glucose_df['Exact Date'] = df['Date'].dt.strftime('%B %d, %Y')

    if not glucose_df.empty:
        glucose_df['Value'] = glucose_df['Value'].str.extract('(\d+\.?\d*)').astype(float)  # Extract numeric values
        glucose_df['Status'] = glucose_df['Value'].apply(
            lambda x: 'Normal (< 140 mg/dL)' if x < 140 else ('Marginal (140-199 mg/dL)' if 140 <= x <= 199 else 'Abnormal (>= 200 mg/dL)')
        )

        fig_glucose = px.line(
            glucose_df,
            x="Date",
            y="Value",
            color="Status",
            color_discrete_map={"Normal (< 140 mg/dL)": "green","Marginal (140-199 mg/dL)": "orange", "Abnormal (>= 200 mg/dL)": "red"},
            markers=True,
            labels={"Value": "Glucose Level", "Date": "Date"},
            title="Glucose Levels Over Time",
            hover_data=["Exact Date"]
        )
        # Punkte dicker machen
        fig_glucose.update_traces(marker=dict(size=10))  # Punktgröße erhöhen

        # Verbindungslinien entfernen
        fig_glucose.update_traces(mode='markers')

        # Berechne den minimalen und maximalen Wert der Zeitachse
        min_date = glucose_df['Date'].min()
        max_date = glucose_df['Date'].max()

        # Füge Puffer für die X-Achse hinzu (5% der Zeitspanne vor und nach dem tatsächlichen Zeitraum)
        buffer_days = (max_date - min_date) * 0.05  # 5% Puffer
        min_date_with_buffer = min_date - buffer_days
        max_date_with_buffer = max_date + buffer_days

        fig_glucose.update_layout(
            shapes=[
                # Normalbereich (< 140 mg/dL) in hellgrün
                dict(
                    type="rect",
                    x0=min_date_with_buffer, x1=max_date_with_buffer,
                    y0=0, y1=140,
                    fillcolor="lightgreen",
                    opacity=0.2,
                    line_width=0
                ),
                # Marginalbereich (140-199 mg/dL) in hellorange
                dict(
                    type="rect",
                    x0=min_date_with_buffer, x1=max_date_with_buffer,
                    y0=140, y1=200,
                    fillcolor="lightgoldenrodyellow",
                    opacity=0.2,
                    line_width=0
                ),
                # Abnormalbereich (>= 200 mg/dL) in hellrot
                dict(
                    type="rect",
                    x0=min_date_with_buffer, x1=max_date_with_buffer,
                    y0=200, y1=glucose_df['Value'].max(),  # Y-Wert bis zum maximalen Glukosewert
                    fillcolor="lightcoral",
                    opacity=0.2,
                    line_width=0
                )
            ],
            #xaxis=dict(range=[glucose_df['Date'].min(), glucose_df['Date'].max()])
        )

        # Diagramm anpassen und anzeigen
        fig_glucose.update_layout(showlegend=True)
        st.plotly_chart(fig_glucose)
    else:
        st.info("No Glucose data available.")

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

# Daten abrufen
#composition_data = fetch_fhir_data(f"https://ips-challenge.it.hs-heilbronn.de/fhir/Composition?patient={patient_id}")
#if not composition_data or "entry" not in composition_data:
#    st.error("No data found for the patient. Please check the patient ID or data source.")
#    st.stop()

#resource = composition_data["entry"][0]["resource"]
#st.title(resource["title"])

#timeline_data = []

#for section in resource["section"]:
#    if section["title"] == "Medication Summary" or section["title"] == "Problems Summary" or section["title"] == "Results Summary":
#        for entry in section["entry"]:
#            clinical_data = search_for_clinical_data(entry["reference"]) # clinical data ist nun ein json aus EINER observation
#            if section["title"] == "Medication Summary":
#                extract_timeline_data_encounter(timeline_data, section["title"], clinical_data) # füge diese observation in die timeline ein
#            if section["title"] == "Problems Summary":
#                extract_timeline_data_condition(timeline_data, section["title"], clinical_data)
#            if section["title"] == "Results Summary":
#                extract_timeline_data_observation(timeline_data, section["title"], clinical_data)

print_diagrams(timeline_data)