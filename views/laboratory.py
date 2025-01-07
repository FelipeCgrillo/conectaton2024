import streamlit as st
import pandas as pd
import plotly.express as px

# Educational and descriptive section
st.markdown("""
### Analysis based on ADA/EASD Guidelines 2023-2024

This analysis is based on the current guidelines of the **American Diabetes Association (ADA)** and the **European Association for the Study of Diabetes (EASD)**. 
These guidelines provide international standards for diabetes diagnosis and monitoring, including:

- Updated diagnostic criteria for diabetes and prediabetes
- Personalized glycemic control targets
- Recommendations for glucose and HbA1c monitoring
- Prevention and management strategies

#### 🎯 Reference Values:

**Fasting Glucose:**
- Normal: 70-99 mg/dL
- Prediabetes: 100-125 mg/dL
- Diabetes: ≥ 126 mg/dL
- Hypoglycemia: < 70 mg/dL

**Glycated Hemoglobin (HbA1c):**
- Normal: < 5.7%
- Prediabetes: 5.7-6.4%
- Diabetes: ≥ 6.5%
- Target control in diabetes: < 8.0%

---
""")

def get_glucose_advice(value):
    if value < low_glucose:
        return "⚠️ **Caution**: Low glucose level. Consult your doctor to adjust your treatment and prevent hypoglycemic episodes."
    elif low_glucose <= value < mid_glucose:
        return "✅ **Excellent**: Your glucose levels are in the normal range."
    elif mid_glucose <= value < high_glucose:
        return "⚠️ **Attention**: Your levels indicate prediabetes. Consult your doctor about prevention strategies and lifestyle changes."
    else:
        return "🚨 **Important**: Your levels indicate diabetes. It is essential to maintain regular follow-up with your medical team."

def get_hba1c_advice(value):
    if value < normal_hemo:
        return "✅ **Excellent**: Your long-term glycemic control is in the normal range."
    elif normal_hemo <= value < mid_hemo:
        return "⚠️ **Attention**: Your levels indicate prediabetes. It's important to implement lifestyle changes and consult with your doctor."
    elif mid_hemo <= value < high_hemo:
        return "🔍 **Follow-up**: Your levels indicate diabetes. Maintain regular monitoring and follow your medical team's recommendations."
    else:
        return "🚨 **Important**: Your glycemic control needs attention. Consult your doctor to adjust your treatment plan."

# Check if a patient is selected
if "patient_id" not in st.session_state or not st.session_state.patient_id:
    st.warning("Please select a patient first.")
    st.stop()

# Check if laboratory data is available
timeline_data = st.session_state.get('laboratory_data', None)
if timeline_data is None or len(timeline_data) == 0:
    st.warning("No laboratory data available for this patient.")
    st.stop()

# Reference values according to ADA/EASD
low_glucose = 70  # mg/dL - normal lower limit
mid_glucose = 100  # mg/dL - prediabetes onset
high_glucose = 126  # mg/dL - diabetes diagnosis

# HbA1c values according to ADA/EASD
normal_hemo = 5.7  # % - normal upper limit
mid_hemo = 6.5  # % - diabetes diagnosis
high_hemo = 8.0  # % - poor control

st.title("Laboratory Results")

