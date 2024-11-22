import streamlit as st
from menu import menu_with_redirect
from fhir_web import create_clinical_event, create_condition, create_observation, create_diagnostic_report, validate

menu_with_redirect()

st.markdown("### 📝 Register New Clinical Event")


ENCOUNTER_TYPES = {
    "AMB": "Ambulatory",
    "EMER": "Emergency",
    "HH": "Home Health",
    "IMP": "Inpatient",
    "ACUTE": "Acute Care",
    "NONAC": "Non-Acute",
    "OBSENC": "Observation Encounter",
    "PRENC": "Pre-Admission",
    "SS": "Short Stay"
}

event_type = st.radio(
    "Event Type",
    ["Encounter", "Condition", "Observation", "Diagnostic Report"]
)

with st.form("new_clinical_event"):
    if event_type == "Encounter":
        encounter_type = st.selectbox(
            "Encounter Type",
            options=list(ENCOUNTER_TYPES.keys()),
            format_func=lambda x: f"{x} - {ENCOUNTER_TYPES[x]}"
        )
        
        description = st.text_area(
            "Event Description",
            placeholder="Describe the clinical event..."
        )
        
        reason = st.text_input(
            "Reason",
            placeholder="Reason for encounter"
        )
        
        date = st.date_input(
            "Event Date"
        )
        
    elif event_type == "Condition":
        condition = st.text_input("Condition", placeholder="e.g., Diabetes decompensation")
        status = st.selectbox("Clinical Status", ["active", "recurrence", "resolved"])
        onset_date = st.date_input("Onset Date")
        
    elif event_type == "Observation":
        obs_type = st.text_input("Observation Type", placeholder="e.g., Blood Glucose")
        value = st.number_input("Value")
        unit = st.text_input("Unit", placeholder="e.g., mg/dL")
        obs_date = st.date_input("Observation Date")
        
    elif event_type == "Diagnostic Report":
        report_type = st.text_input("Report Type", placeholder="e.g., Lab Results")
        conclusion = st.text_area("Conclusion")
        report_date = st.date_input("Report Date")

    
    submitted = st.form_submit_button("Register Event")
    
    if submitted:
        success = False
        if event_type == "Encounter":
            success = create_clinical_event(st.session_state.fhir_server_url, st.session_state.patient_id, {
                "encounter_type": encounter_type,
                "description": description,
                "reason": reason,
                "date": date.isoformat()
            })
        elif event_type == "Condition":
            success = create_condition(st.session_state.fhir_server_url, st.session_state.patient_id, {
                "condition": condition,
                "status": status,
                "onset_date": onset_date.isoformat()
            })
        elif event_type == "Observation":
            success = create_observation(st.session_state.fhir_server_url, st.session_state.patient_id, {
                "type": obs_type,
                "value": value,
                "unit": unit,
                "date": obs_date.isoformat()
            })
        elif event_type == "Diagnostic Report":
            success = create_diagnostic_report(st.session_state.fhir_server_url, st.session_state.patient_id, {
                "type": report_type,
                "conclusion": conclusion,
                "date": report_date.isoformat()
            })
        
        if success:
            st.success(f"{event_type} registered successfully")
            #try:
            #    st.experimental_rerun()
            #except:
            #    st.rerun()
        else:
            st.error(f"Error registering {event_type}")