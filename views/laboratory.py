import streamlit as st
import pandas as pd
import plotly.express as px

# Language translations
TRANSLATIONS = {
    'en': {
        'select_language': 'Select Language',
        'please_select_patient': 'Please select a patient first.',
        'no_lab_data': 'No laboratory data available for this patient.',
        'laboratory_results': 'Laboratory Results',
        'patient_summary': 'Patient Summary',
        'patient_id': 'Patient ID',
        'analysis_parameters': 'Analysis Parameters',
        'severe_hypoglycemia': 'Severe Hypoglycemia',
        'hypoglycemia_alert': 'Hypoglycemia Alert',
        'glucose_target_range': 'Glucose Target Range',
        'significant_hyperglycemia': 'Significant Hyperglycemia',
        'general_hba1c_target': 'General HbA1c Target',
        'strict_hba1c_target': 'Strict HbA1c Target',
        'relaxed_hba1c_target': 'Relaxed HbA1c Target',
        'no_date_info': 'No date information found in the data',
        'dates_parse_error': 'Some dates could not be parsed correctly',
        'no_valid_data': 'No valid data available after date processing',
        'glucose_level': 'Glucose Level',
        'date': 'Date',
        'glucose_levels_time': 'Glucose Levels Over Time',
        'glycemic_control': 'Glycemic Control Analysis',
        'time_in_range': 'Time in Range',
        'target': 'Target',
        'minimize': 'Minimize',
        'hypoglycemic_events': 'Hypoglycemic Events',
        'hyperglycemic_events': 'Hyperglycemic Events',
        'clinical_recommendations': 'Clinical Recommendations',
        'time_range_warning': 'Time in range is below recommended target (>70%). Consider treatment adjustment.',
        'hypo_events_warning': 'Detected {} hypoglycemic events. Review medication dosing and eating patterns.',
        'hyper_events_warning': 'Detected {} significant hyperglycemic events. Evaluate treatment adherence and consider therapy adjustments.',
        'no_glucose_data': 'No glucose data available.',
        'error_processing': 'Error processing {} data: {}',
        'hba1c_levels_time': 'HbA1c Levels Over Time',
        'long_term_analysis': 'Long-term Glycemic Control Analysis',
        'latest_hba1c': 'Latest HbA1c Value',
        'control_status': 'Control Status',
        'on_target': 'On Target',
        'off_target': 'Off Target',
        'hba1c_below_warning': 'HbA1c below strict target. Evaluate hypoglycemia risk.',
        'excellent_control': 'Excellent glycemic control. Maintain current regimen.',
        'suboptimal_control': 'Suboptimal control. Consider treatment intensification.',
        'inadequate_control': 'Inadequate control. Urgent review of therapeutic regimen recommended.',
        'upward_trend': 'Upward trend in HbA1c (+{}%). Evaluate contributing factors.',
        'improvement': 'Improvement in glycemic control ({}%). Maintain effective strategies.',
        'no_hba1c_data': 'No HbA1c data available.'
    },
    'es': {
        'select_language': 'Seleccionar Idioma',
        'please_select_patient': 'Por favor, seleccione un paciente primero.',
        'no_lab_data': 'No hay datos de laboratorio disponibles para este paciente.',
        'laboratory_results': 'Resultados de Laboratorio',
        'patient_summary': 'Resumen del Paciente',
        'patient_id': 'ID del Paciente',
        'analysis_parameters': 'Parámetros de Análisis',
        'severe_hypoglycemia': 'Hipoglucemia Severa',
        'hypoglycemia_alert': 'Alerta de Hipoglucemia',
        'glucose_target_range': 'Rango Objetivo de Glucosa',
        'significant_hyperglycemia': 'Hiperglucemia Significativa',
        'general_hba1c_target': 'Objetivo General de HbA1c',
        'strict_hba1c_target': 'Objetivo Estricto de HbA1c',
        'relaxed_hba1c_target': 'Objetivo Relajado de HbA1c',
        'no_date_info': 'No se encontró información de fechas en los datos',
        'dates_parse_error': 'Algunas fechas no pudieron ser procesadas correctamente',
        'no_valid_data': 'No hay datos válidos disponibles después del procesamiento',
        'glucose_level': 'Nivel de Glucosa',
        'date': 'Fecha',
        'glucose_levels_time': 'Niveles de Glucosa en el Tiempo',
        'glycemic_control': 'Análisis del Control Glucémico',
        'time_in_range': 'Tiempo en Rango',
        'target': 'Objetivo',
        'minimize': 'Minimizar',
        'hypoglycemic_events': 'Eventos de Hipoglucemia',
        'hyperglycemic_events': 'Eventos de Hiperglucemia',
        'clinical_recommendations': 'Recomendaciones Clínicas',
        'time_range_warning': 'El tiempo en rango está por debajo del objetivo recomendado (>70%). Considere ajustar el tratamiento.',
        'hypo_events_warning': 'Se detectaron {} eventos de hipoglucemia. Revisar la dosificación de medicamentos y el patrón de alimentación.',
        'hyper_events_warning': 'Se detectaron {} eventos de hiperglucemia significativa. Evaluar la adherencia al tratamiento y considerar ajustes en la terapia.',
        'no_glucose_data': 'No hay datos de glucosa disponibles.',
        'error_processing': 'Error al procesar los datos de {}: {}',
        'hba1c_levels_time': 'Niveles de HbA1c en el Tiempo',
        'long_term_analysis': 'Análisis del Control Glucémico a Largo Plazo',
        'latest_hba1c': 'Último valor de HbA1c',
        'control_status': 'Estado del Control',
        'on_target': 'En Objetivo',
        'off_target': 'Fuera de Objetivo',
        'hba1c_below_warning': 'HbA1c por debajo del objetivo estricto. Evaluar riesgo de hipoglucemia.',
        'excellent_control': 'Excelente control glucémico. Mantener el régimen actual.',
        'suboptimal_control': 'Control subóptimo. Considerar intensificación del tratamiento.',
        'inadequate_control': 'Control inadecuado. Se recomienda revisión urgente del régimen terapéutico.',
        'upward_trend': 'Tendencia al alza en HbA1c (+{}%). Evaluar factores contribuyentes.',
        'improvement': 'Mejora en el control glucémico ({}%). Mantener estrategias efectivas.',
        'no_hba1c_data': 'No hay datos de HbA1c disponibles.'
    }
}

