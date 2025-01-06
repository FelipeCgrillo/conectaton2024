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

# Función para generar datos personalizados para el hover
def generate_custom_data(row):
    hover_lines = []
    
    # Añadir título/tipo de recurso
    if 'Title' in row and pd.notna(row['Title']):
        hover_lines.append(f"<b>{row['Title']}</b>")
    
    # Añadir fecha
    if 'Exact Date' in row and row['Exact Date']:
        hover_lines.append(f"Date: {row['Exact Date']}")
    
    # Añadir valor si existe
    if 'Value' in row and pd.notna(row['Value']):
        if 'Results - Glucose Level' in str(row['Title']):
            value = str(row['Value']).split()[0]  # Obtener solo el número
            try:
                hover_lines.append(f"Glucose: {float(value):.1f} mg/dL")
            except:
                hover_lines.append(f"Glucose: {row['Value']}")
        elif 'Results - Hemoglobin in Blood' in str(row['Title']):
            value = str(row['Value']).split()[0]  # Obtener solo el número
            try:
                hover_lines.append(f"Hemoglobin: {float(value):.1f} %")
            except:
                hover_lines.append(f"Hemoglobin: {row['Value']}")
        else:
            hover_lines.append(f"Value: {row['Value']}")
    
    return "<br>".join(hover_lines)

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
        f'Abnormal Glucose (< {low_glucose} mg/dL)': {'color': 'red', 'symbol': 'star'},
        f'Normal Glucose ({low_glucose}-{mid_glucose-1} mg/dL)': {'color': 'green', 'symbol': 'square'},  # Grün und Viereck
        f'Marginal Glucose ({mid_glucose}-{high_glucose-1} mg/dL)': {'color': 'orange', 'symbol': 'triangle-up'},  # Orange und Dreieck
        f'Abnormal Glucose (>= {high_glucose} mg/dL)': {'color': 'red', 'symbol': 'star'},  # Rot und Stern
        f'Normal Hemoglobin (< {mid_hemo} %)': {'color': 'green', 'symbol': 'square'},  # Grün und Viereck
        f'Marginal Hemoglobin ({mid_hemo}-{high_hemo-1} %)': {'color': 'orange', 'symbol': 'triangle-up'},  # Orange und Dreieck
        f'Abnormal Hemoglobin (>= {high_hemo} %)': {'color': 'red', 'symbol': 'star'},  # Rot und Stern
        f'Neutral': {'color': 'blue', 'symbol': 'circle'}  # Blau und Kreis
    }

    if 'Results - Glucose Level' in df['Title'].values or 'Results - Hemoglobin in Blood' in df['Title'].values:
        if 'Results - Glucose Level' in df['Title'].values:
            glucose_df_timeline = df[df['Title'] == "Results - Glucose Level"]
            glucose_df_timeline['Value'] = glucose_df_timeline['Value'].str.extract(r'(\d+\.?\d*)').astype(float)  # Extract numeric values
            glucose_df_timeline['Status'] = glucose_df_timeline['Value'].apply(
                lambda x: f'Marginal Glucose (< {low_glucose} mg/dL)' if x < low_glucose else ( f'Normal Glucose ({low_glucose}-{mid_glucose-1} mg/dL)' if low_glucose <= x < mid_glucose else (
                    f'Marginal Glucose ({mid_glucose}-{high_glucose-1} mg/dL)' if mid_glucose <= x < high_glucose else f'Abnormal Glucose (>= {high_glucose} mg/dL)')
                )
            )
            # Zuweisung von Farben und Symbolen basierend auf Status
            glucose_df_timeline['Color'] = glucose_df_timeline['Status'].map(lambda x: style_map[x]['color']).fillna('blue')
            glucose_df_timeline['Symbol'] = glucose_df_timeline['Status'].map(lambda x: style_map[x]['symbol']).fillna('circle')

            # Werte in das Haupt-DataFrame übernehmen
            df.loc[glucose_df_timeline.index, 'Color'] = glucose_df_timeline['Color']
            df.loc[glucose_df_timeline.index, 'Symbol'] = glucose_df_timeline['Symbol']
            df.loc[glucose_df_timeline.index, 'Color'] = glucose_df_timeline['Status']

        if 'Results - Hemoglobin in Blood' in df['Title'].values:
            hemoglobin_df_timeline = df[df['Title'] == "Results - Hemoglobin in Blood"]
            hemoglobin_df_timeline['Value'] = hemoglobin_df_timeline['Value'].str.extract(r'(\d+\.?\d*)').astype(float)  # Extract numeric values
            hemoglobin_df_timeline['Status'] = hemoglobin_df_timeline['Value'].apply(
                lambda x: f'Normal Hemoglobin (< {mid_hemo} %)' if x < mid_hemo else (
                    f'Marginal Hemoglobin ({mid_hemo}-{high_hemo-1} %)' if mid_hemo <= x < high_hemo else f'Abnormal Hemoglobin (>= {high_hemo} %)'
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

    # Preparar los datos para el gráfico
    filtered_df['Exact Date'] = filtered_df['Date'].dt.strftime('%B %d, %Y')
    
    # Formatear valores
    def format_value(row):
        if pd.isna(row['Value']):
            return 'N/A'
        try:
            # Extraer el valor numérico
            value = str(row['Value']).split()[0]
            numeric_value = float(value)
            
            # Formatear según el tipo de medición
            if 'Results - Glucose Level' in row['Title']:
                return f"{numeric_value:.1f} mg/dL"
            elif 'Results - Hemoglobin in Blood' in row['Title']:
                return f"{numeric_value:.1f} %"
            else:
                return str(row['Value'])
        except (ValueError, IndexError):
            return str(row['Value'])
    
    # Aplicar el formato a los valores
    filtered_df['Value'] = filtered_df.apply(format_value, axis=1)
    
    # Asegurarse de que todos los valores tengan el formato correcto
    glucose_mask = filtered_df['Title'] == 'Results - Glucose Level'
    hemoglobin_mask = filtered_df['Title'] == 'Results - Hemoglobin in Blood'
    
    # Verificar y corregir valores de glucosa
    if glucose_mask.any():
        filtered_df.loc[glucose_mask, 'Value'] = filtered_df.loc[glucose_mask].apply(
            lambda x: f"{float(str(x['Value']).split()[0]):.1f} mg/dL" 
            if not pd.isna(x['Value']) and 'mg/dL' not in str(x['Value']) 
            else x['Value'], 
            axis=1
        )
    
    # Verificar y corregir valores de hemoglobina
    if hemoglobin_mask.any():
        filtered_df.loc[hemoglobin_mask, 'Value'] = filtered_df.loc[hemoglobin_mask].apply(
            lambda x: f"{float(str(x['Value']).split()[0]):.1f} %" 
            if not pd.isna(x['Value']) and '%' not in str(x['Value']) 
            else x['Value'], 
            axis=1
        )

    # Asegurarse de que el estado esté presente y formateado
    if 'Status' not in filtered_df.columns:
        filtered_df['Status'] = filtered_df.apply(
            lambda row: row.get('Color', 'Neutral') if pd.isna(row.get('Status')) else row.get('Status'),
            axis=1
        )

    # Wende die Funktion auf die DataFrame-Zeilen an
    filtered_df['hover_info'] = filtered_df.apply(generate_custom_data, axis=1)

    # Plotly Timeline Diagramm erstellen
    if not filtered_df.empty:
        # Crear un gráfico de dispersión para todos los datos
        fig = px.scatter(
            filtered_df,
            x="Date",
            y="Title",
            color="Color",
            symbol="Symbol",
            color_discrete_map={key: val['color'] for key, val in style_map.items()},
            symbol_map={key: val['symbol'] for key, val in style_map.items()},
            labels={"Date": "Date", "Title": "Resource Type", "Color": "Legend"}
        )

        # Añadir línea para conectar los puntos de glucosa
        glucose_data = filtered_df[filtered_df['Title'] == "Results - Glucose Level"].copy()
        if not glucose_data.empty:
            glucose_data['Value'] = glucose_data['Value'].str.extract(r'(\d+\.?\d*)').astype(float)
            fig.add_scatter(
                x=glucose_data['Date'],
                y=glucose_data['Title'],
                mode='lines',
                line=dict(color='gray', width=1, dash='dot'),
                showlegend=False,
                hoverinfo='skip'
            )

        # Actualizar las trazas para mostrar la información correctamente
        for trace in fig.data:
            if hasattr(trace, 'text'):
                trace.update(
                    hovertemplate="<b>%{y}</b><br>" +
                                "Date: %{x|%B %d, %Y}<br>" +
                                "Value: %{text}<extra></extra>",
                    text=filtered_df['Value']
                )

        # Ajustar la leyenda
        fig.for_each_trace(
            lambda trace: trace.update(name=trace.name.split(",")[0] if trace.name else "")
        )

        # Configurar el diseño
        fig.update_layout(
            clickmode="event+select",
            legend=dict(
                x=0.5,
                y=-0.5,
                orientation="h"
            ),
            hoverlabel=dict(
                bgcolor="white",
                font_size=14,
                font_family="Arial"
            )
        )

        # Mostrar el gráfico
        st.plotly_chart(fig)
    else:
        st.warning("No data available for the selected filters.")

print_timeline(timeline_data)
