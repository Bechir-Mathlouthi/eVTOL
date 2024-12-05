import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from streamlit_folium import folium_static
import joblib
import numpy as np
from datetime import datetime, timedelta
import json
from pathlib import Path

# Page configuration with custom theme
st.set_page_config(
    page_title="eVTOL Operations Dashboard",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        background-color: #f5f5f5;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 10px 24px;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .reportview-container {
        background: #f5f5f5;
    }
    .sidebar .sidebar-content {
        background-color: #262730;
    }
    h1 {
        color: #1E88E5;
        font-family: 'Helvetica Neue', sans-serif;
    }
    h2 {
        color: #333;
        font-family: 'Helvetica Neue', sans-serif;
    }
    .stAlert {
        background-color: rgba(255, 255, 255, 0.9);
    }
    </style>
""", unsafe_allow_html=True)

# Load the trained models
@st.cache_resource
def load_models():
    try:
        traffic_model = joblib.load('models/traffic_model.joblib')
        traffic_scaler = joblib.load('models/traffic_scaler.joblib')
        safety_model = joblib.load('models/safety_model.joblib')
        safety_scaler = joblib.load('models/safety_scaler.joblib')
        safety_le = joblib.load('models/safety_label_encoder.joblib')
        return traffic_model, traffic_scaler, safety_model, safety_scaler, safety_le
    except Exception as e:
        st.error(f"Error loading models: {str(e)}")
        return None, None, None, None, None

# Database connection with context manager
class DatabaseConnection:
    def __init__(self, db_path='data/evtol_operations.db'):
        self.db_path = db_path

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path)
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()

def get_weather_icon(condition):
    icons = {
        'Clear': '☀️',
        'Rain': '🌧️',
        'Snow': '❄️',
        'Fog': '🌫️',
        'Storm': '⛈️'
    }
    return icons.get(condition, '❓')

def create_map(flights_df):
    m = folium.Map(location=[40.7128, -74.0060], zoom_start=10)
    
    for _, flight in flights_df.iterrows():
        if flight['path']:
            try:
                path = json.loads(flight['path'])
                folium.CircleMarker(
                    location=path,
                    radius=8,
                    color='red' if flight['status'] == 'In Progress' else 'blue',
                    popup=f"Flight {flight['flight_id']}\n{flight['status']}"
                ).add_to(m)
            except:
                continue
    
    return m

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", [
    "📊 Dashboard",
    "✈️ Flight Management",
    "🛡️ Safety Analysis",
    "🔧 Maintenance Hub",
    "📈 Analytics"
])

# Load models
models = load_models()

if page == "📊 Dashboard":
    st.title("eVTOL Operations Command Center")
    
    # Real-time metrics
    with DatabaseConnection() as conn:
        active_flights = pd.read_sql("SELECT COUNT(*) as count FROM flights WHERE status='In Progress'", conn).iloc[0]['count']
        total_evtols = pd.read_sql("SELECT COUNT(*) as count FROM evtols", conn).iloc[0]['count']
        critical_maintenance = pd.read_sql("SELECT COUNT(*) as count FROM evtols WHERE maintenance_status='Critical'", conn).iloc[0]['count']
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Active Flights", active_flights, "Real-time")
    with col2:
        st.metric("Fleet Size", total_evtols)
    with col3:
        st.metric("Critical Maintenance", critical_maintenance, "Needs attention" if critical_maintenance > 0 else "All good")
    with col4:
        with DatabaseConnection() as conn:
            avg_battery = pd.read_sql("SELECT AVG(battery_status) as avg FROM evtols", conn).iloc[0]['avg']
        st.metric("Avg Battery Level", f"{avg_battery:.1f}%")
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Live Flight Map")
        with DatabaseConnection() as conn:
            flights_df = pd.read_sql("SELECT * FROM flights WHERE status='In Progress'", conn)
        folium_static(create_map(flights_df))
        
    with col2:
        st.subheader("Weather Alerts")
        with DatabaseConnection() as conn:
            weather_data = pd.read_sql("""
                SELECT location, condition, risk_level, temperature, wind_speed
                FROM weather
                WHERE time >= datetime('now', '-1 hour')
                ORDER BY time DESC LIMIT 5
            """, conn)
        
        for _, weather in weather_data.iterrows():
            with st.expander(f"{get_weather_icon(weather['condition'])} {weather['location']}"):
                st.write(f"Risk Level: {weather['risk_level']}")
                st.write(f"Temperature: {weather['temperature']}°C")
                st.write(f"Wind Speed: {weather['wind_speed']} km/h")

    # Traffic and Battery Analytics
    st.subheader("System Analytics")
    col1, col2 = st.columns(2)
    
    with col1:
        with DatabaseConnection() as conn:
            traffic_data = pd.read_sql("""
                SELECT route, congestion_level, COUNT(*) as count
                FROM traffic
                GROUP BY route, congestion_level
            """, conn)
        
        fig = px.density_heatmap(
            traffic_data,
            x="route",
            y="congestion_level",
            z="count",
            title="Traffic Density by Route",
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        with DatabaseConnection() as conn:
            battery_data = pd.read_sql("""
                SELECT model_type, AVG(battery_status) as avg_battery,
                       COUNT(*) as count
                FROM evtols
                GROUP BY model_type
            """, conn)
        
        fig = px.bar(
            battery_data,
            x="model_type",
            y="avg_battery",
            color="count",
            title="Average Battery Status by Model Type",
            labels={"avg_battery": "Average Battery Level (%)"}
        )
        st.plotly_chart(fig, use_container_width=True)

elif page == "✈️ Flight Management":
    st.title("Flight Operations Center")
    
    tabs = st.tabs(["Schedule Flight", "Active Flights", "Flight History"])
    
    with tabs[0]:
        st.subheader("Schedule New Flight")
        col1, col2 = st.columns(2)
        
        with col1:
            origin = st.text_input("Origin")
            destination = st.text_input("Destination")
            
            with DatabaseConnection() as conn:
                available_evtols = pd.read_sql("""
                    SELECT id, model_type, battery_status
                    FROM evtols
                    WHERE maintenance_status = 'OK'
                    AND battery_status >= 20
                """, conn)
            
            if not available_evtols.empty:
                evtol_id = st.selectbox(
                    "Select eVTOL",
                    options=available_evtols['id'],
                    format_func=lambda x: f"{x} (Battery: {available_evtols[available_evtols['id']==x]['battery_status'].iloc[0]}%)"
                )
            else:
                st.error("No available eVTOLs!")
                evtol_id = None
        
        with col2:
            st.write("Estimated Flight Parameters")
            energy_consumption = st.slider("Estimated Energy Consumption (kWh)", 0, 200, 100)
            st.info(f"Estimated Range: {energy_consumption * 0.5:.1f} km")
        
        if st.button("Schedule Flight", key="schedule_flight"):
            if origin and destination and evtol_id:
                with DatabaseConnection() as conn:
                    cursor = conn.cursor()
                    flight_id = f"FL{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    
                    try:
                        cursor.execute("""
                            INSERT INTO flights (flight_id, origin, destination, energy_consumption, status)
                            VALUES (?, ?, ?, ?, 'Scheduled')
                        """, (flight_id, origin, destination, energy_consumption))
                        conn.commit()
                        st.success(f"Flight scheduled successfully! Flight ID: {flight_id}")
                    except Exception as e:
                        st.error(f"Error scheduling flight: {str(e)}")
            else:
                st.warning("Please fill in all required fields!")
    
    with tabs[1]:
        st.subheader("Active Flights Monitor")
        with DatabaseConnection() as conn:
            active_flights = pd.read_sql(
                "SELECT * FROM flights WHERE status='In Progress'",
                conn
            )
        
        if not active_flights.empty:
            for _, flight in active_flights.iterrows():
                with st.expander(f"Flight {flight['flight_id']} - {flight['origin']} to {flight['destination']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"Status: {flight['status']}")
                        st.write(f"Energy Consumption: {flight['energy_consumption']} kWh")
                    with col2:
                        st.write(f"Created: {flight['created_at']}")
                        if st.button("Mark as Completed", key=f"complete_{flight['flight_id']}"):
                            with DatabaseConnection() as conn:
                                cursor = conn.cursor()
                                cursor.execute(
                                    "UPDATE flights SET status='Completed' WHERE flight_id=?",
                                    (flight['flight_id'],)
                                )
                                conn.commit()
                            st.success("Flight marked as completed!")
                            st.rerun()
        else:
            st.info("No active flights at the moment.")
    
    with tabs[2]:
        st.subheader("Flight History")
        with DatabaseConnection() as conn:
            flight_history = pd.read_sql(
                "SELECT * FROM flights ORDER BY created_at DESC LIMIT 100",
                conn
            )
        
        # Flight history visualization
        fig = px.timeline(
            flight_history,
            x_start="created_at",
            x_end="created_at",
            y="flight_id",
            color="status",
            title="Recent Flight Timeline"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed flight table
        st.dataframe(
            flight_history,
            column_config={
                "created_at": "Timestamp",
                "flight_id": "Flight ID",
                "status": st.column_config.SelectboxColumn(
                    "Status",
                    help="Flight status",
                    width="medium",
                    options=[
                        "Scheduled",
                        "In Progress",
                        "Completed",
                        "Cancelled"
                    ]
                )
            },
            hide_index=True
        )

elif page == "🛡️ Safety Analysis":
    st.title("Safety Risk Assessment Center")
    
    if not all(models):
        st.error("Error: Models not loaded properly!")
    else:
        traffic_model, traffic_scaler, safety_model, safety_scaler, safety_le = models
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Real-time Risk Assessment")
            
            # Input parameters
            weather_condition = st.selectbox(
                "Weather Condition",
                ["Clear", "Rain", "Snow", "Fog", "Storm"]
            )
            
            col_a, col_b = st.columns(2)
            with col_a:
                temperature = st.slider("Temperature (°C)", -20, 40, 20)
                wind_speed = st.slider("Wind Speed (km/h)", 0, 100, 15)
            with col_b:
                vehicle_count = st.slider("Vehicle Count in Area", 0, 50, 10)
                average_speed = st.slider("Average Speed (km/h)", 0, 200, 100)
            
            if st.button("Analyze Risk", key="analyze_risk"):
                try:
                    # Prepare input data
                    condition_encoded = safety_le.transform([weather_condition])[0]
                    input_data = np.array([[
                        condition_encoded, temperature, wind_speed,
                        vehicle_count, average_speed
                    ]])
                    input_scaled = safety_scaler.transform(input_data)
                    
                    # Predict risk level
                    risk_prediction = safety_model.predict(input_scaled)[0]
                    risk_proba = safety_model.predict_proba(input_scaled)[0]
                    risk_levels = ['Low', 'Medium', 'High']
                    risk_level = risk_levels[risk_prediction]
                    
                    # Create gauge chart for risk visualization
                    fig = go.Figure(go.Indicator(
                        mode = "gauge+number",
                        value = risk_prediction * 50,
                        title = {'text': "Risk Level"},
                        gauge = {
                            'axis': {'range': [0, 100]},
                            'bar': {'color': "darkblue"},
                            'steps': [
                                {'range': [0, 33], 'color': "lightgreen"},
                                {'range': [33, 66], 'color': "yellow"},
                                {'range': [66, 100], 'color': "red"}
                            ]
                        }
                    ))
                    st.plotly_chart(fig)
                    
                    # Display risk probabilities
                    st.write("Risk Probability Distribution:")
                    prob_df = pd.DataFrame({
                        'Risk Level': risk_levels,
                        'Probability': risk_proba
                    })
                    st.bar_chart(prob_df.set_index('Risk Level'))
                    
                except Exception as e:
                    st.error(f"Error in risk analysis: {str(e)}")
        
        with col2:
            st.subheader("Historical Risk Patterns")
            with DatabaseConnection() as conn:
                historical_risks = pd.read_sql("""
                    SELECT risk_level, COUNT(*) as count
                    FROM weather
                    GROUP BY risk_level
                """, conn)
            
            fig = px.pie(
                historical_risks,
                values='count',
                names='risk_level',
                title='Historical Risk Distribution',
                color='risk_level',
                color_discrete_map={
                    'Low': 'green',
                    'Medium': 'yellow',
                    'High': 'red'
                }
            )
            st.plotly_chart(fig)

elif page == "🔧 Maintenance Hub":
    st.title("Maintenance Control Center")
    
    # Fleet Overview
    st.subheader("Fleet Status Overview")
    with DatabaseConnection() as conn:
        fleet_data = pd.read_sql("""
            SELECT id, model_type, battery_status, maintenance_status,
                   usage_count, last_maintenance
            FROM evtols
            ORDER BY maintenance_status DESC
        """, conn)
    
    # Fleet metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Total Fleet",
            len(fleet_data),
            f"Active: {len(fleet_data[fleet_data['maintenance_status']=='OK'])}"
        )
    with col2:
        avg_battery = fleet_data['battery_status'].mean()
        st.metric(
            "Average Battery",
            f"{avg_battery:.1f}%",
            f"{len(fleet_data[fleet_data['battery_status']<20])} critical"
        )
    with col3:
        maintenance_needed = len(fleet_data[fleet_data['maintenance_status']!='OK'])
        st.metric(
            "Maintenance Required",
            maintenance_needed,
            "vehicles"
        )
    
    # Maintenance Schedule
    st.subheader("Maintenance Schedule")
    maintenance_view = st.radio(
        "View",
        ["All Vehicles", "Needs Maintenance", "OK Status"],
        horizontal=True
    )
    
    if maintenance_view == "Needs Maintenance":
        fleet_data = fleet_data[fleet_data['maintenance_status']!='OK']
    elif maintenance_view == "OK Status":
        fleet_data = fleet_data[fleet_data['maintenance_status']=='OK']
    
    for _, vehicle in fleet_data.iterrows():
        with st.expander(f"eVTOL {vehicle['id']} - {vehicle['model_type']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"Battery Status: {vehicle['battery_status']}%")
                st.write(f"Maintenance Status: {vehicle['maintenance_status']}")
                st.write(f"Usage Count: {vehicle['usage_count']} flights")
            with col2:
                st.write(f"Last Maintenance: {vehicle['last_maintenance']}")
                if vehicle['maintenance_status'] != 'OK':
                    if st.button("Mark Maintenance Complete", key=f"maintain_{vehicle['id']}"):
                        with DatabaseConnection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE evtols
                                SET maintenance_status='OK',
                                    last_maintenance=CURRENT_TIMESTAMP
                                WHERE id=?
                            """, (vehicle['id'],))
                            conn.commit()
                        st.success("Maintenance status updated!")
                        st.rerun()

