import streamlit as st
from streamlit_js_eval import get_geolocation
import folium
import datetime
import pandas as pd
import base64
import streamlit.components.v1 as components

import auth
import points
from map_plot import plot_location
import voice_memo

# Piraten-thema titel en introductie
st.title("Piraten Locatiekaart 🏴‍☠️")
st.markdown("""
Ahoy, piraat! Zet koers naar jouw verborgen schat.  
Gebruik deze kaart om je huidige locatie te bepalen en de dichtstbijzijnde geheimen (locaties) te ontdekken.  
Bereid je voor op een avontuur vol verborgen rijkdommen en gevaarlijke wateren! ☠️🏝️
""")

username, authenticated = auth.authenticate()
if authenticated:
    # Optie om cirkels te tonen
    show_radii = st.checkbox("Toon cirkels", value=True, 
                             help="Laat de cirkels zien rond iedere locatie, alsof het vijandelijk water is.")
    
    loc = None
    if st.checkbox("Bepaal mijne locatie", help="Klik hier om jouw positie te bepalen via je browser. Arr!"):
        loc = get_geolocation()
        st.write("Arr! Hier zijn je coördinaten:", loc)
        if loc and "coords" in loc:
            lat = loc["coords"]["latitude"]
            lon = loc["coords"]["longitude"]
            folium_map = plot_location(lat, lon, show_radii)
            # Render de kaart als HTML en vervang vaste breedte door 100%
            map_html = folium_map.get_root().render()
            map_html = map_html.replace('width:700px', 'width:100%')
            components.html(map_html, height=500)
            
            # Invoeropties voor het aantal locaties en het verbergen van inactieve locaties
            num_locations = st.number_input("Aantal locaties om te tonen", 
                                            min_value=1, value=10, step=1,
                                            help="Voer het aantal dichtstbijzijnde locaties in dat je wilt zien. 10 is de standaard.")
            hide_inactive = st.checkbox("Verberg inactieve locaties", value=False, 
                                        help="Verberg locaties die niet actief zijn (buiten de datumperiode).")
            
            if st.button("Toon dichtstbijzijnde locaties, maat!"):
                df_points = points.load_points()
                # Bereken de afstand voor iedere locatie
                df_points["distance"] = df_points.apply(lambda row: points.haversine(lat, lon, row["latitude"], row["longitude"]), axis=1)
                current_date = datetime.datetime.utcnow()
                if hide_inactive:
                    df_points = df_points[df_points.apply(lambda row: row["available_from"] <= current_date <= row["available_to"], axis=1)]
                closest_df = df_points.nsmallest(num_locations, "distance").copy()
                
                voice_memo_status = []
                for idx, row in closest_df.iterrows():
                    if "voice_memo" not in row or pd.isna(row["voice_memo"]) or row["voice_memo"].strip() == "":
                        voice_memo_status.append("Geen schat")
                    else:
                        if not (row["available_from"] <= current_date <= row["available_to"]):
                            voice_memo_status.append(
                                f"Niet actief (beschikbaar van {row['available_from'].date()} tot {row['available_to'].date()})"
                            )
                        elif row["distance"] > row["radius"]:
                            voice_memo_status.append(
                                f"Buiten bereik (afstand: {row['distance']:.2f} km, straal: {row['radius']:.2f} km)"
                            )
                        else:
                            try:
                                file_data, file_name = voice_memo.get_decrypted_voice_memo(row["voice_memo"])
                                b64 = base64.b64encode(file_data).decode()
                                # Change the MIME type to application/octet-stream so no .mp3 is appended.
                                download_link = f'<a href="data:application/octet-stream;base64,{b64}" download="{file_name}">Schat opgraven</a>'
                                voice_memo_status.append(download_link)
                            except Exception as e:
                                voice_memo_status.append(f"Fout bij decryptie: {str(e)}")
                closest_df["Schat"] = voice_memo_status
                closest_df["Afstand (km)"] = closest_df["distance"].map(lambda d: f"{d:.2f}")
                closest_df["Actieve Periode"] = closest_df.apply(
                    lambda row: f"{row['available_from'].date()} tot {row['available_to'].date()}", axis=1
                )
                display_df = closest_df.rename(columns={"pointer_text": "Locatie", "radius": "Straal (km)"})
                final_cols = ["Locatie", "Straal (km)", "Actieve Periode", "Afstand (km)", "Schat"]
                html_table = display_df[final_cols].to_html(escape=False, index=False)
                st.markdown(f'<div style="overflow-x:auto;">{html_table}</div>', unsafe_allow_html=True)
