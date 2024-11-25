import streamlit as st
from menu import menu_with_redirect
import pandas as pd
import plotly.express as px

patient_id = st.session_state.get('patient_id', None)
timeline_data = st.session_state.get('laboratory_data', None)
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
            symbol="Symbol",
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

print_timeline(timeline_data)
