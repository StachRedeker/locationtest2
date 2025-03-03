import streamlit as st
from streamlit_js_eval import get_geolocation
from streamlit_folium import folium_static
import folium
import datetime
import pandas as pd
import base64

import auth
import points
from map_plot import plot_location
import voice_memo

# Liefdesboodschap voor Kim
st.markdown("""
# Gebruikerslocatie op de kaart
Welkom lieve XXX! ❤️  
""")

username, authenticated = auth.authenticate()
if authenticated:
    # Opties voor de gebruiker
    toon_stralen = st.checkbox("Toon stralen", value=True)
    loc = None
    if st.checkbox("Controleer mijn locatie"):
        loc = get_geolocation()
        st.write("Je coördinaten:", loc)
        if loc and "coords" in loc:
            lat = loc["coords"]["latitude"]
            lon = loc["coords"]["longitude"]
            kaart = plot_location(lat, lon, toon_stralen)
            folium_static(kaart, width=700, height=500)
            
            # Gebruiker kan het aantal te tonen locaties aanpassen; standaard is 10.
            aantal_locaties = st.number_input("Aantal locaties om te tonen", min_value=1, value=10, step=1)
            verberg_inactief = st.checkbox("Verberg inactieve locaties", value=False)
            
            if st.button("Toon dichtstbijzijnde locaties"):
                df_points = points.load_points()
                # Bereken de afstand voor elke locatie
                df_points["afstand"] = df_points.apply(lambda row: points.haversine(lat, lon, row["latitude"], row["longitude"]), axis=1)
                huidige_datum = datetime.datetime.utcnow()
                # Filter inactieve locaties als dit gevraagd is
                if verberg_inactief:
                    df_points = df_points[df_points.apply(lambda row: row["available_from"] <= huidige_datum <= row["available_to"], axis=1)]
                # Selecteer de dichtstbijzijnde locaties
                dichtstbijzijnde = df_points.nsmallest(aantal_locaties, "afstand").copy()
                
                # Bouw de kolom voor spraakmemo-status
                spraakmemo_status = []
                for idx, row in dichtstbijzijnde.iterrows():
                    if "voice_memo" not in row or pd.isna(row["voice_memo"]) or row["voice_memo"].strip() == "":
                        spraakmemo_status.append("Geen spraakmemo")
                    else:
                        if not (row["available_from"] <= huidige_datum <= row["available_to"]):
                            spraakmemo_status.append(
                                f"Niet actief (beschikbaar van {row['available_from'].date()} tot {row['available_to'].date()})"
                            )
                        elif row["afstand"] > row["radius"]:
                            spraakmemo_status.append(
                                f"Buiten bereik (afstand: {row['afstand']:.2f} km, straal: {row['radius']:.2f} km)"
                            )
                        else:
                            try:
                                file_data, file_name = voice_memo.get_decrypted_voice_memo(row["voice_memo"])
                                b64 = base64.b64encode(file_data).decode()
                                download_link = f'<a href="data:audio/mpeg;base64,{b64}" download="{file_name}">Download spraakmemo</a>'
                                spraakmemo_status.append(download_link)
                            except Exception as e:
                                spraakmemo_status.append(f"Fout bij decoderen: {str(e)}")
                dichtstbijzijnde["Spraakmemo"] = spraakmemo_status
                dichtstbijzijnde["Afstand (km)"] = dichtstbijzijnde["afstand"].map(lambda d: f"{d:.2f}")
                dichtstbijzijnde["Actieve periode"] = dichtstbijzijnde.apply(lambda row: f"{row['available_from'].date()} tot {row['available_to'].date()}", axis=1)
                display_df = dichtstbijzijnde.rename(columns={"pointer_text": "Locatie", "radius": "Straal (km)"})
                kolommen = ["Locatie", "Straal (km)", "Actieve periode", "Afstand (km)", "Spraakmemo"]
                html_table = display_df[kolommen].to_html(escape=False, index=False)
                st.markdown(html_table, unsafe_allow_html=True)
