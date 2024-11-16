import streamlit as st
from menu import menu_with_redirect
import pandas as pd
import plotly.express as px

menu_with_redirect()
# test
# Verify the user's role
if not st.session_state.found_patient:
    st.warning("No patient found.")
    st.stop()

st.title("Clinical timeline")

# Sample FHIR resource data
data = [
    {"resource_type": "Condition", "date": "2023-01-10", "details": "Hypertension"},
    {"resource_type": "Immunization", "date": "2023-03-05", "details": "COVID-19 Vaccine"},
    {"resource_type": "MedicationRequest", "date": "2023-06-15", "details": "Atorvastatin 20mg"},
    {"resource_type": "Condition", "date": "2023-09-10", "details": "Diabetes Type 2"},
    {"resource_type": "MedicationRequest", "date": "2023-10-12", "details": "Metformin 500mg"},
]

# Convert data into a DataFrame
df = pd.DataFrame(data)
df['date'] = pd.to_datetime(df['date'])

# Initialize session state for selected data if it doesn't exist
if "selected_data_index" not in st.session_state:
    st.session_state.selected_data_index = None

# Filter selection
resource_types = df['resource_type'].unique()
selected_resources = st.multiselect("Filter by Resource Type", options=resource_types, default=resource_types)

# Filter the DataFrame based on selection
filtered_df = df[df['resource_type'].isin(selected_resources)]

# Create the Plotly timeline chart
fig = px.scatter(
    filtered_df,
    x="date",
    y="resource_type",
    text="resource_type",
    title="FHIR Resource Timeline",
    labels={"date": "Date", "resource_type": "Resource Type"},
    hover_data=["details"]
)

# Update layout to make it interactive
fig.update_traces(marker=dict(size=12, opacity=0.7), mode="markers+text", textposition="top center")
fig.update_layout(clickmode="event+select")

# Display the chart in Streamlit
event = st.plotly_chart(fig, on_select="rerun")

st.write(event)