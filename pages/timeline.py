import streamlit as st
from menu import menu_with_redirect
import pandas as pd
import plotly.express as px

patient_id = st.session_state.get('patient_id', None)
timeline_data = st.session_state.get('laboratory_data', None)
menu_with_redirect()

# Hilfsfunktion zur Erstellung von Name-Value-Paaren für eine beliebige Anzahl
def generate_custom_data(row):
    # Beginne mit den Basisfeldern
    hover_lines = [f"Exact Date: {row['Exact Date']}" if 'Exact Date' in row and row['Exact Date'] else ""]
    if 'Name' in row and pd.notna(row['Name']):
        hover_lines.append(f"Name: {row['Name']}")
    if 'Value' in row and pd.notna(row['Value']):
        hover_lines.append(f"Value: {row['Value']}")
    # Dynamisch Name-Value-Paare hinzufügen
    for i in range(5):  # Passe die maximale Anzahl von Paaren an
        name_key = f"Name {i}"
        value_key = f"Value {i}"
        name = row.get(name_key, None)
        value = row.get(value_key, None)
        # Füge das Paar nur hinzu, wenn beide Werte existieren und nicht NaN sind
        if pd.notna(name) and pd.notna(value):
            hover_lines.append(f"{name}: {value}")
    # Entferne leere Zeilen und erstelle einen zusammenhängenden String
    return "<br>".join(hover_lines) if hover_lines else None

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
        'Normal Glucose (< 140 mg/dL)': {'color': 'green', 'symbol': 'square'},  # Grün und Viereck
        'Marginal Glucose (140-199 mg/dL)': {'color': 'orange', 'symbol': 'triangle-up'},  # Orange und Dreieck
        'Abnormal Glucose (>= 200 mg/dL)': {'color': 'red', 'symbol': 'star'},  # Rot und Stern
        'Normal Hemoglobin (20–38 mmol/mol)': {'color': 'green', 'symbol': 'square'},  # Grün und Viereck
        'Marginal Hemoglobin (39–47 mmol/mol)': {'color': 'orange', 'symbol': 'triangle-up'},  # Orange und Dreieck
        'Abnormal Hemoglobin (> 48 mmol/mol)': {'color': 'red', 'symbol': 'star'},  # Rot und Stern
        'Neutral': {'color': 'blue', 'symbol': 'circle'}  # Blau und Kreis
    }

    if 'Observation - Glucose Level' in df['Title'].values or 'Observation - Hemoglobin in Blood' in df['Title'].values:
        if 'Observation - Glucose Level' in df['Title'].values:
            glucose_df_timeline = df[df['Title'] == "Observation - Glucose Level"]
            glucose_df_timeline['Value'] = glucose_df_timeline['Value'].str.extract(r'(\d+\.?\d*)').astype(float)  # Extract numeric values
            glucose_df_timeline['Status'] = glucose_df_timeline['Value'].apply(
                lambda x: 'Normal Glucose (< 140 mg/dL)' if x < 140 else (
                    'Marginal Glucose (140-199 mg/dL)' if 140 <= x <= 199 else 'Abnormal Glucose (>= 200 mg/dL)'
                )
            )
            # Zuweisung von Farben und Symbolen basierend auf Status
            glucose_df_timeline['Color'] = glucose_df_timeline['Status'].map(lambda x: style_map[x]['color']).fillna('blue')
            glucose_df_timeline['Symbol'] = glucose_df_timeline['Status'].map(lambda x: style_map[x]['symbol']).fillna('circle')

            # Werte in das Haupt-DataFrame übernehmen
            df.loc[glucose_df_timeline.index, 'Color'] = glucose_df_timeline['Color']
            df.loc[glucose_df_timeline.index, 'Symbol'] = glucose_df_timeline['Symbol']
            df.loc[glucose_df_timeline.index, 'Color'] = glucose_df_timeline['Status']

        if 'Observation - Hemoglobin in Blood' in df['Title'].values:
            hemoglobin_df_timeline = df[df['Title'] == "Observation - Hemoglobin in Blood"]
            hemoglobin_df_timeline['Value'] = hemoglobin_df_timeline['Value'].str.extract(r'(\d+\.?\d*)').astype(float)  # Extract numeric values
            hemoglobin_df_timeline['Status'] = hemoglobin_df_timeline['Value'].apply(
                lambda x: 'Normal Hemoglobin (20–38 mmol/mol)' if x <= 5.6 else (
                    'Marginal Hemoglobin (39–47 mmol/mol)' if 5.6 < x <= 6.4 else 'Abnormal Hemoglobin (> 48 mmol/mol)'
                )
            )
            # Zuweisung von Farben und Symbolen basierend auf Status
            hemoglobin_df_timeline['Color'] = hemoglobin_df_timeline['Status'].map(lambda x: style_map[x]['color']).fillna('blue')
            hemoglobin_df_timeline['Symbol'] = hemoglobin_df_timeline['Status'].map(lambda x: style_map[x]['symbol']).fillna('circle')

            # Werte in das Haupt-DataFrame übernehmen
            df.loc[hemoglobin_df_timeline.index, 'Color'] = hemoglobin_df_timeline['Color']
            df.loc[hemoglobin_df_timeline.index, 'Symbol'] = hemoglobin_df_timeline['Symbol']
            df.loc[hemoglobin_df_timeline.index, 'Color'] = hemoglobin_df_timeline['Status']
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

    # Wende die Funktion auf die DataFrame-Zeilen an
    filtered_df['hover_info'] = filtered_df.apply(generate_custom_data, axis=1)

    # Plotly Timeline Diagramm erstellen
    if not filtered_df.empty:
        fig = px.scatter(
            filtered_df,
            x="Date",
            y="Title",
            color="Color",
            symbol="Symbol",
            color_discrete_map={key: val['color'] for key, val in style_map.items()},
            symbol_map={key: val['symbol'] for key, val in style_map.items()},
            labels={"Date": "Date", "Title": "Resource Type", "Color": "Legend"},
            custom_data=["hover_info"],
            hover_data={
                "Symbol": False
            }
        )

        # Legenden-Einträge anpassen/entfernen
        fig.for_each_trace(
            lambda trace: trace.update(name=trace.name.split(",")[0])  # Entferne alles nach dem Komma (z. B. "Symbol")
        )

        fig.update_traces(
            #text=filtered_df["Symbol"].where(filtered_df["Symbol"] != "", filtered_df["Name"]),
            marker=dict(size=12, opacity=0.7),
            mode="markers+text",
            textposition="top center",
            hovertemplate="%{customdata[0]}"
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

print_timeline(timeline_data)
