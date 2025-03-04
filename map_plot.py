import folium
import datetime
import pandas as pd
import points

def plot_location(lat, lon, show_radii):
    """
    Maakt een folium-kaart met jouw positie en voegt markers en cirkels toe voor de locaties.
    Alle teksten zijn in het Nederlands en hebben een piratenstijl.
    """
    m = folium.Map(location=[lat, lon], zoom_start=12, control_scale=True)
    folium.Marker(
        [lat, lon],
        popup="Jouw positie",
        tooltip="Hier ben jij, piraat! 🏴‍☠️",
        icon=folium.Icon(color='blue')
    ).add_to(m)
    
    df = points.load_points()
    if not df.empty:
        current_date = datetime.datetime.utcnow()
        for _, row in df.iterrows():
            r_lat = row["latitude"]
            r_lon = row["longitude"]
            straal = row["radius"]
            available_from = row["available_from"]
            available_to = row["available_to"]
            pointer_text = row["pointer_text"]
            is_active = available_from <= current_date <= available_to
            kleur = "green" if is_active else "gray"
            
            if show_radii and is_active:
                folium.Circle(
                    location=[r_lat, r_lon],
                    radius=straal * 1000,
                    color=kleur,
                    fill=True,
                    fill_color=kleur,
                    fill_opacity=0.3
                ).add_to(m)
            
            if is_active:
                popup_text = f"{pointer_text}<br>Straal: {straal:.2f} km"
            else:
                popup_text = f"{pointer_text}<br>Beschikbaar: {available_from.date()} tot {available_to.date()}"
            
            folium.Marker(
                [r_lat, r_lon],
                popup=popup_text,
                tooltip=pointer_text,
                icon=folium.Icon(color=kleur)
            ).add_to(m)
    return m
