import requests
import pandas as pd
import rasterio
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium

# Funktion zur Abfrage der Koordinaten (Beispiel)
# Funktion zur Abfrage der Koordinaten (Beispiel)
def get_coordinates(gemeinde):
    url = f"https://api3.geo.admin.ch/rest/services/api/SearchServer?searchText={gemeinde}&type=locations&sr=2056"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        x = data['results'][0]['attrs'].get('x')
        y = data['results'][0]['attrs'].get('y')
        lat = data['results'][0]['attrs'].get('lat')
        lon = data['results'][0]['attrs'].get('lon')
        return y, x, lat, lon
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return y, x, lat, lon

# Funktion zur Abfrage des Rasterwerts
def get_raster_value(year, coordinates):
    cog_url = f"https://data.geo.admin.ch/ch.bafu.luftreinhaltung-stickstoffdioxid/luftreinhaltung-stickstoffdioxid_{year}/luftreinhaltung-stickstoffdioxid_{year}_2056.tif"
    with rasterio.open(cog_url) as src:
        for val in src.sample([coordinates]):
            return val[0]

def create_map(center):
    m = folium.Map(location=center,
        zoom_start=14,
        control_scale=True,
        tiles="https://wmts.geo.admin.ch/1.0.0/ch.swisstopo.pixelkarte-farbe/default/current/3857/{z}/{x}/{y}.jpeg",
        attr='Map data: &copy; <a href="https://www.swisstopo.ch" target="_blank" rel="noopener noreferrer">swisstopo</a>;<a href="https://www.bafu.admin.ch/" target="_blank" rel="noopener noreferrer">BAFU</a>'
    )
    
    # Zweite WMTS-Ebene hinzufügen
    folium.TileLayer(
        tiles="https://wmts.geo.admin.ch/1.0.0/ch.bafu.luftreinhaltung-stickstoffdioxid/default/2023/3857/{z}/{x}/{y}.png",
        name='Luftreinhaltung Schwefeldioxid',
        overlay=True,
        opacity=0.7,
        show=True,
        attr=' '
    ).add_to(m)
    
    # Punkt bei der center-Position hinzufügen
    folium.Marker(
        location=center,
        popup=gemeinde,
        icon=folium.Icon(color='red')
    ).add_to(m)
    
    return m



# App
# Streamlit app
st.title("Luftqualität in deiner Gemeinde")
st.markdown(
    """
Dank der erfolgreichen Schweizer Luftreinhaltepolitik hat sich die Luftqualität in der Schweiz seit den 1990er Jahren deutlich verbessert.

Wie sieht die Luftqualität in deiner Gemeinde aus? Finde es heraus:

"""
)

# Suchfeld für die Eingabe der Gemeinde
gemeinde = st.text_input('Gib den Namen der Gemeinde ein:')

# Hauptlogik
data = []
if gemeinde:
    coordinatesOutput = get_coordinates(gemeinde)

    for year in range(1990, 1995):
        try:
            # Get the raster value for the current year and coordinates
            raster_value = get_raster_value(year, coordinatesOutput[0:2])
            # Append the year and raster value to the data list
            data.append([year, raster_value])
        except Exception as e:
            # Handle the error appropriately, e.g., append NaN or skip the year
            data.append([year, float('nan')])  # Append NaN for failed requests

    # Create a pandas DataFrame from the data
    df = pd.DataFrame(data, columns=['Year', 'RasterValue'])
    fig = px.bar(df, x='Year', y='RasterValue', title='Schwefeldioxid in µg/m³')
    fig.update_layout(
        xaxis_title='Jahr',
        yaxis_title='Jahresmittelwert (µg/m³)'
        )

    # Hinzufügen einer Linie bei Grenzwert von 30
    fig.add_trace(go.Scatter(
        x=[df['Year'].min(), df['Year'].max()],
        y=[30, 30],
        mode="lines",
        line=go.scatter.Line(color="Red", dash="dash"),
        name='Jahresgrenzwert gemäss Luftreinhalte-Verordnung:  30 µg/m³'
    ))
    
    # Aktualisieren des Layouts, um die Legende hinzuzufügen und weitere Informationen zu ergänzen
    fig.update_layout(
        legend=dict(
            #title="Legende",
            itemsizing="constant",
            orientation="h",  # Horizontale Ausrichtung der Legende
            x=0,  # Position der Legende
            xanchor="left",
            y=-0.2,  # Position der Legende
            yanchor="top",
            bgcolor="white",  # Hintergrundfarbe der Legende
            #bordercolor="Black",  # Rahmenfarbe der Legende
            #borderwidth=2,  # Rahmenbreite der Legende
            font=dict(
                family="Arial",
                size=12,
                color="Black"
            )
        )
    )
    st.plotly_chart(fig)

    m = create_map(coordinatesOutput[2:4])
    output = st_folium(m, width=700)

    st.markdown(
    """
    ***Hinweis***
    
    Die Zeitreihe zeigt die modellierten Karten der Jahresmittelwerte seit 1990 im 200 m Raster, ab 2020 im 20 m Raster.
    Lokal kann die Konzentration von den modellierten Daten abweichen.
    Einzelne Pixel sind nicht für die Bewertung von Einzelstandorten heranzuziehen.
    Der in der Luftreinhalte-Verordnung festgelegte Jahresgrenzwert für NO₂ liegt bei 30 µg/m³
    
    """
    )
