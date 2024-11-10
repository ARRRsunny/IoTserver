from flask import Flask, request, jsonify, send_file, abort
from flask_cors import CORS
import os
import json
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import urllib.request as ul
import logging
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
# Rest of your code

DATA_DIR = 'data'
GRAPH_DIR = 'graphs'

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(GRAPH_DIR, exist_ok=True)

app = Flask(__name__)
CORS(app)

scheduler = BackgroundScheduler()

def get_data_file():
    today = datetime.now().strftime('%d%m%Y')
    return os.path.join(DATA_DIR, f'sensor_data_{today}.json')

def initialize_data_storage():
    data_file = get_data_file()
    if not os.path.exists(data_file):
        with open(data_file, 'w') as f:
            json.dump([], f)

def daily_task():
    initialize_data_storage()

@app.route('/', methods=['GET'])
def serve_html():
    try:
        url = "https://raw.githubusercontent.com/ARRRsunny/IoTserver/refs/heads/main/graph.html"
        with ul.urlopen(url) as client:
            htmldata = client.read().decode('utf-8')
        return htmldata
    except Exception as e:
        logging.error("Error serving HTML: %s", e)
        abort(500, "Internal server error")

@app.route('/submit-data', methods=['POST'])
def submit_data():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    expected_keys = {"Present", "duration", "wet area", "moisture", "last record time duration"}
    if not expected_keys.issubset(data.keys()):
        return jsonify({'error': 'Invalid data format'}), 400

    data['time'] = datetime.now().strftime('%H:%M:%S')

    data_file = get_data_file()
    with open(data_file, 'r+') as f:
        sensor_data = json.load(f)
        sensor_data.append(data)
        f.seek(0)
        json.dump(sensor_data, f, indent=4)

    return jsonify({'message': 'Data saved successfully'}), 201

def generate_graph(sensor_data, graph_type, date_label):
    times = [entry['time'] for entry in sensor_data]
    data_map = {
        'duration': [entry['duration'] for entry in sensor_data],
        'moisture': [entry['moisture'] for entry in sensor_data],
        'present': [1 if entry['Present'] else 0 for entry in sensor_data],
        'wet_area': [1 if entry['wet area'] else 0 for entry in sensor_data],
        'last_record_duration': [entry['last record time duration'] for entry in sensor_data],
    }

    y_data = data_map.get(graph_type)
    if y_data is None:
        return None

    fig, ax = plt.subplots()
    
    # Plot without connecting lines for 'duration' and 'present'
    if graph_type in ['duration', 'present']:
        ax.scatter(times, y_data)
    else:
        ax.plot(times, y_data, marker='o')

    ax.set_title(f'{graph_type.capitalize()} Over Time - {date_label}')
    ax.set_xlabel('Time')
    ax.set_ylabel(graph_type.capitalize())
    plt.xticks(rotation=45)
    plt.tight_layout()
    graph_file = save_graph(fig, f'{graph_type}_graph.png')
    return graph_file

@app.route('/get-graph/<graph_type>', methods=['GET'])
def get_graph(graph_type):
    data_file = get_data_file()
    with open(data_file, 'r') as f:
        sensor_data = json.load(f)

    if not sensor_data:
        return jsonify({'error': 'No data available to plot'}), 400

    date_label = datetime.now().strftime('%d-%m-%Y')
    graph_file = generate_graph(sensor_data, graph_type, date_label)
    
    if graph_file is None or not os.path.exists(graph_file):
        return jsonify({'error': f'{graph_type} graph not found or failed to generate.'}), 404
    
    return send_file(graph_file, mimetype='image/png')

@app.route('/get-data', methods=['GET'])
def get_data():
    data_file = get_data_file()
    with open(data_file, 'r') as f:
        sensor_data = json.load(f)

    return jsonify(sensor_data), 200

def save_graph(fig, filename):
    path = os.path.join(GRAPH_DIR, filename)
    fig.savefig(path)
    plt.close(fig)
    return path

if __name__ == '__main__':
    initialize_data_storage()
    scheduler.add_job(daily_task, 'cron', hour=0, minute=0)
    scheduler.start()
    app.run(host='0.0.0.0', port=8080)