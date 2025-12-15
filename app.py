import logging
import os
from logging.handlers import RotatingFileHandler
import time
from flask import Flask, jsonify, g, request, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
import sqlite3

app = Flask(__name__)
DATABASE = 'states.db'

def setup_logging():
    # Set up a log file that rotates (so it doesn't grow forever)
    handler = RotatingFileHandler('api.log', maxBytes=100000, backupCount=1)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

setup_logging()

@app.before_request
def log_request_info():
    """Log details about every incoming request."""
    g.start_time = time.time()
    app.logger.info(f"REQUEST: {request.method} {request.url} - IP: {request.remote_addr}")

@app.after_request
def log_response_info(response):
    """Log response status and duration."""
    duration = time.time() - g.start_time
    app.logger.info(
        f"RESPONSE: {response.status} - Duration: {duration:.4f}s"
    )
    return response

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
    return jsonify({
        "message": "Welcome to the States of the World API",
        "docs": "Check the documentation at /swagger",
        "endpoints": [
            "/api/countries",
            "/api/countries/top-10-population",
            "/api/countries/top-10-density",
            "/api/country/<name>",
            "/api/countries/search"
        ]
    })


@app.route('/api/countries', methods=['GET'])
def get_all_countries():
    cur = get_db().cursor()
    cur.execute("SELECT id, name, capital, population, area_km2, density FROM countries")
    rows = cur.fetchall()
    return jsonify([dict(row) for row in rows])


@app.route('/api/countries/top-10-population', methods=['GET'])
def get_top_population():
    cur = get_db().cursor()
    cur.execute('''
        SELECT name, population, density, area_km2 
        FROM countries WHERE population IS NOT NULL 
        ORDER BY population DESC LIMIT 10
    ''')
    rows = cur.fetchall()
    return jsonify([dict(row) for row in rows])


@app.route('/api/countries/top-10-density', methods=['GET'])
def get_top_density():
    cur = get_db().cursor()
    cur.execute('''
        SELECT name, density, population, area_km2 
        FROM countries WHERE density IS NOT NULL 
        ORDER BY density DESC LIMIT 10
    ''')
    rows = cur.fetchall()
    return jsonify([dict(row) for row in rows])

@app.route('/api/countries/top-10-language', methods=['GET'])
def get_top_language():
    cur = get_db().cursor()
    cur.execute('''
        SELECT l.name, SUM(c.population) as total_reach
        FROM languages l
        JOIN country_languages cl ON l.id = cl.language_id
        JOIN countries c ON cl.country_id = c.id
        GROUP BY l.name
        ORDER BY total_reach DESC
        LIMIT 10
    ''')
    rows = cur.fetchall()
    return jsonify([dict(row) for row in rows])

@app.route('/api/statistics', methods=['GET'])
def get_stats():
    cur = get_db().cursor()
    stats = {}

    # Total Countries
    cur.execute("SELECT COUNT(*) as total_countries FROM countries")
    stats['total_countries'] = cur.fetchone()['total_countries']

    # Total Population
    cur.execute("SELECT SUM(population) as total_population FROM countries")
    stats['total_population'] = cur.fetchone()['total_population']

    # Average Density
    cur.execute("SELECT AVG(density) as average_density FROM countries WHERE density IS NOT NULL")
    stats['average_density'] = cur.fetchone()['average_density']

    return jsonify(stats)


@app.route('/api/country/<string:country_name>', methods=['GET'])
def get_country_details(country_name):
    cur = get_db().cursor()
    cur.execute("SELECT * FROM countries WHERE name LIKE ?", (country_name,))
    country = cur.fetchone()

    if country is None:
        app.logger.warning(f"404 Not Found: Country '{country_name}'")
        return jsonify({"error": "Country not found"}), 404

    country_dict = dict(country)

    # Languages
    cur.execute('''
        SELECT l.name FROM languages l
        JOIN country_languages cl ON l.id = cl.language_id
        WHERE cl.country_id = ?
    ''', (country_dict['id'],))
    country_dict['languages'] = [row['name'] for row in cur.fetchall()]

    # Neighbors
    cur.execute('SELECT neighbor_name FROM borders WHERE country_id = ?', (country_dict['id'],))
    country_dict['neighbors'] = [row['neighbor_name'] for row in cur.fetchall()]

    return jsonify(country_dict)


@app.route('/api/countries/search', methods=['GET'])
def search_countries():
    language = request.args.get('language')
    neighbor = request.args.get('neighbor')
    political = request.args.get('political_system')
    timezone = request.args.get('timezone')

    query = "SELECT DISTINCT c.name, c.capital, c.population FROM countries c"
    params = []
    conditions = []
    joins = []

    if language:
        joins.append("JOIN country_languages cl ON c.id = cl.country_id JOIN languages l ON cl.language_id = l.id")
        conditions.append("l.name LIKE ?")
        params.append(f"%{language}%")

    if neighbor:
        joins.append("JOIN borders b ON c.id = b.country_id")
        conditions.append("b.neighbor_name LIKE ?")
        params.append(f"%{neighbor}%")

    if political:
        conditions.append("c.political_system LIKE ?")
        params.append(f"%{political}%")

    if timezone:
        conditions.append("c.timezone LIKE ?")
        params.append(f"%{timezone}%")

    full_sql = query
    if joins: full_sql += " " + " ".join(joins)
    if conditions: full_sql += " WHERE " + " AND ".join(conditions)
    full_sql += " ORDER BY c.name"

    cur = get_db().cursor()
    try:
        cur.execute(full_sql, params)
        rows = cur.fetchall()
        return jsonify([dict(row) for row in rows])
    except sqlite3.Error as e:
        app.logger.error(f"Search Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


# --- ERROR HANDLERS ---
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Not Found", "status": 404}), 404


@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Server Error: {error}")
    return jsonify({"error": "Internal Server Error", "status": 500}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)