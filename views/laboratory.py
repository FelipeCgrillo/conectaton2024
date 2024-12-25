import streamlit as st

import pandas as pd
import plotly.express as px

patient_id = st.session_state.get('patient_id', None)
timeline_data = st.session_state.get('laboratory_data', None)


st.title("Laboratory Results")

def print_diagram_glucose(data):
    # Convert data into a DataFrame
    df = pd.DataFrame(data)
    df['Date'] = pd.to_datetime(df['Date'])

    # Glucose values chart
    glucose_df = df[df['Title'] == "Results - Glucose Level"]

    if not glucose_df.empty:# and not glucose_df.isna().all().all():
        # Add color
        glucose_df['Color'] = "Neutral"
        # Add symbol
        glucose_df['Symbol'] = "circle"
        glucose_df.loc[:, 'Exact Date'] = df['Date'].dt.strftime('%B %d, %Y')
        glucose_df['Value'] = glucose_df['Value'].str.extract(r'(\d+\.?\d*)').astype(float)  # Extract numeric values
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
            labels={"Value": "Glucose Level [mg/dL]", "Date": "Date"},
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

def print_diagram_hemoglobin(data):
    # Convert data into a DataFrame
    df = pd.DataFrame(data)
    df['Date'] = pd.to_datetime(df['Date'])

    # Glucose values chart
    hemoglobin_df = df[df['Title'] == "Results - Hemoglobin in Blood"]
    #hemoglobin_df = hemoglobin_df[hemoglobin_df['Name'].str.contains("Hemoglobin", case=False)]
    
    if not hemoglobin_df.empty:
        hemoglobin_df['Value'] = hemoglobin_df['Value'].str.extract(r'(\d+\.?\d*)').astype(float)  # Extract numeric values
        hemoglobin_df['Exact Date'] = hemoglobin_df['Date'].dt.strftime('%B %d, %Y')
        
        # Categorize values
        def categorize_hba1c(value):
            if value <= 5.6:
                return 'Normal (20–38 mmol/mol)'
            elif 5.6 < value <= 6.4:
                return 'Marginal (39–47 mmol/mol)'
            else:
                return 'Abnormal (> 48 mmol/mol)'

        hemoglobin_df['Status'] = hemoglobin_df['Value'].apply(categorize_hba1c)

        # Plotly chart
        fig_glucose = px.line(
            hemoglobin_df,
            x="Date",
            y="Value",
            color="Status",
            color_discrete_map={
                "Normal (20–38 mmol/mol)": "green",
                "Marginal (39–47 mmol/mol)": "orange",
                "Abnormal (> 48 mmol/mol)": "red"
            },
            markers=True,
            labels={"Value": "Hemoglobin  [%]", "Date": "Date"},
            title="Hemoglobin Levels Over Time",
            hover_data=["Exact Date"]
        )
        
        # Punktgröße erhöhen
        fig_glucose.update_traces(marker=dict(size=10), mode='markers')

        # Puffer für X-Achse
        min_date = hemoglobin_df['Date'].min()
        max_date = hemoglobin_df['Date'].max()
        buffer_days = pd.Timedelta(days=(max_date - min_date).days * 0.05)
        min_date_with_buffer = min_date - buffer_days
        max_date_with_buffer = max_date + buffer_days

        # Markierungsbereiche
        fig_glucose.update_layout(
            shapes=[
                dict(type="rect", x0=min_date_with_buffer, x1=max_date_with_buffer,
                     y0=4.0, y1=5.7, fillcolor="lightgreen", opacity=0.2, line_width=0),
                dict(type="rect", x0=min_date_with_buffer, x1=max_date_with_buffer,
                     y0=5.7, y1=6.5, fillcolor="lightgoldenrodyellow", opacity=0.2, line_width=0),
                dict(type="rect", x0=min_date_with_buffer, x1=max_date_with_buffer,
                     y0=6.5, y1=hemoglobin_df['Value'].max() if not hemoglobin_df.empty else 7.0,
                     fillcolor="lightcoral", opacity=0.2, line_width=0)
            ]
        )

        # Diagramm anzeigen
        st.plotly_chart(fig_glucose)
    else:
        st.info("No Hemoglobin data available.")

print_diagram_glucose(timeline_data)
print_diagram_hemoglobin(timeline_data)