def print_diagram_glucose(data):
    df = pd.DataFrame(data)
    
    if 'Date' not in df.columns:
        st.error("No date information found in the data")
        return
        
    try:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        if df['Date'].isna().any():
            st.warning("Some dates could not be parsed correctly")
            df = df.dropna(subset=['Date'])
        
        if df.empty:
            st.info("No valid data available after date processing")
            return

        glucose_df = df[df['Title'] == "Results - Glucose Level"]

        if not glucose_df.empty:
            glucose_df['Color'] = "Neutral"
            glucose_df['Symbol'] = "circle"
            glucose_df.loc[:, 'Exact Date'] = glucose_df['Date'].dt.strftime('%B %d, %Y')
            glucose_df['Value'] = glucose_df['Value'].str.extract(r'(\d+\.?\d*)').astype(float)
            glucose_df['Status'] = glucose_df['Value'].apply(
                lambda x: f'Hypoglycemia (< {low_glucose} mg/dL)' if x < low_glucose else (
                    f'Normal ({low_glucose}-{mid_glucose-1} mg/dL)' if low_glucose <= x < mid_glucose else (
                    f'Prediabetes ({mid_glucose}-{high_glucose-1} mg/dL)' if mid_glucose <= x < high_glucose else 
                    f'Diabetes (≥ {high_glucose} mg/dL)')
            ))

            fig_glucose = px.line(
                glucose_df,
                x="Date",
                y="Value",
                color_discrete_sequence=['#000080'],
                markers=True,
                labels={"Value": "Fasting Glucose [mg/dL]", "Date": "Date"},
                title="Glucose Levels Over Time",
                hover_data=["Exact Date", "Status"]
            )
            
            fig_glucose.update_traces(marker=dict(size=10))
            fig_glucose.update_traces(mode='markers')

            min_date = glucose_df['Date'].min()
            max_date = glucose_df['Date'].max()
            buffer_days = (max_date - min_date) * 0.05
            min_date_with_buffer = min_date - buffer_days
            max_date_with_buffer = max_date + buffer_days

            fig_glucose.update_layout(showlegend=True)
            st.plotly_chart(fig_glucose)
            
            # Show advice based on the latest value
            latest_value = glucose_df['Value'].iloc[-1]
            st.markdown("### Recommendation")
            st.markdown(get_glucose_advice(latest_value))
        else:
            st.info("No glucose data available.")
    except Exception as e:
        st.error(f"Error processing glucose data: {e}")

def print_diagram_hemoglobin(data):
    df = pd.DataFrame(data)
    
    if 'Date' not in df.columns:
        st.error("No date information found in the data")
        return
        
    try:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        if df['Date'].isna().any():
            st.warning("Some dates could not be parsed correctly")
            df = df.dropna(subset=['Date'])
        
        if df.empty:
            st.info("No valid data available after date processing")
            return

        hemoglobin_df = df[df['Title'] == "Results - Ac1-Test"]
        
        if not hemoglobin_df.empty:
            hemoglobin_df['Value'] = hemoglobin_df['Value'].str.extract(r'(\d+\.?\d*)').astype(float)
            hemoglobin_df['Exact Date'] = hemoglobin_df['Date'].dt.strftime('%B %d, %Y')
            
            def categorize_hba1c(value):
                if value < normal_hemo:
                    return f'Normal (< {normal_hemo}%)'
                elif normal_hemo <= value < mid_hemo:
                    return f'Prediabetes ({normal_hemo}-{mid_hemo-0.1}%)'
                elif mid_hemo <= value < high_hemo:
                    return f'Controlled Diabetes ({mid_hemo}-{high_hemo-0.1}%)'
                else:
                    return f'Uncontrolled Diabetes (≥ {high_hemo}%)'

            hemoglobin_df['Status'] = hemoglobin_df['Value'].apply(categorize_hba1c)

            fig_hemoglobin = px.line(
                hemoglobin_df,
                x="Date",
                y="Value",
                color_discrete_sequence=['#000080'],
                markers=True,
                labels={"Value": "HbA1c [%]", "Date": "Date"},
                title="Glycated Hemoglobin (HbA1c) Over Time",
                hover_data=["Exact Date", "Status"]
            )
            
            fig_hemoglobin.update_traces(marker=dict(size=10), mode='markers')

            min_date = hemoglobin_df['Date'].min()
            max_date = hemoglobin_df['Date'].max()
            buffer_days = pd.Timedelta(days=(max_date - min_date).days * 0.05)
            min_date_with_buffer = min_date - buffer_days
            max_date_with_buffer = max_date + buffer_days

            st.plotly_chart(fig_hemoglobin)
            
            # Show advice based on the latest value
            latest_value = hemoglobin_df['Value'].iloc[-1]
            st.markdown("### Recommendation")
            st.markdown(get_hba1c_advice(latest_value))
        else:
            st.info("No HbA1c data available.")
    except Exception as e:
        st.error(f"Error processing HbA1c data: {e}")

print_diagram_glucose(timeline_data)
print_diagram_hemoglobin(timeline_data)