import streamlit as st
import requests
from menu import menu_with_redirect
from fhir_web import search_patient

import folium
from streamlit_folium import folium_static

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

def get_location_coordinates(address_str):
    """
    Get coordinates for an address using Nominatim geocoder.
    
    Args:
        address_str (str): Address string to geocode
    
    Returns:
        tuple: (latitude, longitude) or None if geocoding fails
    """
    try:
        import ssl
        import certifi
        
        ctx = ssl.create_default_context(cafile=certifi.where())
        geolocator = Nominatim(
            user_agent="patient_search_portal",
            ssl_context=ctx
        )
        
        location = geolocator.geocode(address_str, timeout=10)
        if location:
            return location.latitude, location.longitude
        return None
    except (GeocoderTimedOut, GeocoderUnavailable) as e:
        st.warning(f"Geocoding error: {e}")
        return None
    except Exception as e:
        st.warning(f"Error getting coordinates: {e}")
        return None

menu_with_redirect()

st.title("Demographics")

patient_data = search_patient(st.session_state.fhir_server_url,st.session_state.patient_id)

st.markdown("### 👤 Basic Info")
name = patient_data.get('name', [{}])[0].get('given', ['N/A'])[0] + " " + \
        patient_data.get('name', [{}])[0].get('family', 'N/A')
gender = patient_data.get('gender', 'N/A')
birthdate = patient_data.get('birthDate', 'N/A')

st.markdown(f"**Name:** {name}")
st.markdown(f"**Gender:** {gender}")
st.markdown(f"**Birthdate:** {birthdate}")

# Add some spacing
st.markdown("---")

# Contact Information Section
st.markdown("### 📞 Contact Info")
telecom = patient_data.get('telecom', [])
for contact in telecom:
    system = contact.get('system', 'N/A')
    value = contact.get('value', 'N/A')
    st.markdown(f"**{system.title()}:** {value}")

# Add some spacing
st.markdown("---")

# Address Information Section
st.markdown("### 📍 Address")

# Create two columns for address and map
addr_col, map_col = st.columns([1, 1])

address = patient_data.get('address', [{}])[0]
if address:
    with addr_col:
        line = address.get('line', ['N/A'])[0]
        city = address.get('city', 'N/A')
        state = address.get('state', 'N/A')
        country = address.get('country', 'N/A')
        
        st.markdown(f"**Street:** {line}")
        st.markdown(f"**City:** {city}")
        st.markdown(f"**State:** {state}")
        st.markdown(f"**Country:** {country}")
    
    # Create address string for geocoding
    address_parts = []
    if line != 'N/A':
        address_parts.append(line)
    if city != 'N/A':
        address_parts.append(city)
    if state != 'N/A':
        address_parts.append(state)
    if country != 'N/A':
        address_parts.append(country)
    
    if address_parts:
        address_str = ", ".join(address_parts)
        coordinates = get_location_coordinates(address_str)
        
        if coordinates:
            with map_col:
                # Create the map with improved styling
                m = folium.Map(
                    location=coordinates,
                    zoom_start=15,
                    width='100%',
                    height='100%'
                )
                
                # Add a marker with a popup containing the address
                folium.Marker(
                    coordinates,
                    popup=folium.Popup(address_str, max_width=300),
                    tooltip="Patient's Location",
                    icon=folium.Icon(
                        color='red',
                        icon='info-sign',
                        prefix='fa'
                    )
                ).add_to(m)
                
                # Add a circle around the location
                folium.Circle(
                    coordinates,
                    radius=100,
                    color='red',
                    fill=True,
                    fillOpacity=0.2
                ).add_to(m)
                
                # Display the map with custom size
                folium_static(m, width=400, height=300)  # Adjusted size for column
        else:
            with map_col:
                st.info("Location could not be displayed on map")

# Add some spacing
st.markdown("---")

# Rest of the sections (Identifiers, Extensions, etc.)
st.markdown("### 🆔 Identifiers")
if 'identifier' in patient_data:
    identifiers_data = []
    for identifier in patient_data['identifier']:
        identifiers_data.append({
            'System': identifier.get('system', 'N/A'),
            'Value': identifier.get('value', 'N/A'),
            'Type': identifier.get('type', {}).get('text', 'N/A')
        })
    if identifiers_data:
        st.table(identifiers_data)

# Extensions Table
if 'extension' in patient_data:
    st.markdown("### 📑 Extensions")
    extensions_data = []
    for extension in patient_data['extension']:
        extensions_data.append({
            'URL': extension.get('url', 'N/A'),
            'Value': str(extension.get('valueString', extension.get('valueCode', 'N/A')))
        })
    if extensions_data:
        st.table(extensions_data)

# Communication Preferences
if 'communication' in patient_data:
    st.markdown("### 🗣️ Communication Preferences")
    comm_data = []
    for comm in patient_data['communication']:
        language = comm.get('language', {}).get('text', 'N/A')
        preferred = comm.get('preferred', False)
        comm_data.append({
            'Language': language,
            'Preferred': '✓' if preferred else '✗'
        })
    if comm_data:
        st.table(comm_data)