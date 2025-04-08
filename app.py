import requests
import pandas as pd
import rasterio
import streamlit as st
import plotly.express as px

# Funktion zur Abfrage der Koordinaten (Beispiel)
def get_coordinates(gemeinde):
    url = f"https://api3.geo.admin.ch/rest/services/api/SearchServer?searchText={gemeinde}&type=locations&sr=2056"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        x = data['results'][0]['attrs'].get('x')
        y = data['results'][0]['attrs'].get('y')
        return y, x
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return y, x

# Funktion zur Abfrage des Rasterwerts
def get_raster_value(year, coordinates):
    cog_url = f"https://data.geo.admin.ch/ch.bafu.luftreinhaltung-schwefeldioxid/luftreinhaltung-schwefeldioxid_{year}/luftreinhaltung-schwefeldioxid_{year}_2056.tif"
    with rasterio.open(cog_url) as src:
        for val in src.sample([coordinates]):
            return val[0]


# App
# Streamlit app
st.title("Luftqualität in deiner Gemeinde")

# Suchfeld für die Eingabe der Gemeinde
gemeinde = st.text_input('Gib den Namen der Gemeinde ein:')

# Hauptlogik
if gemeinde:
    coordinatesOutput = get_coordinates(gemeinde)

    for year in range(1980, 1985):
        try:
            # Get the raster value for the current year and coordinates
            raster_value = get_raster_value(year, coordinatesOutput)
            # Append the year and raster value to the data list
            data.append([year, raster_value])
        except Exception as e:
            # Handle the error appropriately, e.g., append NaN or skip the year
            data.append([year, float('nan')])  # Append NaN for failed requests

    # Create a pandas DataFrame from the data
    df = pd.DataFrame(data, columns=['Year', 'RasterValue'])
    st.write(df)
