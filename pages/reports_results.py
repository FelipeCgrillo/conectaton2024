import streamlit as st
from menu import menu_with_redirect
from fhir_web import search_patient_resource, process_observations

menu_with_redirect()

# Observations Section
observations = search_patient_resource(st.session_state.fhir_server_url, st.session_state.patient_id, "Observation")
grouped_obs = process_observations(observations)

for category, obs_data in grouped_obs.items():
    with st.expander(f"📊 {category} Observations", expanded=True):
        st.table(obs_data)

if not grouped_obs:
    st.info("No observations recorded")

# Diagnostic Reports Section
with st.expander("📋 Diagnostic Reports", expanded=True):
    reports = search_patient_resource(st.session_state.fhir_server_url, st.session_state.patient_id, "DiagnosticReport")
    if reports:
        reports_data = []
        for entry in reports:
            report = entry.get('resource', {})
            reports_data.append({
                'Report': report.get('code', {}).get('text', 'N/A'),
                'Date': report.get('effectiveDateTime', 'N/A'),
                'Status': report.get('status', 'N/A'),
                'Category': report.get('category', [{}])[0].get('text', 'N/A')
            })
        st.table(reports_data)
    else:
        st.info("No diagnostic reports recorded")