elif page == "📈 Analytics":
    st.title("Analytics and Insights")
    
    # Time range selector
    time_range = st.selectbox(
        "Time Range",
        ["Last 24 Hours", "Last Week", "Last Month", "All Time"]
    )
    
    time_filters = {
        "Last 24 Hours": "datetime('now', '-1 day')",
        "Last Week": "datetime('now', '-7 days')",
        "Last Month": "datetime('now', '-30 days')",
        "All Time": "datetime('now', '-100 years')"  # Effectively all time
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Flight Statistics")
        with DatabaseConnection() as conn:
            flight_stats = pd.read_sql(f"""
                SELECT status, COUNT(*) as count
                FROM flights
                WHERE created_at >= {time_filters[time_range]}
                GROUP BY status
            """, conn)
        
        fig = px.pie(
            flight_stats,
            values='count',
            names='status',
            title='Flight Status Distribution'
        )
        st.plotly_chart(fig)
    
    with col2:
        st.subheader("Energy Consumption Trends")
        with DatabaseConnection() as conn:
            energy_data = pd.read_sql(f"""
                SELECT DATE(created_at) as date,
                       AVG(energy_consumption) as avg_energy
                FROM flights
                WHERE created_at >= {time_filters[time_range]}
                GROUP BY DATE(created_at)
                ORDER BY date
            """, conn)
        
        fig = px.line(
            energy_data,
            x='date',
            y='avg_energy',
            title='Average Energy Consumption Over Time'
        )
        st.plotly_chart(fig)
    
    # Advanced Analytics
    st.subheader("Advanced Analytics")
    
    tabs = st.tabs(["Traffic Patterns", "Safety Trends", "Maintenance Analysis"])
    
    with tabs[0]:
        with DatabaseConnection() as conn:
            hourly_traffic = pd.read_sql(f"""
                SELECT strftime('%H', timestamp) as hour,
                       route,
                       AVG(vehicle_count) as avg_vehicles
                FROM traffic
                WHERE timestamp >= {time_filters[time_range]}
                GROUP BY hour, route
            """, conn)
        
        fig = px.density_heatmap(
            hourly_traffic,
            x='hour',
            y='route',
            z='avg_vehicles',
            title='Hourly Traffic Patterns by Route'
        )
        st.plotly_chart(fig)
    
    with tabs[1]:
        with DatabaseConnection() as conn:
            safety_trends = pd.read_sql(f"""
                SELECT DATE(time) as date,
                       risk_level,
                       COUNT(*) as count
                FROM weather
                WHERE time >= {time_filters[time_range]}
                GROUP BY date, risk_level
                ORDER BY date
            """, conn)
        
        fig = px.area(
            safety_trends,
            x='date',
            y='count',
            color='risk_level',
            title='Safety Risk Trends Over Time'
        )
        st.plotly_chart(fig)
    
    with tabs[2]:
        with DatabaseConnection() as conn:
            maintenance_analysis = pd.read_sql(f"""
                SELECT model_type,
                       AVG(usage_count) as avg_usage,
                       COUNT(*) as total_vehicles,
                       SUM(CASE WHEN maintenance_status != 'OK' THEN 1 ELSE 0 END) as maintenance_needed
                FROM evtols
                GROUP BY model_type
            """, conn)
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig.add_trace(
            go.Bar(
                x=maintenance_analysis['model_type'],
                y=maintenance_analysis['avg_usage'],
                name="Average Usage"
            ),
            secondary_y=False
        )
        
        fig.add_trace(
            go.Scatter(
                x=maintenance_analysis['model_type'],
                y=maintenance_analysis['maintenance_needed'] / maintenance_analysis['total_vehicles'] * 100,
                name="Maintenance Rate (%)",
                mode='lines+markers'
            ),
            secondary_y=True
        )
        
        fig.update_layout(title="Maintenance Analysis by Model Type")
        fig.update_yaxes(title_text="Average Usage Count", secondary_y=False)
        fig.update_yaxes(title_text="Maintenance Rate (%)", secondary_y=True)
        
        st.plotly_chart(fig)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>eVTOL Smart Operations and Safety Management System - Powered by AI</p>
        <p style='color: #666; font-size: 0.8em'>© 2024 All rights reserved</p>
    </div>
    """,
    unsafe_allow_html=True
) 