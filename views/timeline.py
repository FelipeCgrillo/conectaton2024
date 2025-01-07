import streamlit as st
import pandas as pd
import plotly.express as px

patient_id = st.session_state.get('patient_id', None)
timeline_data = st.session_state.get('laboratory_data', None)

low_glucose = 60 # mg/dL
mid_glucose = 100 # mg/dL
high_glucose = 140 # mg/dL
mid_hemo = 6.5 # percent = 7,75 mmol/l = 47 mmol/mol
high_hemo = 8.5 # percent = 11 mmol/l = 69 mmol/mol

# Hilfsfunktion zur Erstellung von Name-Value-Paaren für eine beliebige Anzahl
def generate_custom_data(row):
    # Beginne mit den Basisfeldern
    hover_lines = [f"Exact Date: {row['Exact Date']}" if 'Exact Date' in row and row['Exact Date'] else ""]
    if 'Name' in row and pd.notna(row['Name']):
        hover_lines.append(f"Name: {row['Name']}")
    if 'Value' in row and pd.notna(row['Value']):
        hover_lines.append(f"Value: {row['Value']}")
    # Dynamisch Name-Value-Paare hinzufügen
    for i in range(5):  # Passe die maximale Anzahl von Paaren an
        name_key = f"Name {i}"
        value_key = f"Value {i}"
        name = row.get(name_key, None)
        value = row.get(value_key, None)
        # Füge das Paar nur hinzu, wenn beide Werte existieren und nicht NaN sind
        if pd.notna(name) and pd.notna(value):
            hover_lines.append(f"{name}: {value}")
    # Entferne leere Zeilen und erstelle einen zusammenhängenden String
    return "<br>".join(hover_lines) if hover_lines else None