# Initialize language in session state if not present
if 'language' not in st.session_state:
    st.session_state.language = 'en'

# Language selector
language = st.selectbox(
    TRANSLATIONS[st.session_state.language]['select_language'],
    ['en', 'es'],
    index=0 if st.session_state.language == 'en' else 1
)

# Update language in session state if changed
if language != st.session_state.language:
    st.session_state.language = language

# Helper function to get translated text
def t(key, *args):
    text = TRANSLATIONS[st.session_state.language].get(key, key)
    if args:
        return text.format(*args)
    return text

# Check if a patient is selected
if "patient_id" not in st.session_state or not st.session_state.patient_id:
    st.warning(t('please_select_patient'))
    st.stop()

# Check if laboratory data is available
timeline_data = st.session_state.get('laboratory_data', None)
if timeline_data is None or len(timeline_data) == 0:
    st.warning(t('no_lab_data'))
    st.stop()

# Ranges according to ADA/EASD 2023
class GlucoseRanges:
    # General ranges
    HYPOGLYCEMIA_SEVERE = 54  # mg/dL
    HYPOGLYCEMIA_ALERT = 70   # mg/dL
    TARGET_LOWER = 80         # mg/dL
    TARGET_UPPER = 130        # mg/dL
    HYPERGLYCEMIA_ALERT = 180 # mg/dL
    
    # Pregnancy-specific ranges
    PREGNANCY_FASTING = 95    # mg/dL
    PREGNANCY_1H = 140        # mg/dL
    PREGNANCY_2H = 120        # mg/dL

class HbA1cRanges:
    TARGET_GENERAL = 7.0      # %
    TARGET_STRICT = 6.5       # % (for selected patients without hypoglycemia risk)
    TARGET_RELAXED = 8.0      # % (for patients with comorbidities or elderly)
    DIAGNOSIS_THRESHOLD = 6.5  # % (threshold for diabetes diagnosis)

