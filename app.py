from flask import Flask, jsonify, g, request
from flask_swagger_ui import get_swaggerui_blueprint
import sqlite3

app = Flask(__name__)
DATABASE = 'states.db'

SWAGGER_URL = '/swagger'
API_URL = '/static/swagger.json'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "States of the World API"
    }
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

def get_db():

    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    """Closes the database connection automatically when request is done."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route('/')
def home():
    """The Homepage: Lists available API endpoints."""
    return jsonify({
        "message": "Welcome to the States of the World API",
        "docs": "Check the documentation at /swagger",
        "endpoints": [
            "/api/countries",
            "/api/countries/top-10-population",
            "/api/countries/top-10-density",
            "/api/country/<name>"
        ]
    })


@app.route('/api/countries', methods=['GET'])
def get_all_countries():
    """Returns a lightweight list of all countries."""
    cur = get_db().cursor()
    cur.execute("SELECT id, name, capital, population, area_km2, density FROM countries")
    rows = cur.fetchall()

    result = [dict(row) for row in rows]
    return jsonify(result)


@app.route('/api/countries/top-10-population', methods=['GET'])
def get_top_population():
    """Returns the top 10 most populated countries."""
    cur = get_db().cursor()
    cur.execute('''
        SELECT name, population, density, area_km2 
        FROM countries 
        WHERE population IS NOT NULL 
        ORDER BY population DESC 
        LIMIT 10
    ''')
    rows = cur.fetchall()
    return jsonify([dict(row) for row in rows])


@app.route('/api/countries/top-10-density', methods=['GET'])
def get_top_density():
    """Returns the top 10 most densely populated countries."""
    cur = get_db().cursor()
    cur.execute('''
        SELECT name, density, population, area_km2 
        FROM countries 
        WHERE density IS NOT NULL 
        ORDER BY density DESC 
        LIMIT 10
    ''')
    rows = cur.fetchall()
    return jsonify([dict(row) for row in rows])


@app.route('/api/country/<string:country_name>', methods=['GET'])
def get_country_details(country_name):
    """
    Detailed view for a single country.
    Includes JOINs to fetch Neighbors and Languages.
    """
    cur = get_db().cursor()

    # 1. Fetch Basic Info (Case-insensitive search)
    cur.execute("SELECT * FROM countries WHERE name LIKE ?", (country_name,))
    country = cur.fetchone()

    if country is None:
        return jsonify({"error": "Country not found"}), 404

    country_dict = dict(country)
    country_id = country['id']

    # 2. Fetch Languages (MtoM Join)
    cur.execute('''
        SELECT l.name FROM languages l
        JOIN country_languages cl ON l.id = cl.language_id
        WHERE cl.country_id = ?
    ''', (country_id,))
    country_dict['languages'] = [row['name'] for row in cur.fetchall()]

    # 3. Fetch Neighbors (OtoM Join)
    cur.execute('''
        SELECT neighbor_name FROM borders WHERE country_id = ?
    ''', (country_id,))
    country_dict['neighbors'] = [row['neighbor_name'] for row in cur.fetchall()]

    return jsonify(country_dict)


if __name__ == '__main__':
    app.run(debug=True, port=5000)