def print_timeline(data):
    # Verify the user's role
    if not st.session_state.patient_id:
        st.warning("No patient found.")
        st.stop()

    st.title("Clinical Timeline")

    # Convert data into a DataFrame
    df = pd.DataFrame(data)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # Separate rows with invalid or missing dates
    no_date_df = df[df['Date'].isna()]
    valid_date_df = df[df['Date'].notna()]

    # Assign default date to rows with missing dates (for timeline plotting)
    valid_date_df['Date'] = valid_date_df['Date'].fillna(pd.Timestamp("1900-01-01"))

    # Add default color and symbol
    valid_date_df['Color'] = "Neutral"
    valid_date_df['Symbol'] = "circle"

    # Style map for glucose and hemoglobin levels
    style_map = {
        f'Abnormal Glucose (< {low_glucose} mg/dL)': {'color': 'red', 'symbol': 'star'},
        f'Normal Glucose ({low_glucose}-{mid_glucose-1} mg/dL)': {'color': 'green', 'symbol': 'square'},
        f'Marginal Glucose ({mid_glucose}-{high_glucose-1} mg/dL)': {'color': 'orange', 'symbol': 'triangle-up'},
        f'Abnormal Glucose (>= {high_glucose} mg/dL)': {'color': 'red', 'symbol': 'star'},
        f'Normal Hemoglobin (< {mid_hemo} %)': {'color': 'green', 'symbol': 'square'},
        f'Marginal Hemoglobin ({mid_hemo}-{high_hemo-1} %)': {'color': 'orange', 'symbol': 'triangle-up'},
        f'Abnormal Hemoglobin (>= {high_hemo} %)': {'color': 'red', 'symbol': 'star'},
        f'Neutral': {'color': 'blue', 'symbol': 'circle'}
    }

    # Reverse map for legend labels
    color_symbol_map = {f"{val['color']}, {val['symbol']}": key for key, val in style_map.items()}

    # Apply glucose styles
    if 'Results - Glucose Level' in valid_date_df['Title'].values:
        glucose_df_timeline = valid_date_df[valid_date_df['Title'] == "Results - Glucose Level"]
        glucose_df_timeline['Value'] = glucose_df_timeline['Value'].str.extract(r'(\d+\.?\d*)').astype(float)
        #glucose_df_timeline['Status'] = glucose_df_timeline['Value'].apply(
        #    lambda x: f'Abnormal Glucose (< {low_glucose} mg/dL)' if x < low_glucose else (
        #        f'Normal Glucose ({low_glucose}-{mid_glucose-1} mg/dL)' if x < mid_glucose else (
        #            f'Marginal Glucose ({mid_glucose}-{high_glucose-1} mg/dL)' if x < high_glucose else 
        #            f'Abnormal Glucose (>= {high_glucose} mg/dL)'
        #        )
        #    )
        #)
        #glucose_df_timeline['Color'] = glucose_df_timeline['Status'].map(lambda x: style_map[x]['color']).fillna('blue')
        #glucose_df_timeline['Symbol'] = glucose_df_timeline['Status'].map(lambda x: style_map[x]['symbol']).fillna('circle')
        #valid_date_df.loc[glucose_df_timeline.index, ['Color', 'Symbol']] = glucose_df_timeline[['Color', 'Symbol']]

    # Apply hemoglobin styles
    if 'Results - Ac1-Test' in valid_date_df['Title'].values:
        hemoglobin_df_timeline = valid_date_df[valid_date_df['Title'] == "Results - Ac1-Test"]
        hemoglobin_df_timeline['Value'] = hemoglobin_df_timeline['Value'].str.extract(r'(\d+\.?\d*)').astype(float)
        #hemoglobin_df_timeline['Status'] = hemoglobin_df_timeline['Value'].apply(
        #    lambda x: f'Normal Hemoglobin (< {mid_hemo} %)' if x < mid_hemo else (
        #        f'Marginal Hemoglobin ({mid_hemo}-{high_hemo-1} %)' if x < high_hemo else 
        #        f'Abnormal Hemoglobin (>= {high_hemo} %)'
        #    )
        #)
        #hemoglobin_df_timeline['Color'] = hemoglobin_df_timeline['Status'].map(lambda x: style_map[x]['color']).fillna('blue')
        #hemoglobin_df_timeline['Symbol'] = hemoglobin_df_timeline['Status'].map(lambda x: style_map[x]['symbol']).fillna('circle')
        #valid_date_df.loc[hemoglobin_df_timeline.index, ['Color', 'Symbol']] = hemoglobin_df_timeline[['Color', 'Symbol']]

    # Sidebar filters
    st.sidebar.header("Filter Options")
    start_date = st.sidebar.date_input("Start Date", value=valid_date_df['Date'].min().date())
    end_date = st.sidebar.date_input("End Date", value=valid_date_df['Date'].max().date())
    if start_date > end_date:
        st.sidebar.error("Start Date must be earlier than End Date.")
        st.stop()
    resource_types = valid_date_df['Title'].unique()
    selected_resources = st.sidebar.multiselect(
        "Filter by Resource Type", options=resource_types, default=resource_types
    )

    # Filter DataFrame
    filtered_df = valid_date_df[
        (valid_date_df['Date'] >= pd.Timestamp(start_date)) &
        (valid_date_df['Date'] <= pd.Timestamp(end_date)) &
        (valid_date_df['Title'].isin(selected_resources))
    ]
    filtered_df['hover_info'] = filtered_df.apply(generate_custom_data, axis=1)

    # Plot timeline
    if not filtered_df.empty:
        fig = px.scatter(
            filtered_df,
            x="Date",
            y="Title",
            color="Color",
            symbol="Symbol",
            #color_discrete_map={val['color']: val['color'] for val in style_map.values()},
            #symbol_map={val['symbol']: val['symbol'] for val in style_map.values()},
            labels={"Date": "Date", "Title": "Resource Type", "Color": "Legend"},
            custom_data=["hover_info"],
            hover_data={"Symbol": False}
        )
        fig.update_traces(marker=dict(size=12, opacity=0.7), hovertemplate="%{customdata[0]}")
        # Update legend with descriptions
        #fig.for_each_trace(lambda t: t.update(name=color_symbol_map.get(f"{t.marker.color}, {t.marker.symbol}", t.name)))
        fig.update_layout(showlegend=False, clickmode="event+select", legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig)
    else:
        st.warning("No data available for the selected filters.")

    # Display table for entries without a valid date
    if not no_date_df.empty:
        st.subheader("Entries Without a Valid Date")
        # Remove columns where all values are NaN or empty
        no_date_df_cleaned = no_date_df.dropna(axis=1, how='all')
        st.table(no_date_df_cleaned)

print_timeline(timeline_data)