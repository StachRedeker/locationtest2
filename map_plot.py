import folium
import datetime
from points import load_points

def plot_location(lat, lon, show_radii):
    """
    Creates a Folium map centered on (lat, lon) and adds markers and circles.
    """
    m = folium.Map(location=[lat, lon], zoom_start=12, control_scale=True)
    folium.Marker([lat, lon], popup="Your Location", tooltip="You are here", icon=folium.Icon(color="blue")).add_to(m)
    df = load_points()
    if not df.empty:
        current_date = datetime.datetime.utcnow()
        for _, row in df.iterrows():
            r_lat = row["latitude"]
            r_lon = row["longitude"]
            radius = row["radius"]
            available_from = row["available_from"]
            available_to = row["available_to"]
            pointer_text = row["pointer_text"]
            is_active = available_from <= current_date <= available_to
            color = "green" if is_active else "gray"
            if show_radii and is_active:
                folium.Circle(
                    location=[r_lat, r_lon],
                    radius=radius * 1000,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.3
                ).add_to(m)
            if is_active:
                popup_text = f"{pointer_text}<br>Radius: {radius:.2f} km"
            else:
                popup_text = f"{pointer_text}<br>Available from: {available_from.date()} to {available_to.date()}"
            folium.Marker([r_lat, r_lon], popup=popup_text, tooltip=pointer_text, icon=folium.Icon(color=color)).add_to(m)
    return m
