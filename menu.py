import streamlit as st

fhir_web = st.Page("views/fhir_web.py", title="Search Patient", default=True)
demographics = st.Page("views/demographics.py", title="Demographics")
clinical = st.Page("views/clinical.py", title="Clinical")
encounters_procedures = st.Page("views/encounters_procedures.py", title="Encounters & Procedures")
reports_results = st.Page("views/reports_results.py", title="Reports & Results")
new_event = st.Page("views/new_event.py", title="New Event")
timeline = st.Page("views/timeline.py", title="Clinical timeline")
laboratory = st.Page("views/laboratory.py", title="Laboratory results")

def update_navigation():
    """Update navigation based on patient selection"""
    # Verificar si hay un paciente seleccionado
    if "patient_id" in st.session_state and st.session_state.patient_id:
        # Si hay un paciente, mostrar todas las páginas
        pages = [fhir_web, demographics, clinical, encounters_procedures, 
                reports_results, new_event, timeline, laboratory]
        
        # Verificar si los datos del laboratorio están disponibles
        if "laboratory_data" not in st.session_state:
            st.session_state.laboratory_data = []
            
        return st.navigation(pages)
    
    # Si no hay paciente, solo mostrar la página de búsqueda
    return st.navigation([fhir_web])

# Set this True if you want to use the history data of Martas composition instead if the current version
st.session_state.history = True

# Actualizar la navegación
pg = update_navigation()

# Ejecutar la página actual
try:
    pg.run()
except Exception as e:
    st.error(f"Error loading page: {str(e)}")
    st.error("Please try selecting a patient first if you haven't done so.")