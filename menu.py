
import streamlit as st

def authenticated_menu():
    # Show a navigation menu for authenticated users
    st.sidebar.page_link("fhir_web.py", label="Search Patient")
    st.sidebar.page_link("pages/demographics.py", label="Demographics")
    st.sidebar.page_link("pages/clinical.py", label="Clinical")
    st.sidebar.page_link("pages/encounters_procedures.py", label="Encounters & Procedures")
    st.sidebar.page_link("pages/reports_results.py", label="Reports & Results")
    st.sidebar.page_link("pages/new_event.py", label="New Event")
    st.sidebar.page_link("pages/timeline.py", label="Clinical Timeline")
#    if st.session_state.patient_id in ["admin", "super-admin"]:
#        st.sidebar.page_link("pages/admin.py", label="Manage users")
#        st.sidebar.page_link(
#            "pages/super-admin.py",
#            label="Manage admin access",
#            disabled=st.sesion_state.role != "super-admin",
#        )


def unauthenticated_menu():
    # Show a navigation menu for unauthenticated users
    st.sidebar.page_link("fhir_web.py", label="Search Patient")


def menu():
    # Determine if a user is logged in or not, then show the correct
    # navigation menu
    if "patient_id" not in st.session_state or st.session_state.patient_id is None:
        unauthenticated_menu()
    else:
        authenticated_menu()


def menu_with_redirect():
    # Redirect users to the main page if not logged in, otherwise continue to
    # render the navigation menu
    if "patient_id" not in st.session_state or st.session_state.patient_id is None:
        st.switch_page("fhir_web.py")
    menu()

"""
import streamlit as st

fhir_web = st.Page("fhir_web.py", title="Search patient")
demographics = st.Page("pages/demographics.py", title="Demographics")
clinical = st.Page("pages/clinical.py", title="Clinical")
encounters_procedures = st.Page("pages/encounters_procedures.py", title="Encounters & Procedures")
reports_results = st.Page("pages/reports_results.py", title="Reports & Results")
new_event = st.Page("pages/new_event.py", title="New Event")
timeline = st.Page("pages/timeline.py", title="Clinical timeline")

def authenticated_menu():
    # Show a navigation menu for authenticated users
    st.navigation([fhir_web, demographics, clinical, encounters_procedures, reports_results, new_event, timeline])


def unauthenticated_menu():
    # Show a navigation menu for unauthenticated users
    st.navigation([fhir_web])


def menu():
    # Determine if a user is logged in or not, then show the correct
    # navigation menu
    if "patient_id" not in st.session_state or st.session_state.patient_id is None:
        unauthenticated_menu()
    else:
        authenticated_menu()


def menu_with_redirect():
    # Redirect users to the main page if not logged in, otherwise continue to
    # render the navigation menu
    if "patient_id" not in st.session_state or st.session_state.patient_id is None:
        st.switch_page("fhir_web.py")
    menu()
"""