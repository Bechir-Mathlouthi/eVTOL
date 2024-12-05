import sqlite3
import random
from datetime import datetime, timedelta
import numpy as np

def populate_database():
    conn = sqlite3.connect('data/evtol_operations.db')
    cursor = conn.cursor()
    
    # Sample data for eVTOLs
    evtol_models = ['Model-A', 'Model-B', 'Model-C']
    for i in range(10):
        evtol_id = f'EVTOL{i:03d}'
        cursor.execute('''
            INSERT INTO evtols (id, battery_status, maintenance_status, usage_count, 
                              last_maintenance, model_type, max_range)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            evtol_id,
            random.uniform(60, 100),  # battery_status
            random.choice(['OK', 'Warning']),  # maintenance_status
            random.randint(0, 100),  # usage_count
            datetime.now() - timedelta(days=random.randint(0, 30)),  # last_maintenance
            random.choice(evtol_models),  # model_type
            random.uniform(100, 300)  # max_range
        ))
    
    # Sample weather data
    locations = ['Zone-A', 'Zone-B', 'Zone-C', 'Zone-D']
    conditions = ['Clear', 'Rain', 'Snow', 'Fog', 'Storm']
    risk_levels = ['Low', 'Medium', 'High']
    
    for i in range(100):
        time = datetime.now() - timedelta(hours=random.randint(0, 72))
        cursor.execute('''
            INSERT INTO weather (time, location, condition, risk_level, 
                               temperature, wind_speed)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            time,
            random.choice(locations),
            random.choice(conditions),
            random.choice(risk_levels),
            random.uniform(-5, 35),  # temperature
            random.uniform(0, 50)  # wind_speed
        ))
    
    # Sample traffic data
    routes = ['Route1', 'Route2', 'Route3', 'Route4']
    congestion_levels = ['Low', 'Medium', 'High']
    
    for i in range(200):
        time = datetime.now() - timedelta(hours=random.randint(0, 72))
        cursor.execute('''
            INSERT INTO traffic (route, congestion_level, timestamp,
                               vehicle_count, average_speed)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            random.choice(routes),
            random.choice(congestion_levels),
            time,
            random.randint(5, 50),  # vehicle_count
            random.uniform(30, 200)  # average_speed
        ))
    
    # Sample flights data
    origins = ['Heliport-A', 'Heliport-B', 'Heliport-C']
    destinations = ['Vertiport-X', 'Vertiport-Y', 'Vertiport-Z']
    statuses = ['Scheduled', 'In Progress', 'Completed']
    
    for i in range(50):
        flight_id = f'FL{datetime.now().strftime("%Y%m%d")}{i:03d}'
        created_at = datetime.now() - timedelta(hours=random.randint(0, 48))
        cursor.execute('''
            INSERT INTO flights (flight_id, origin, destination, path,
                               energy_consumption, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            flight_id,
            random.choice(origins),
            random.choice(destinations),
            f"[{random.uniform(-74, -73)}, {random.uniform(40, 41)}]",  # sample path coordinates
            random.uniform(50, 150),  # energy_consumption
            random.choice(statuses),
            created_at
        ))
    
    conn.commit()
    conn.close()
    print("Sample data populated successfully!")

if __name__ == "__main__":
    populate_database() 