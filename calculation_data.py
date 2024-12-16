import streamlit as st
import requests

def search_for_clinical_data(request):
    """
    This method gets the json of the clinical data
        :param request: reference to e.g. observation
        :return: clinical data as json
    """
    try:
        url = f"https://ips-challenge.it.hs-heilbronn.de/fhir/{request}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()

        return []
    except requests.RequestException as e:
        st.error(f"Error fetching data: {e}")
        return []

def fetch_fhir_data(url):
    """
    Get the data from a specific URLS
    :param url: url of fhir data
    :return: json
    """
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error while reading the data: {response.status_code}")
        return None

# Get the data of results summary for the timeline
def extract_timeline_data_observation(timeline_data, clinical_data):
    """
    extract the information of an observation from the clinical data
    :param timeline_data: json to save the specific data and later print the timelines
    :param clinical_data: extended data of the patient
    """
    # extract date, name and loinc code
    date = clinical_data["effectiveDateTime"]
    observation_name = clinical_data["code"]["coding"][0]["display"]
    loinc = clinical_data["code"]["coding"][0]["code"]
    symbol = ""

    # check if the observation is a glucose or hemoglobin level
    if loinc == "14749-6": # loinc code for glucose level
        symbol = " - Glucose Level"
    elif loinc == "4548-4": # loinc code for hemoglobin level
        symbol = " - Hemoglobin in Blood"

    # try to get an value of this observation if available
    value = ""
    try:
        value = str(clinical_data["valueQuantity"]["value"]) + " " + clinical_data["valueQuantity"]["code"]
    except KeyError:
        value = "No value"

    # add data to the timeline
    timeline_data.append({
        "Title": "Results" + symbol,
        "Name": observation_name,
        "Date": date,
        "Value": value
    })

# Get the data of medication summary for the timeline
def extract_timeline_data_encounter(timeline_data, clinical_data):
    """
    extract the information of an encounter from the clinical data
    :param timeline_data: json to save the specific data and later print the timelines
    :param clinical_data: extended data of the patient
    """
    date = ""
    if clinical_data["resourceType"] == "MedicationRequest":
        # extract date
        date = clinical_data["authoredOn"]
        title ="Medication Requests"
    if clinical_data["resourceType"] == "MedicationStatement":
        # extract date
        date = clinical_data["effectiveDateTime"]
        title ="Medication Statements"
    if clinical_data["resourceType"] == "MedicationAdministration":
        # extract date
        date = clinical_data["effectiveDateTime"]
        title ="Medication Adminstrations"
    
    if date != "":
        concept = clinical_data["medicationCodeableConcept"]
        encounter_name = concept["coding"][0]["display"]

        # add data to the timeline
        timeline_data.append({
            "Title": title,
            "Name": encounter_name,
            "Date": date
        })

    if clinical_data["resourceType"] == "MedicationDispense":
        # extract date
        date = clinical_data["whenPrepared"]
        concept = clinical_data["medicationCodeableConcept"]
        encounter_name = concept["coding"][0]["display"]

        # add data to the timeline
        timeline_data.append({
            "Title": "Medication Dispenses",
            "Name": encounter_name,
            "Date": date
        })

# Get the data of problems summary for the timeline
def extract_timeline_data_condition(timeline_data, clinical_data):
    """
    extract the information of an condition from the clinical data
    :param timeline_data: json to save the specific data and later print the timelines
    :param clinical_data: extended data of the patient
    """
    # extract date
    date = clinical_data["onsetDateTime"]
    code = clinical_data["code"]
    condition_name= code["coding"][0]["display"]
    
    # add data to the timeline
    timeline_data.append({
        "Title": "Problems",
        "Name": condition_name,
        "Date": date
    })

# Get the data of allergies summary for the timeline
def extract_timeline_data_intolerance(timeline_data, clinical_data):
    """
    extract the information of an intolerance from the clinical data
    :param timeline_data: json to save the specific data and later print the timelines
    :param clinical_data: extended data of the patient
    """
    # extract date
    date = clinical_data["onsetDateTime"]
    code = clinical_data["code"]
    intolerance_name= code["coding"][0]["display"]

    # add data to the timeline
    timeline_data.append({
        "Title": "Allergy Intolerance",
        "Name": intolerance_name,
        "Date": date,
        "Reaction": clinical_data["reaction"][0]["manifestation"][0]["coding"][0]["display"],
        "Criticality": clinical_data["criticality"]
    })

# Get the data of vital signs summary for the timeline
def extract_timeline_data_vital(timeline_data, clinical_data):
    """
    extract the information of vital data from the clinical data
    :param timeline_data: json to save the specific data and later print the timelines
    :param clinical_data: extended data of the patient
    """
    # extract date
    date = clinical_data["effectiveDateTime"]
    code = clinical_data["code"]
    vital_name= code["coding"][0]["display"]

    value = ""
    try:
        value = str(clinical_data["valueQuantity"]["value"]) + " " + clinical_data["valueQuantity"]["code"]
    except KeyError:
        value = "No Value"

    # if there is no directly linked value, try to extract a list of values (component)
    if value == "No Value":
        try:
            # initialize a dictionary for vital data
            vital_data = {"Title": "Vital Signs", "Date": date}
            vital_data["Name"] = vital_name
            number = 1
            # Iteriere durch die Komponenten in clinical_data
            for component in clinical_data["component"]:
                # add name and value for every component to the dict
                vital_data[f"Name {number}"] = str(component["code"]["coding"][0]["display"])
                vital_data[f"Value {number}"] = (
                    str(component["valueQuantity"]["value"]) + " " + component["valueQuantity"]["code"]
                )
                number += 1
            timeline_data.append(vital_data)
        except KeyError:
            try:
                vital_data = {"Title": "Vital Signs", "Date": date}
                vital_data[f"Name {number}"] = clinical_data["code"]["coding"][0]["display"]
                vital_data["Value"] = clinical_data["valueString"]
                timeline_data.append(vital_data)
            except KeyError:
                value = "No Value"
    else:
        # add standard data to the timeline
        timeline_data.append({
            "Title": "Vital Signs",
            "Name": vital_name,
            "Date": date,
            "Value": value
        })

# Get the data of social history summary for the timeline
def extract_timeline_data_history(timeline_data, clinical_data):
    """
    extract the information of the social history from the clinical data
    :param timeline_data: json to save the specific data and later print the timelines
    :param clinical_data: extended data of the patient
    """
    # extract date
    date = clinical_data["effectiveDateTime"]
    code = clinical_data["code"]
    history_name = "Observation - Other"

    # add value, note and method to the data for information of the data history
    value = ""
    try:
        value = clinical_data["valueCodeableConcept"]["coding"][0]["display"]
    except KeyError:
        value = "No value"
    note = ""
    try:
        note = clinical_data["note"][0]["text"]
    except KeyError:
        note = "No Note"
    method = ""
    try:
        method = clinical_data["method"]["coding"][0]["display"]
    except KeyError:
        method = "No Method"

    # add data to the timeline
    timeline_data.append({
        "Title": "Social History",
        "Name": history_name,
        "Date": date,
        "Value": value,
        "Note": note,
        "Method": method
    })