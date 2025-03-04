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

# Pirate-themed title and introduction
st.title("Piraten Locatiekaart")
st.markdown("""
Ahoy, piraat! Zet koers naar jouw verborgen schat.  
Gebruik deze kaart om je huidige locatie te bepalen en de dichtstbijzijnde geheimen (locaties) te ontdekken.  
Bereid je voor op een avontuur vol verborgen rijkdommen en gevaarlijke wateren!
""")

username, authenticated = auth.authenticate()
if authenticated:
    # Checkbox to show radii (straalgebieden)
    show_radii = st.checkbox("Toon straalgebieden", value=True, 
                             help="Laat de cirkels zien rond iedere locatie, alsof het de grenzen van vijandelijk gebied zijn.")
    
    loc = None
    if st.checkbox("Bepaal mijne locatie", 
                   help="Klik hier om jouw huidige positie te bepalen via je browser. Arr!"):
        loc = get_geolocation()
        st.write("Arr! Hier zijn je coördinaten:", loc)
        if loc and "coords" in loc:
            lat = loc["coords"]["latitude"]
            lon = loc["coords"]["longitude"]
            # Use container width for better responsiveness
            folium_map = plot_location(lat, lon, show_radii)
            folium_static(folium_map, height=500, use_container_width=True)
            
            # User inputs for number of locations to show and whether to hide inactive ones
            num_locations = st.number_input("Aantal locaties om te tonen", 
                                            min_value=1, value=10, step=1,
                                            help="Voer het aantal dichtstbijzijnde locaties in dat je wilt zien. 10 is de standaard.")
            hide_inactive = st.checkbox("Verberg inactieve locaties", value=False, 
                                        help="Verberg locaties die nog niet actief zijn (buiten de datumperiode).")
            
            if st.button("Toon dichtstbijzijnde locaties, maat!"):
                df_points = points.load_points()
                # Bereken de afstand voor iedere locatie
                df_points["distance"] = df_points.apply(lambda row: points.haversine(lat, lon, row["latitude"], row["longitude"]), axis=1)
                current_date = datetime.datetime.utcnow()
                # Filter inactieve locaties indien nodig
                if hide_inactive:
                    df_points = df_points[df_points.apply(lambda row: row["available_from"] <= current_date <= row["available_to"], axis=1)]
                # Selecteer de dichtstbijzijnde 'num_locations' locaties
                closest_df = df_points.nsmallest(num_locations, "distance").copy()
                
                # Bouw de 'Stemmemo' kolom
                voice_memo_status = []
                for idx, row in closest_df.iterrows():
                    if "voice_memo" not in row or pd.isna(row["voice_memo"]) or row["voice_memo"].strip() == "":
                        voice_memo_status.append("Geen stemmemo")
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
                                download_link = f'<a href="data:audio/mpeg;base64,{b64}" download="{file_name}">Download stemmemo</a>'
                                voice_memo_status.append(download_link)
                            except Exception as e:
                                voice_memo_status.append(f"Fout bij decryptie: {str(e)}")
                closest_df["Stemmemo"] = voice_memo_status
                closest_df["Afstand (km)"] = closest_df["distance"].map(lambda d: f"{d:.2f}")
                closest_df["Actieve Periode"] = closest_df.apply(
                    lambda row: f"{row['available_from'].date()} tot {row['available_to'].date()}", axis=1
                )
                display_df = closest_df.rename(columns={"pointer_text": "Locatie", "radius": "Straal (km)"})
                final_cols = ["Locatie", "Straal (km)", "Actieve Periode", "Afstand (km)", "Stemmemo"]
                html_table = display_df[final_cols].to_html(escape=False, index=False)
                # Wrap the table in a responsive div
                st.markdown(f'<div style="overflow-x:auto;">{html_table}</div>', unsafe_allow_html=True)