# Use the new ranges
low_glucose = GlucoseRanges.HYPOGLYCEMIA_ALERT
mid_glucose = GlucoseRanges.TARGET_LOWER
high_glucose = GlucoseRanges.TARGET_UPPER
very_high_glucose = GlucoseRanges.HYPERGLYCEMIA_ALERT

mid_hemo = HbA1cRanges.TARGET_GENERAL
high_hemo = HbA1cRanges.TARGET_RELAXED

st.title(t('laboratory_results'))

# Display patient summary
st.header(t('patient_summary'))
st.write(f"{t('patient_id')}: {st.session_state.patient_id}")
st.write(t('analysis_parameters'))
st.write(f"- {t('severe_hypoglycemia')}: < {GlucoseRanges.HYPOGLYCEMIA_SEVERE} mg/dL")
st.write(f"- {t('hypoglycemia_alert')}: {GlucoseRanges.HYPOGLYCEMIA_SEVERE}-{GlucoseRanges.HYPOGLYCEMIA_ALERT-1} mg/dL")
st.write(f"- {t('glucose_target_range')}: {GlucoseRanges.TARGET_LOWER}-{GlucoseRanges.TARGET_UPPER} mg/dL")
st.write(f"- {t('significant_hyperglycemia')}: > {GlucoseRanges.HYPERGLYCEMIA_ALERT} mg/dL")
st.write(f"- {t('general_hba1c_target')}: {HbA1cRanges.TARGET_GENERAL}%")
st.write(f"- {t('strict_hba1c_target')}: {HbA1cRanges.TARGET_STRICT}%")
st.write(f"- {t('relaxed_hba1c_target')}: {HbA1cRanges.TARGET_RELAXED}%")

