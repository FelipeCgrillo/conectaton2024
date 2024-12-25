import streamlit as st

fhir_web = st.Page("views/fhir_web.py", title="Search Patient", default=True)
demographics = st.Page("views/demographics.py", title="Demographics")
timeline = st.Page("views/timeline.py", title="Clinical timeline")
clinical = st.Page("views/clinical.py", title="Clinical")
encounters_procedures = st.Page("views/encounters_procedures.py", title="Encounters & Procedures")
reports_results = st.Page("views/reports_results.py", title="Reports & Results")
new_event = st.Page("views/new_event.py", title="New Event")
laboratory = st.Page("views/laboratory.py", title="Laboratory results")

def update_navigation():
    if "patient_id" in st.session_state and st.session_state.patient_id:
        return st.navigation([fhir_web, demographics, clinical, encounters_procedures, reports_results, new_event, timeline, laboratory])
    return st.navigation([fhir_web])

# Set this True if you want to use the history data of Martas composition instead if the current version
st.session_state.history = False

pg = update_navigation()
pg.run()