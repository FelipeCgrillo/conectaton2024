import streamlit as st
from views.fhir_web import search_patient_resource

# Encounters Section
with st.expander("🏥 Encounters", expanded=True):
    encounters = search_patient_resource(st.session_state.fhir_server_url, st.session_state.patient_id, "Encounter")
    if encounters:
        encounters_data = []
        for entry in encounters:
            encounter = entry.get('resource', {})
            
            # Get encounter type from coding
            encounter_type = 'N/A'
            type_codings = encounter.get('type', [{}])[0].get('coding', [])
            for coding in type_codings:
                if coding.get('display'):
                    encounter_type = coding.get('display')
                    break
                elif coding.get('code'):
                    encounter_type = f"Code: {coding.get('code')}"
                    break
            
            # Get encounter class
            class_code = encounter.get('class', {})
            encounter_class = class_code.get('code', 'N/A')
            if class_code.get('display'):
                encounter_class = class_code.get('display')
            
            # Get service type if available
            service_type = 'N/A'
            if 'serviceType' in encounter:
                service_codings = encounter['serviceType'].get('coding', [])
                for coding in service_codings:
                    if coding.get('display'):
                        service_type = coding.get('display')
                        break
            
            # Get service provider - handle both reference and display
            service_provider = 'N/A'
            provider_info = encounter.get('serviceProvider', {})
            if 'display' in provider_info:
                service_provider = provider_info['display']
            elif 'reference' in provider_info:
                service_provider = provider_info['reference'].split('/')[-1]
            
            # Get period start and end dates
            period = encounter.get('period', {})
            start_date = period.get('start', 'N/A')
            end_date = period.get('end', 'N/A')
            
            encounters_data.append({
                'Type': encounter_type,
                'Class': encounter_class,
                'Service': service_type,
                'Provider': service_provider,
                'Start Date': start_date,
                'End Date': end_date,
                'Status': encounter.get('status', 'N/A')
            })
        
        # Sort encounters by start date
        encounters_data.sort(key=lambda x: x['Start Date'] if x['Start Date'] != 'N/A' else '', reverse=True)
        st.table(encounters_data)
        
        # Display total count
        st.markdown(f"*Total encounters: {len(encounters_data)}*")
    else:
        st.info("No encounters recorded")

# Procedures Section
with st.expander("⚕️ Procedures", expanded=True):
    procedures = search_patient_resource(st.session_state.fhir_server_url, st.session_state.patient_id, "Procedure")
    if procedures:
        procedures_data = []
        for entry in procedures:
            procedure = entry.get('resource', {})
            
            # Get performed period if available
            performed_period = procedure.get('performedPeriod', {})
            start_date = performed_period.get('start', procedure.get('performedDateTime', 'N/A'))
            end_date = performed_period.get('end', 'N/A')
            
            procedures_data.append({
                'Procedure': procedure.get('code', {}).get('text', 'N/A'),
                'Start Date': start_date,
                'End Date': end_date,
                'Status': procedure.get('status', 'N/A')
            })
            
        # Sort procedures by start date
        procedures_data.sort(key=lambda x: x['Start Date'] if x['Start Date'] != 'N/A' else '', reverse=True)
        st.table(procedures_data)
        
        # Display total count
        st.markdown(f"*Total procedures: {len(procedures_data)}*")
    else:
        st.info("No procedures recorded")