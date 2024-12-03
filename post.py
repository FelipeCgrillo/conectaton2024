####### Put new observations to UC4-Patient

import requests
import json#
from datetime import datetime
import pytz

### Only works for UC4-Patient !!!
#### Edit the Observation_ID, Encounter and Date, then it puts the new observation #############
observation_id = "UC4-GlucoseLevel2018"
encounter = "UC4-Encounter2018February"
date = "2018-02-14"
number = "4" # Number of the Use Case
blood_sugar = "135"

print(datetime.now())

### Code ###

# URL des FHIR-Servers
FHIR_SERVER_URL = f"https://ips-challenge.it.hs-heilbronn.de/fhir/Observation/{observation_id}"

glucose_data = {
  "resourceType": "Observation",
  "id": observation_id,
  "meta": {
    "versionId": "1",
    "lastUpdated": str(datetime.now(pytz.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+00:00"),
    "source": "#Oyu3CUrSMWdA9qe3",
    "profile": [ "http://hl7.org/fhir/uv/ips/StructureDefinition/Observation-results-uv-ips" ]
  },
  "text": {
    "status": "generated",
    "div": f"<div xmlns=\"http://www.w3.org/1999/xhtml\"><p class=\"res-header-id\"><b>Generated Narrative: Observation {observation_id}</b></p><a name=\"{observation_id}\"> </a><a name=\"hc{observation_id}\"> </a><a name=\"{observation_id}-en-US\"> </a><p><b>status</b>: Final</p><p><b>category</b>: <span title=\"Codes:\">laboratory</span></p><p><b>code</b>: <span title=\"Codes:{'http://loinc.org 14749-6'}\">Glucose [Mass/volume] in Serum or Plasma</span></p><p><b>subject</b>: <a href=\"Patient-UC{number}-Patient.html\">Marta Perez  Female, DoB: 1959-05-15</a></p><p><b>encounter</b>: <a href=\"Encounter-{encounter}.html\">Encounter: status = finished; class = AMB (AMB); period = {date} --&gt; (ongoing)</a></p><p><b>effective</b>: {date}</p><p><b>value</b>: 95 mg/dL<span style=\"background: LightGoldenRodYellow\"> (Details: UCUM  codemg/dL = 'mg/dL')</span></p></div>"
  },
  "status": "final",
  "category": [ {
    "coding": [ {
      "code": "laboratory"
    } ]
  } ],
  "code": {
    "coding": [ {
      "system": "http://loinc.org",
      "code": "14749-6",
      "display": "Glucose [Mass/volume] in Serum or Plasma"
    } ]
  },
  "subject": {
    "reference": f"Patient/UC{number}-Patient"
  },
  "encounter": {
    "reference": f"Encounter/{encounter}"
  },
  "effectiveDateTime": date,
  "valueQuantity": {
    "value": blood_sugar,
    "system": "http://unitsofmeasure.org",
    "code": "mg/dL"
  }
}

# Header (falls erforderlich)
headers = {
    "Content-Type": "application/fhir+json",
    # Falls Authentifizierung notwendig ist, füge den API-Token hinzu
    # "Authorization": "Bearer YOUR_ACCESS_TOKEN"
}

# Prüfen, ob die Observation bereits existiert
response = requests.get(f"{FHIR_SERVER_URL}", headers=headers)

if response.status_code == 200:
    print("Die Observation mit dieser ID existiert bereits.")
    print("Inhalt der existierenden Ressource:", response.json())
elif response.status_code == 404:
    print("Die Observation mit dieser ID existiert nicht. Sie kann erstellt werden.")
else:
    print("Fehler bei der Überprüfung:", response.status_code)
    print("Antwort:", response.text)

# Wenn die Observation nicht existiert, können Sie sie posten
if response.status_code == 404:
    post_response = requests.put(
        f"{FHIR_SERVER_URL}",
        headers=headers,
        data=json.dumps(glucose_data),
    )

    if post_response.status_code == 201:
        print("Observation erfolgreich gepostet!")
        print("Location:", post_response.headers.get("Location"))
    else:
        print("Fehler beim Posten der Daten:", post_response.status_code)
        print("Antwort:", post_response.text)

# Add to composition

reference = {
    "reference": f"Observation/{observation_id}"
}

url = f"https://ips-challenge.it.hs-heilbronn.de/fhir/Composition?patient=UC{number}-Patient"
# Abrufen der Composition
response = requests.get(url)
if response.status_code == 200:
    composition_bundle = response.json()
    
    # Extrahiere die Composition-Ressource
    composition_data = composition_bundle["entry"][0]["resource"]
    
    # Neue Referenz hinzufügen
    new_reference = {"reference": f"Observation/{observation_id}"}
    
    # Füge die neue Referenz zur passenden Section hinzu
    for section in composition_data.get("section", []):
        if section.get("title") == "Results Summary":
            if "entry" not in section:  # Falls "entry" nicht existiert
                section["entry"] = []  # Initialisiere es als leere Liste
            if new_reference not in section["entry"]:
              section["entry"].append(new_reference)  # Referenz hinzufügen
            else:
              print("The reference already exists.")
              break

    # URL für die Aktualisierung der Composition
    update_url = f"https://ips-challenge.it.hs-heilbronn.de/fhir/Composition/{composition_data['id']}"
    headers = {"Content-Type": "application/json"}
    
    # PUT-Request für die aktualisierte Composition
    update_response = requests.put(update_url, headers=headers, json=composition_data)


    if update_response.status_code == 200:
        print("Composition updated successfully.")
    else:
        print(f"Error updating composition: {update_response.status_code}, {update_response.text}")
else:
    print(f"Error fetching composition: {response.status_code}")

# Add Encounter #

encounter_data = {
    "resourceType": "Encounter",
    "id": encounter,
    "meta": {
      "versionId": "1",
      "lastUpdated": str(datetime.now(pytz.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+00:00"),
      "source": "#BqGNsDJtrv7R1JrZ"
    },
    "text": {
      "status": "generated",
      "div": f"<div xmlns=\"http://www.w3.org/1999/xhtml\"><p class=\"res-header-id\"><b>Generated Narrative: Encounter {encounter}</b></p><a name=\"{encounter}\"> </a><a name=\"hc{encounter}\"> </a><a name=\"{encounter}-en-US\"> </a><p><b>status</b>: Finished</p><p><b>class</b>: [not stated] AMB: AMB</p><p><b>subject</b>: <a href=\"Patient-UC{number}-Patient.html\">Marta Perez  Female, DoB: 1959-05-15</a></p><p><b>period</b>: {date} --&gt; (ongoing)</p><p><b>serviceProvider</b>: <a href=\"Organization-UC{number}-HospitalVillarrica.html\">Organization Hospital de Villarrica</a></p></div>"
    },
    "status": "finished",
    "class": {
      "code": "AMB"
    },
    "subject": {
      "reference": f"Patient/UC{number}-Patient"
    },
    "period": {
      "start": date
    },
    "serviceProvider": {
      "reference": "Organization/UC4-HospitalVillarrica"
    }
}

# Header (falls erforderlich)
headers = {
    "Content-Type": "application/fhir+json",
    # Falls Authentifizierung notwendig ist, füge den API-Token hinzu
    # "Authorization": "Bearer YOUR_ACCESS_TOKEN"
}

# Prüfen, ob der Encounter bereits existiert
response = requests.get(f"https://ips-challenge.it.hs-heilbronn.de/fhir/Encounter/{encounter}", headers=headers)

if response.status_code == 200:
    print("Der Encounter mit dieser ID existiert bereits.")
    print("Inhalt der existierenden Ressource:", response.json())
elif response.status_code == 404:
    print("Der Encounter mit dieser ID existiert nicht. Sie kann erstellt werden.")
else:
    print("Fehler bei der Überprüfung:", response.status_code)
    print("Antwort:", response.text)

# Wenn die Observation nicht existiert, können Sie sie posten
if response.status_code == 404:
    post_response = requests.put(
        f"https://ips-challenge.it.hs-heilbronn.de/fhir/Encounter/{encounter}",
        headers=headers,
        data=json.dumps(encounter_data),
    )

    if post_response.status_code == 201:
        print("Observation erfolgreich gepostet!")
        print("Location:", post_response.headers.get("Location"))
    else:
        print("Fehler beim Posten der Daten:", post_response.status_code)
        print("Antwort:", post_response.text)


