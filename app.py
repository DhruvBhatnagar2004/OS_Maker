from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__, static_folder='./build', static_url_path='')
CORS(app)

# Database setup
def get_db_connection():
    conn = sqlite3.connect('osmaker.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS os_configurations
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     selected_os TEXT,
                     option TEXT,
                     customization_details TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS os_options
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     name TEXT,
                     description TEXT,
                     image TEXT)''')
    conn.commit()
    conn.close()

init_db()

# API routes
@app.route('/api/os-options', methods=['GET'])
def get_os_options():
    conn = get_db_connection()
    os_options = conn.execute('SELECT * FROM os_options').fetchall()
    conn.close()
    return jsonify([dict(row) for row in os_options])

@app.route('/api/submit-os', methods=['POST'])
def submit_os():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO os_configurations (selected_os, option, customization_details) VALUES (?, ?, ?)',
                 (data['selectedOS'], data['option'], data['customizationDetails']))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return jsonify({"message": "OS configuration submitted successfully", "id": new_id}), 201

@app.route('/api/get-submissions', methods=['GET'])
def get_submissions():
    conn = get_db_connection()
    submissions = conn.execute('SELECT * FROM os_configurations ORDER BY id DESC LIMIT 5').fetchall()
    conn.close()
    return jsonify([dict(row) for row in submissions])

# Serve React App
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True)