import streamlit as st
from menu import menu_with_redirect
import pandas as pd
import plotly.express as px
import requests
from fhir.resources.composition import Composition

patient_id = st.session_state.get('patient_id', None)
menu_with_redirect()

def print_timeline(data):
    
    # Verify the user's role
    if not st.session_state.patient_id:
        st.warning("No patient found.")
        st.stop()

    st.title("Clinical Timeline")

    # Convert data into a DataFrame
    df = pd.DataFrame(data)
    df['Date'] = pd.to_datetime(df['Date'])

    # Add color
    df['Color'] = "Neutral"
    # Add symbol
    df['Symbol'] = "circle"

    style_map = {
        'Normal (< 140 mg/dL)': {'color': 'green', 'symbol': 'square'},  # Grün und Viereck
        'Marginal (140-199 mg/dL)': {'color': 'orange', 'symbol': 'triangle-up'},  # Orange und Dreieck
        'Abnormal (>= 200 mg/dL)': {'color': 'red', 'symbol': 'star'},  # Rot und Stern
        'Neutral': {'color': 'blue', 'symbol': 'circle'}  # Blau und Kreis
    }

    if 'Observation - Glucose Level' in df['Title'].values:
        glucose_df_timeline = df[df['Title'] == "Observation - Glucose Level"]
        glucose_df_timeline['Value'] = glucose_df_timeline['Value'].str.extract(r'(\d+\.?\d*)').astype(float)  # Extract numeric values
        glucose_df_timeline['Status'] = glucose_df_timeline['Value'].apply(
            lambda x: 'Normal (< 140 mg/dL)' if x < 140 else (
                'Marginal (140-199 mg/dL)' if 140 <= x <= 199 else 'Abnormal (>= 200 mg/dL)'
            )
        )
        # Zuweisung von Farben und Symbolen basierend auf Status
        glucose_df_timeline['Color'] = glucose_df_timeline['Status'].map(lambda x: style_map[x]['color']).fillna('blue')
        glucose_df_timeline['Symbol'] = glucose_df_timeline['Status'].map(lambda x: style_map[x]['symbol']).fillna('circle')

        # Werte in das Haupt-DataFrame übernehmen
        df.loc[glucose_df_timeline.index, 'Color'] = glucose_df_timeline['Color']
        df.loc[glucose_df_timeline.index, 'Symbol'] = glucose_df_timeline['Symbol']
        
        df.loc[glucose_df_timeline.index, 'Color'] = glucose_df_timeline['Status']
    else:
        df['Color'] = "Neutral"  # Standardfarbe für andere Daten
        df['Symbol'] = "circle"

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

    filtered_df['Exact Date'] = filtered_df['Date'].dt.strftime('%B %d, %Y')

    # Plotly Timeline Diagramm erstellen
    if not filtered_df.empty:
        fig = px.scatter(
            filtered_df,
            x="Date",
            y="Title",
            color="Color",
            symbol="Symbol",  # Form der Punkte
            color_discrete_map={key: val['color'] for key, val in style_map.items()},  # Farbskala
            symbol_map={key: val['symbol'] for key, val in style_map.items()},
            labels={"Date": "Date", "Title": "Resource Type", "Color": "Legend"},
            hover_data=["Name", "Exact Date"]
        )
        
        fig.update_traces(
            #text=filtered_df["Symbol"].where(filtered_df["Symbol"] != "", filtered_df["Name"]),
            marker=dict(size=12, opacity=0.7),
            mode="markers+text",
            textposition="top center"
        )
        
        fig.update_layout(clickmode="event+select", legend=dict(
                                                            x=0.5,  # Zentriert horizontal
                                                            y=-0.5,  # Oberhalb des Diagramms
                                                            orientation="h",  # Horizontal
                                                        )
        )

        # Zeitstrahl in Streamlit anzeigen
        st.plotly_chart(fig)
    else:
        st.warning("No data available for the selected filters.")

# Funktion zum Abrufen der Daten
def fetch_fhir_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Fehler beim Abrufen der Daten: {response.status_code}")
        return None

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
composition_data = fetch_fhir_data(f"https://ips-challenge.it.hs-heilbronn.de/fhir/Composition?patient={patient_id}")
if not composition_data or "entry" not in composition_data:
    st.error("No data found for the patient. Please check the patient ID or data source.")
    st.stop()

resource = composition_data["entry"][0]["resource"]
#st.title(resource["title"])

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

print_timeline(timeline_data)