def print_diagram_glucose(data):
    df = pd.DataFrame(data)
    
    if 'Date' not in df.columns:
        st.error(t('no_date_info'))
        return
        
    try:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        if df['Date'].isna().any():
            st.warning(t('dates_parse_error'))
            df = df.dropna(subset=['Date'])
        
        if df.empty:
            st.info(t('no_valid_data'))
            return

        # Glucose values chart
        glucose_df = df[df['Title'] == "Results - Glucose Level"]

        if not glucose_df.empty:
            glucose_df['Color'] = "Neutral"
            glucose_df['Symbol'] = "circle"
            glucose_df.loc[:, 'Exact Date'] = glucose_df['Date'].dt.strftime('%B %d, %Y')
            glucose_df['Value'] = glucose_df['Value'].str.extract(r'(\d+\.?\d*)').astype(float)

            # New classification according to ADA/EASD
            def classify_glucose(value):
                if value < GlucoseRanges.HYPOGLYCEMIA_SEVERE:
                    return f'{t("severe_hypoglycemia")} (< {GlucoseRanges.HYPOGLYCEMIA_SEVERE} mg/dL)'
                elif value < GlucoseRanges.HYPOGLYCEMIA_ALERT:
                    return f'{t("hypoglycemia_alert")} ({GlucoseRanges.HYPOGLYCEMIA_SEVERE}-{GlucoseRanges.HYPOGLYCEMIA_ALERT-1} mg/dL)'
                elif GlucoseRanges.HYPOGLYCEMIA_ALERT <= value < GlucoseRanges.TARGET_LOWER:
                    return f'{t("below_target")} ({GlucoseRanges.HYPOGLYCEMIA_ALERT}-{GlucoseRanges.TARGET_LOWER-1} mg/dL)'
                elif GlucoseRanges.TARGET_LOWER <= value <= GlucoseRanges.TARGET_UPPER:
                    return f'{t("target_range")} ({GlucoseRanges.TARGET_LOWER}-{GlucoseRanges.TARGET_UPPER} mg/dL)'
                elif GlucoseRanges.TARGET_UPPER < value <= GlucoseRanges.HYPERGLYCEMIA_ALERT:
                    return f'{t("above_target")} ({GlucoseRanges.TARGET_UPPER+1}-{GlucoseRanges.HYPERGLYCEMIA_ALERT} mg/dL)'
                else:
                    return f'{t("significant_hyperglycemia")} (> {GlucoseRanges.HYPERGLYCEMIA_ALERT} mg/dL)'

            glucose_df['Status'] = glucose_df['Value'].apply(classify_glucose)

            # Updated colors for better visualization
            color_map = {
                f'{t("severe_hypoglycemia")} (< {GlucoseRanges.HYPOGLYCEMIA_SEVERE} mg/dL)': "red",
                f'{t("hypoglycemia_alert")} ({GlucoseRanges.HYPOGLYCEMIA_SEVERE}-{GlucoseRanges.HYPOGLYCEMIA_ALERT-1} mg/dL)': "orange",
                f'{t("below_target")} ({GlucoseRanges.HYPOGLYCEMIA_ALERT}-{GlucoseRanges.TARGET_LOWER-1} mg/dL)': "yellow",
                f'{t("target_range")} ({GlucoseRanges.TARGET_LOWER}-{GlucoseRanges.TARGET_UPPER} mg/dL)': "green",
                f'{t("above_target")} ({GlucoseRanges.TARGET_UPPER+1}-{GlucoseRanges.HYPERGLYCEMIA_ALERT} mg/dL)': "yellow",
                f'{t("significant_hyperglycemia")} (> {GlucoseRanges.HYPERGLYCEMIA_ALERT} mg/dL)': "red"
            }

            fig_glucose = px.line(
                glucose_df,
                x="Date",
                y="Value",
                color="Status",
                color_discrete_map=color_map,
                markers=True,
                labels={"Value": f"{t('glucose_level')} [mg/dL]", "Date": t('date')},
                title=t('glucose_levels_time'),
                hover_data=["Exact Date"]
            )

            fig_glucose.update_traces(marker=dict(size=10))
            fig_glucose.update_traces(mode='markers')

            # Calculate X-axis ranges
            min_date = glucose_df['Date'].min()
            max_date = glucose_df['Date'].max()
            buffer_days = (max_date - min_date) * 0.05
            min_date_with_buffer = min_date - buffer_days
            max_date_with_buffer = max_date + buffer_days

            # Update shaded areas according to new ranges
            fig_glucose.update_layout(
                shapes=[
                    # Severe hypoglycemia
                    dict(
                        type="rect",
                        x0=min_date_with_buffer, x1=max_date_with_buffer,
                        y0=0, y1=GlucoseRanges.HYPOGLYCEMIA_SEVERE,
                        fillcolor="mistyrose",
                        opacity=0.2,
                        line_width=0
                    ),
                    # Hypoglycemia alert
                    dict(
                        type="rect",
                        x0=min_date_with_buffer, x1=max_date_with_buffer,
                        y0=GlucoseRanges.HYPOGLYCEMIA_SEVERE, y1=GlucoseRanges.HYPOGLYCEMIA_ALERT,
                        fillcolor="lightsalmon",
                        opacity=0.2,
                        line_width=0
                    ),
                    # Below target
                    dict(
                        type="rect",
                        x0=min_date_with_buffer, x1=max_date_with_buffer,
                        y0=GlucoseRanges.HYPOGLYCEMIA_ALERT, y1=GlucoseRanges.TARGET_LOWER,
                        fillcolor="khaki",
                        opacity=0.2,
                        line_width=0
                    ),
                    # Target range
                    dict(
                        type="rect",
                        x0=min_date_with_buffer, x1=max_date_with_buffer,
                        y0=GlucoseRanges.TARGET_LOWER, y1=GlucoseRanges.TARGET_UPPER,
                        fillcolor="lightgreen",
                        opacity=0.2,
                        line_width=0
                    ),
                    # Above target
                    dict(
                        type="rect",
                        x0=min_date_with_buffer, x1=max_date_with_buffer,
                        y0=GlucoseRanges.TARGET_UPPER, y1=GlucoseRanges.HYPERGLYCEMIA_ALERT,
                        fillcolor="khaki",
                        opacity=0.2,
                        line_width=0
                    ),
                    # Significant hyperglycemia
                    dict(
                        type="rect",
                        x0=min_date_with_buffer, x1=max_date_with_buffer,
                        y0=GlucoseRanges.HYPERGLYCEMIA_ALERT, y1=glucose_df['Value'].max(),
                        fillcolor="mistyrose",
                        opacity=0.2,
                        line_width=0
                    )
                ]
            )

            # Add statistics and recommendations
            st.plotly_chart(fig_glucose)

            # Statistical analysis
            total_readings = len(glucose_df)
            in_range = len(glucose_df[
                (glucose_df['Value'] >= GlucoseRanges.TARGET_LOWER) & 
                (glucose_df['Value'] <= GlucoseRanges.TARGET_UPPER)
            ])
            time_in_range = (in_range / total_readings) * 100 if total_readings > 0 else 0

            st.subheader(t('glycemic_control'))
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    t('time_in_range'),
                    f"{time_in_range:.1f}%",
                    f"{t('target')}: >70%"
                )
            
            with col2:
                hypo_events = len(glucose_df[glucose_df['Value'] < GlucoseRanges.HYPOGLYCEMIA_ALERT])
                st.metric(
                    t('hypoglycemic_events'),
                    hypo_events,
                    f"{t('target')}: {t('minimize')}"
                )
            
            with col3:
                hyper_events = len(glucose_df[glucose_df['Value'] > GlucoseRanges.HYPERGLYCEMIA_ALERT])
                st.metric(
                    t('hyperglycemic_events'),
                    hyper_events,
                    f"{t('target')}: {t('minimize')}"
                )

            # Recommendations based on guidelines
            st.subheader(t('clinical_recommendations'))
            if time_in_range < 70:
                st.warning(t('time_range_warning'))
            
            if hypo_events > 0:
                st.warning(t('hypo_events_warning').format(hypo_events))
            
            if hyper_events > 0:
                st.warning(t('hyper_events_warning').format(hyper_events))

        else:
            st.info(t('no_glucose_data'))
    except Exception as e:
        st.error(t('error_processing').format('glucose', str(e)))

