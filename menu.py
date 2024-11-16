import streamlit as st


def authenticated_menu():
    # Show a navigation menu for authenticated users
    st.sidebar.page_link("fhir_web.py", label="Search Patient")
    st.sidebar.page_link("pages/timeline.py", label="Timeline")
#    if st.session_state.found_patient in ["admin", "super-admin"]:
#        st.sidebar.page_link("pages/admin.py", label="Manage users")
#        st.sidebar.page_link(
#            "pages/super-admin.py",
#            label="Manage admin access",
#            disabled=st.session_state.role != "super-admin",
#        )


def unauthenticated_menu():
    # Show a navigation menu for unauthenticated users
    st.sidebar.page_link("fhir_web.py", label="Search Patient")


def menu():
    # Determine if a user is logged in or not, then show the correct
    # navigation menu
    if "found_patient" not in st.session_state or st.session_state.found_patient is None:
        unauthenticated_menu()
        return
    authenticated_menu()


def menu_with_redirect():
    # Redirect users to the main page if not logged in, otherwise continue to
    # render the navigation menu
    if "found_patient" not in st.session_state or st.session_state.found_patient is None:
        st.switch_page("fhir_web.py")
    menu()