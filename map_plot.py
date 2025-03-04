import folium
import datetime
import points
from points import haversine

def plot_location(user_lat, user_lon, show_radii):
    """
    Creates a folium map centered on the user's position and adds markers and circles for each location.
    
    The circle color indicates:
      - Gray: location is inactive (beschikbaar buiten de datumperiode)
      - Green: location is active and the user is within the radius (binnen bereik)
      - Red: location is active but the user is outside the radius (buiten bereik)
    
    User-visible texts are in Dutch with a pirate flavor.
    """
    m = folium.Map(location=[user_lat, user_lon], zoom_start=12, control_scale=True)
    # User's location marker with a blue icon.
    folium.Marker(
        [user_lat, user_lon],
        popup="Jouw positie",
        tooltip="Hier ben jij, piraat! 🏴‍☠️",
        icon=folium.Icon(color='blue', icon='user', prefix='fa')
    ).add_to(m)
    
    df = points.load_points()
    if not df.empty:
        current_date = datetime.datetime.utcnow()
        for _, row in df.iterrows():
            loc_lat = row["latitude"]
            loc_lon = row["longitude"]
            loc_radius = row["radius"]
            available_from = row["available_from"]
            available_to = row["available_to"]
            location_text = row["pointer_text"]
            is_active = available_from <= current_date <= available_to
            distance = haversine(user_lat, user_lon, loc_lat, loc_lon)
            
            # Determine circle color:
            if not is_active:
                circle_color = "gray"
            else:
                circle_color = "green" if distance <= loc_radius else "red"
            
            if show_radii and is_active:
                folium.Circle(
                    location=[loc_lat, loc_lon],
                    radius=loc_radius * 1000,  # convert km to m
                    color=circle_color,
                    fill=True,
                    fill_color=circle_color,
                    fill_opacity=0.3
                ).add_to(m)
            
            if is_active:
                popup_text = f"{location_text}<br>Straal: {loc_radius:.2f} km<br>Afstand: {distance:.2f} km"
            else:
                popup_text = f"{location_text}<br>Beschikbaar: {available_from.date()} tot {available_to.date()}"
            
            folium.Marker(
                [loc_lat, loc_lon],
                popup=popup_text,
                tooltip=location_text,
                icon=folium.Icon(color=circle_color, icon='compass', prefix='fa')
            ).add_to(m)
    return m
