import streamlit as st

import pandas as pd
import plotly.express as px

patient_id = st.session_state.get('patient_id', None)
timeline_data = st.session_state.get('laboratory_data', None)

low_glucose = 60 # mg/dL
mid_glucose = 100 # mg/dL
high_glucose = 140 # mg/dL
mid_hemo = 6.5 # percent = 7,75 mmol/l = 47 mmol/mol
high_hemo = 8.5 # percent = 11 mmol/l = 69 mmol/mol

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
            lambda x: f'Marginal (< {low_glucose} mg/dL)' if x < low_glucose else ( f'Normal ({low_glucose}-{mid_glucose-1} mg/dL)' if low_glucose <= x < mid_glucose else (
                    f'Marginal ({mid_glucose}-{high_glucose-1} mg/dL)' if mid_glucose <= x < high_glucose else f'Abnormal (>= {high_glucose} mg/dL)')
        ))

        fig_glucose = px.line(
            glucose_df,
            x="Date",
            y="Value",
            color="Status",
            color_discrete_map={f'Marginal (< {low_glucose} mg/dL)': "orange", f'Normal ({low_glucose}-{mid_glucose-1} mg/dL)': "green",f'Marginal ({mid_glucose}-{high_glucose-1} mg/dL)': "orange", f'Abnormal (>= {high_glucose} mg/dL)': "red"},
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
                # Minimalbereich (< 60 mg/dL) in hellorange
                dict(
                    type="rect",
                    x0=min_date_with_buffer, x1=max_date_with_buffer,
                    y0=0, y1=low_glucose,
                    fillcolor="lightgoldenrodyellow",
                    opacity=0.2,
                    line_width=0
                ),
                # Normalbereich (60-99 mg/dL) in hellgrün
                dict(
                    type="rect",
                    x0=min_date_with_buffer, x1=max_date_with_buffer,
                    y0=low_glucose, y1=mid_glucose,
                    fillcolor="lightgreen",
                    opacity=0.2,
                    line_width=0
                ),
                # Marginalbereich (100-139 mg/dL) in hellorange
                dict(
                    type="rect",
                    x0=min_date_with_buffer, x1=max_date_with_buffer,
                    y0=mid_glucose, y1=high_glucose,
                    fillcolor="lightgoldenrodyellow",
                    opacity=0.2,
                    line_width=0
                ),
                # Abnormalbereich (>= 140 mg/dL) in hellrot
                dict(
                    type="rect",
                    x0=min_date_with_buffer, x1=max_date_with_buffer,
                    y0=high_glucose, y1=glucose_df['Value'].max(),  # Y-Wert bis zum maximalen Glukosewert
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
            if value < mid_hemo:
                return f'Normal (< {mid_hemo} %)'
            elif mid_hemo <= value < high_hemo:
                return f'Marginal ({mid_hemo}-{high_hemo-1} %)'
            else:
                return f'Abnormal (>= {high_hemo} %)'

        hemoglobin_df['Status'] = hemoglobin_df['Value'].apply(categorize_hba1c)

        # Plotly chart
        fig_hemoglobin = px.line(
            hemoglobin_df,
            x="Date",
            y="Value",
            color="Status",
            color_discrete_map={
                f"Normal (< {mid_hemo} %)": "green",
                f"Marginal ({mid_hemo}-{high_hemo-1} %)": "orange",
                f"Abnormal (>= {high_hemo} %)": "red"
            },
            markers=True,
            labels={"Value": "Hemoglobin  [%]", "Date": "Date"},
            title="Hemoglobin Levels Over Time (Ac1 Test)",
            hover_data=["Exact Date"]
        )
        
        # Punktgröße erhöhen
        fig_hemoglobin.update_traces(marker=dict(size=10), mode='markers')

        # Puffer für X-Achse
        min_date = hemoglobin_df['Date'].min()
        max_date = hemoglobin_df['Date'].max()
        buffer_days = pd.Timedelta(days=(max_date - min_date).days * 0.05)
        min_date_with_buffer = min_date - buffer_days
        max_date_with_buffer = max_date + buffer_days

        # Markierungsbereiche
        fig_hemoglobin.update_layout(
            shapes=[
                dict(type="rect", x0=min_date_with_buffer, x1=max_date_with_buffer,
                     y0=0, y1=mid_hemo, fillcolor="lightgreen", opacity=0.2, line_width=0),
                dict(type="rect", x0=min_date_with_buffer, x1=max_date_with_buffer,
                     y0=mid_hemo, y1=high_hemo, fillcolor="lightgoldenrodyellow", opacity=0.2, line_width=0),
                dict(type="rect", x0=min_date_with_buffer, x1=max_date_with_buffer,
                     y0=high_hemo, y1=hemoglobin_df['Value'].max() if not hemoglobin_df.empty else 7.0,
                     fillcolor="lightcoral", opacity=0.2, line_width=0)
            ]
        )

        # Diagramm anzeigen
        st.plotly_chart(fig_hemoglobin)
    else:
        st.info("No Hemoglobin data available.")

print_diagram_glucose(timeline_data)
print_diagram_hemoglobin(timeline_data)