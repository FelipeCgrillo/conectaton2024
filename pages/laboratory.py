import streamlit as st
from menu import menu_with_redirect
import pandas as pd
import plotly.express as px
import requests
from fhir.resources.composition import Composition

patient_id = st.session_state.get('patient_id', None)
menu_with_redirect()

st.title("Laboratory Resluts")