import sqlite3
import os
from pathlib import Path

def create_database():
    try:
        # Create data directory if it doesn't exist
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        print(f"Data directory created/verified at: {data_dir.absolute()}")
        
        db_path = data_dir / 'evtol_operations.db'
        print(f"Creating/connecting to database at: {db_path}")
        
        # Connect to SQLite database (creates it if it doesn't exist)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print("Database connection established")

        # Create Flights table
        print("Creating Flights table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS flights (
            flight_id TEXT PRIMARY KEY,
            origin TEXT NOT NULL,
            destination TEXT NOT NULL,
            path TEXT,
            energy_consumption REAL,
            status TEXT CHECK(status IN ('Scheduled', 'In Progress', 'Completed', 'Cancelled')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Create Weather table
        print("Creating Weather table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS weather (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            location TEXT NOT NULL,
            condition TEXT CHECK(condition IN ('Clear', 'Rain', 'Snow', 'Fog', 'Storm')),
            risk_level TEXT CHECK(risk_level IN ('Low', 'Medium', 'High')),
            temperature REAL,
            wind_speed REAL
        )
        ''')

        # Create eVTOLs table
        print("Creating eVTOLs table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS evtols (
            id TEXT PRIMARY KEY,
            battery_status REAL CHECK(battery_status >= 0 AND battery_status <= 100),
            maintenance_status TEXT CHECK(maintenance_status IN ('OK', 'Warning', 'Critical')),
            usage_count INTEGER DEFAULT 0,
            last_maintenance TIMESTAMP,
            model_type TEXT,
            max_range REAL
        )
        ''')

        # Create Traffic table
        print("Creating Traffic table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS traffic (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route TEXT NOT NULL,
            congestion_level TEXT CHECK(congestion_level IN ('Low', 'Medium', 'High')),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            vehicle_count INTEGER,
            average_speed REAL
        )
        ''')

        # Create indices for better query performance
        print("Creating indices...")
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_flights_status ON flights(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_weather_time ON weather(time)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_traffic_route ON traffic(route)')

        # Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("\nCreated tables:", [table[0] for table in tables])

        # Commit changes and close connection
        conn.commit()
        print("\nChanges committed to database")
        conn.close()
        print("Database connection closed")
        
        return True

    except Exception as e:
        print(f"Error during database setup: {str(e)}")
        return False

if __name__ == "__main__":
    success = create_database()
    if success:
        print("\nDatabase setup completed successfully!")
    else:
        print("\nDatabase setup failed!") 