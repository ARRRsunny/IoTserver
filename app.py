from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import matplotlib.pyplot as plt
import os
import json
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import os
import urllib.request as ul
import logging
from flask import Flask, jsonify, abort, send_file
DATA_DIR = 'data'
GRAPH_DIR = 'graphs'

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(GRAPH_DIR, exist_ok=True)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

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
        url = "https://raw.githubusercontent.com/ARRRsunny/music-player/refs/heads/main/musicplayer_server.html"
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

def generate_individual_graphs(sensor_data, date_label):
    times = [entry['time'] for entry in sensor_data]
    graph_files = []

    # Ensure the graph directory exists
    os.makedirs(GRAPH_DIR, exist_ok=True)

    # Duration graph
    durations = [entry['duration'] for entry in sensor_data]
    fig = plt.figure()
    plt.plot(times, durations, marker='o', label='Duration (s)')
    plt.title(f'Duration Over Time - {date_label}')
    plt.xlabel('Time')
    plt.ylabel('Duration (seconds)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    duration_graph = save_graph(fig, 'duration_graph.png')
    graph_files.append(duration_graph)

    # Moisture graph
    moistures = [entry['moisture'] for entry in sensor_data]
    fig = plt.figure()
    plt.plot(times, moistures, marker='x', color='r', label='Moisture')
    plt.title(f'Moisture Over Time - {date_label}')
    plt.xlabel('Time')
    plt.ylabel('Moisture')
    plt.xticks(rotation=45)
    plt.tight_layout()
    moisture_graph = save_graph(fig, 'moisture_graph.png')
    graph_files.append(moisture_graph)

    # Present graph
    presents = [1 if entry['Present'] else 0 for entry in sensor_data]
    fig = plt.figure()
    plt.plot(times, presents, marker='s', color='g', label='Present')
    plt.title(f'Presence Over Time - {date_label}')
    plt.xlabel('Time')
    plt.ylabel('Present (1=True, 0=False)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    present_graph = save_graph(fig, 'present_graph.png')
    graph_files.append(present_graph)

    # Wet area graph
    wet_areas = [1 if entry['wet area'] else 0 for entry in sensor_data]
    fig = plt.figure()
    plt.plot(times, wet_areas, marker='d', color='b', label='Wet Area')
    plt.title(f'Wet Area Over Time - {date_label}')
    plt.xlabel('Time')
    plt.ylabel('Wet Area (1=True, 0=False)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    wet_area_graph = save_graph(fig, 'wet_area_graph.png')
    graph_files.append(wet_area_graph)

    # Last record time duration graph
    last_record_durations = [entry['last record time duration'] for entry in sensor_data]
    fig = plt.figure()
    plt.plot(times, last_record_durations, marker='^', color='m', label='Last Record Time')
    plt.title(f'Last Record Time Duration Over Time - {date_label}')
    plt.xlabel('Time')
    plt.ylabel('Duration (hours)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    last_record_graph = save_graph(fig, 'last_record_duration_graph.png')
    graph_files.append(last_record_graph)

    return graph_files

@app.route('/generate-graphs', methods=['GET'])
def generate_graphs():
    data_file = get_data_file()
    with open(data_file, 'r') as f:
        sensor_data = json.load(f)
    
    if not sensor_data:
        return jsonify({'error': 'No data available to plot'}), 400

    date_label = datetime.now().strftime('%d-%m-%Y')
    graph_files = generate_individual_graphs(sensor_data, date_label)
    return jsonify({'message': 'Graphs generated successfully', 'graphs': graph_files}), 200

@app.route('/get-graph/<graph_type>', methods=['GET'])
def get_graph(graph_type):
    graph_file = f'{graph_type}_graph.png'
    if not os.path.exists(graph_file):
        return jsonify({'error': f'{graph_type} graph not found. Generate it first.'}), 404
    
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
    app.run(host="192.168.194.251",port=8080,debug=True)