def print_diagram_hemoglobin(data):
    df = pd.DataFrame(data)
    
    if 'Date' not in df.columns:
        st.error(t('no_date_info'))
        return
        
    try:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        if df['Date'].isna().any():
            st.warning(t('dates_parse_error'))
            df = df.dropna(subset=['Date'])
        
        if df.empty:
            st.info(t('no_valid_data'))
            return

        hemoglobin_df = df[df['Title'] == "Results - Hemoglobin in Blood"]
        
        if not hemoglobin_df.empty:
            hemoglobin_df['Value'] = hemoglobin_df['Value'].str.extract(r'(\d+\.?\d*)').astype(float)
            hemoglobin_df['Exact Date'] = hemoglobin_df['Date'].dt.strftime('%B %d, %Y')
            
            def categorize_hba1c(value):
                if value < HbA1cRanges.TARGET_STRICT:
                    return f'{t("below_strict_target")} (< {HbA1cRanges.TARGET_STRICT}%)'
                elif HbA1cRanges.TARGET_STRICT <= value < HbA1cRanges.TARGET_GENERAL:
                    return f'{t("strict_target")} ({HbA1cRanges.TARGET_STRICT}-{HbA1cRanges.TARGET_GENERAL-0.1}%)'
                elif HbA1cRanges.TARGET_GENERAL <= value < HbA1cRanges.TARGET_RELAXED:
                    return f'{t("general_target")} ({HbA1cRanges.TARGET_GENERAL}-{HbA1cRanges.TARGET_RELAXED-0.1}%)'
                else:
                    return f'{t("above_target")} (≥ {HbA1cRanges.TARGET_RELAXED}%)'

            hemoglobin_df['Status'] = hemoglobin_df['Value'].apply(categorize_hba1c)

            color_map = {
                f'{t("below_strict_target")} (< {HbA1cRanges.TARGET_STRICT}%)': "yellow",
                f'{t("strict_target")} ({HbA1cRanges.TARGET_STRICT}-{HbA1cRanges.TARGET_GENERAL-0.1}%)': "green",
                f'{t("general_target")} ({HbA1cRanges.TARGET_GENERAL}-{HbA1cRanges.TARGET_RELAXED-0.1}%)': "yellow",
                f'{t("above_target")} (≥ {HbA1cRanges.TARGET_RELAXED}%)': "red"
            }

            fig_hemoglobin = px.line(
                hemoglobin_df,
                x="Date",
                y="Value",
                color="Status",
                color_discrete_map=color_map,
                markers=True,
                labels={"Value": "HbA1c [%]", "Date": t('date')},
                title=t('hba1c_levels_time'),
                hover_data=["Exact Date"]
            )
            
            fig_hemoglobin.update_traces(marker=dict(size=10), mode='markers')

            min_date = hemoglobin_df['Date'].min()
            max_date = hemoglobin_df['Date'].max()
            buffer_days = pd.Timedelta(days=(max_date - min_date).days * 0.05)
            min_date_with_buffer = min_date - buffer_days
            max_date_with_buffer = max_date + buffer_days

            fig_hemoglobin.update_layout(
                shapes=[
                    # Below strict target
                    dict(
                        type="rect",
                        x0=min_date_with_buffer, x1=max_date_with_buffer,
                        y0=0, y1=HbA1cRanges.TARGET_STRICT,
                        fillcolor="khaki",
                        opacity=0.2,
                        line_width=0
                    ),
                    # Strict target
                    dict(
                        type="rect",
                        x0=min_date_with_buffer, x1=max_date_with_buffer,
                        y0=HbA1cRanges.TARGET_STRICT, y1=HbA1cRanges.TARGET_GENERAL,
                        fillcolor="lightgreen",
                        opacity=0.2,
                        line_width=0
                    ),
                    # General target
                    dict(
                        type="rect",
                        x0=min_date_with_buffer, x1=max_date_with_buffer,
                        y0=HbA1cRanges.TARGET_GENERAL, y1=HbA1cRanges.TARGET_RELAXED,
                        fillcolor="khaki",
                        opacity=0.2,
                        line_width=0
                    ),
                    # Above target
                    dict(
                        type="rect",
                        x0=min_date_with_buffer, x1=max_date_with_buffer,
                        y0=HbA1cRanges.TARGET_RELAXED, y1=hemoglobin_df['Value'].max(),
                        fillcolor="mistyrose",
                        opacity=0.2,
                        line_width=0
                    )
                ]
            )

            st.plotly_chart(fig_hemoglobin)

            # Trend analysis
            st.subheader(t('long_term_analysis'))
            
            # Calculate metrics
            latest_value = hemoglobin_df.iloc[-1]['Value'] if not hemoglobin_df.empty else None
            previous_value = hemoglobin_df.iloc[-2]['Value'] if len(hemoglobin_df) > 1 else None
            
            if latest_value is not None:
                col1, col2 = st.columns(2)
                
                with col1:
                    delta = f"{latest_value - previous_value:+.1f}%" if previous_value is not None else None
                    st.metric(
                        t('latest_hba1c'),
                        f"{latest_value:.1f}%",
                        delta
                    )
                
                with col2:
                    in_target = (HbA1cRanges.TARGET_STRICT <= latest_value <= HbA1cRanges.TARGET_GENERAL)
                    st.metric(
                        t('control_status'),
                        t('on_target') if in_target else t('off_target'),
                        f"{t('target')}: 6.5-7.0%"
                    )

                # Recommendations based on latest value
                st.subheader(t('clinical_recommendations'))
                if latest_value < HbA1cRanges.TARGET_STRICT:
                    st.warning(t('hba1c_below_warning'))
                elif HbA1cRanges.TARGET_STRICT <= latest_value <= HbA1cRanges.TARGET_GENERAL:
                    st.success(t('excellent_control'))
                elif HbA1cRanges.TARGET_GENERAL < latest_value < HbA1cRanges.TARGET_RELAXED:
                    st.warning(t('suboptimal_control'))
                else:
                    st.error(t('inadequate_control'))

                # Trend
                if previous_value is not None:
                    trend = latest_value - previous_value
                    if abs(trend) >= 0.5:  # Significant change in HbA1c
                        if trend > 0:
                            st.warning(t('upward_trend').format(trend))
                        else:
                            st.info(t('improvement').format(trend))

        else:
            st.info(t('no_hba1c_data'))
    except Exception as e:
        st.error(t('error_processing').format('HbA1c', str(e)))

print_diagram_glucose(timeline_data)
print_diagram_hemoglobin(timeline_data)