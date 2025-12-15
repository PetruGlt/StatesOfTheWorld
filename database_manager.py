import sqlite3
import json
import os

DB_NAME = "states.db"

class DatabaseManager:
    def __init__(self, database):
        self.db_name = database
        self.conn = None
        self.cursor = None

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
            print(f"Connected to database: {self.db_name}")
        except sqlite3.Error as e:
            print(f"Database error: {e}")

    def close(self):
        if self.conn:
            self.conn.close()
            print("Database connection closed.")

    def create_schema(self):
        # Main Countries Table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS countries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            capital TEXT,
            population INTEGER,
            area_km2 REAL,
            density REAL,
            timezone TEXT,
            political_system TEXT
        )
        ''')

        # Languages Table (Unique list of all languages in the world)
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS languages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
        ''')

        # Join Table: Country <-> Languages (MtoM)
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS country_languages (
            country_id INTEGER,
            language_id INTEGER,
            FOREIGN KEY (country_id) REFERENCES countries (id),
            FOREIGN KEY (language_id) REFERENCES languages (id),
            PRIMARY KEY (country_id, language_id)
        )
        ''')

        # Borders Table (OtoM)
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS borders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_id INTEGER,
            neighbor_name TEXT,
            FOREIGN KEY (country_id) REFERENCES countries (id)
        )
        ''')

        self.conn.commit()
        print("Tables created successfully.")

    def populate_from_json(self, json_file):

        if not os.path.exists(json_file):
            print(f"Error: {json_file} not found.")
            return

        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"Importing {len(data)} countries into database...")

        for entry in data:
            try:
                self.cursor.execute('''
                    INSERT OR IGNORE INTO countries 
                    (name, capital, population, area_km2, density, timezone, political_system)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    entry['name'],
                    entry['capital'],
                    entry['population'],
                    entry['area_in_km2'],
                    entry['density'],
                    entry['timezone'],
                    entry['political_system']
                ))

                # Get the ID of the country we just inserted
                # If ignore was triggered (duplicate), we need to fetch the ID manually
                self.cursor.execute("SELECT id FROM countries WHERE name = ?", (entry['name'],))
                country_id = self.cursor.fetchone()[0]

                # Process Languages (Comma separated string in JSON)
                if entry.get('language'):
                    # "English, French" -> ["English", "French"]
                    langs = [l.strip() for l in entry['language'].split(',')]

                    for lang_name in langs:
                        # Insert language into languages table (if it does not exist)
                        self.cursor.execute("INSERT OR IGNORE INTO languages (name) VALUES (?)", (lang_name,))

                        # Get language ID
                        self.cursor.execute("SELECT id FROM languages WHERE name = ?", (lang_name,))
                        lang_id = self.cursor.fetchone()[0]

                        # Link in koin Table
                        self.cursor.execute('''
                            INSERT OR IGNORE INTO country_languages (country_id, language_id) 
                            VALUES (?, ?)
                        ''', (country_id, lang_id))

                # Process Neighbors (List in JSON)
                if entry.get('neighbors'):
                    for neighbor in entry['neighbors']:
                        self.cursor.execute('''
                            INSERT INTO borders (country_id, neighbor_name)
                            VALUES (?, ?)
                        ''', (country_id, neighbor))

            except sqlite3.Error as e:
                print(f"Error inserting {entry['name']}: {e}")

        self.conn.commit()
        print("Data population complete.")

    def test_query(self):
        print("\n--- TEST: Top 10 Populated Countries ---")
        self.cursor.execute("SELECT name, population FROM countries ORDER BY population DESC LIMIT 10")
        for row in self.cursor.fetchall():
            print(f"{row[0]}: {row[1]:,}")

        print("\n--- TEST: Neighbors of Romania ---")
        self.cursor.execute('''
            SELECT neighbor_name FROM borders 
            JOIN countries ON borders.country_id = countries.id 
            WHERE countries.name = 'Romania'
        ''')
        print([row[0] for row in self.cursor.fetchall()])

        print("\n--- TEST: Top 10 Density Population Countries ---")
        self.cursor.execute("SELECT name, density FROM countries ORDER BY density DESC LIMIT 10")
        for row in self.cursor.fetchall():
            print(f"{row[0]}: {row[1]:,}")

    def add_indexes(self):
        print("Optimization: Adding database indexes...")
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            # 1. Index for fast country lookups by name (used in /api/country/<name>)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_country_name ON countries(name)")

            # 2. Indexes for sorting (used in Top 10 routes)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_population ON countries(population)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_density ON countries(density)")

            # 3. Index for filtering (used in Search route)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_language_name ON languages(name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_neighbor_name ON borders(neighbor_name)")

            conn.commit()
            print("Indexes added.")
            conn.close()

        except sqlite3.Error as e:
            print(f"❌ Error adding indexes: {e}")



if __name__ == "__main__":
    db = DatabaseManager(DB_NAME)
    db.connect()
    db.create_schema()

    # verify if the tables in the database are populated before populating it
    cur = db.conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM countries")
        count = cur.fetchone()[0]
    except sqlite3.OperationalError:
        count = 0

    if count == 0:
        db.populate_from_json('states_final.json')

    db.test_query()
    db.add_indexes()
    db.close()