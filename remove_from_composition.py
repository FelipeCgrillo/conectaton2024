import requests

FHIR_SERVER = "https://ips-challenge.it.hs-heilbronn.de/fhir/"
RESOURCE_ID = "Observation/39bc8ff9-f610-4528-9ebe-f5c8e6f99a00"

# Step 1: Retrieve all Compositions
response = requests.get(f"{FHIR_SERVER}/Composition")
response.raise_for_status()
compositions = response.json().get("entry", [])

for entry in compositions:
    composition = entry["resource"]
    composition_id = composition["id"]

    # Step 2: Check if the Observation is referenced
    updated_sections = []
    has_deleted_observation = False

    for section in composition.get("section", []):
        updated_entries = [
            entry for entry in section.get("entry", [])
            if entry.get("reference") != RESOURCE_ID
        ]
        if len(updated_entries) != len(section.get("entry", [])):
            has_deleted_observation = True
        section["entry"] = updated_entries
        updated_sections.append(section)

    # Step 3: Update Composition only if it referenced the deleted Observation
    if has_deleted_observation:
        composition["section"] = updated_sections
        update_response = requests.put(
            f"{FHIR_SERVER}/Composition/{composition_id}",
            json=composition
        )
        update_response.raise_for_status()
        print(f"Updated Composition {composition_id}")
