import smtplib
import os
import json
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import numpy as np
from flask import Flask, request, jsonify, send_file, abort
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import urllib.request as ul
# Email credentials

email_user = "example@gmail.com" #use google app password
email_pass = "password"
email_receiver = "example2@gmail.com"

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

def get_last_week_data():
    last_week_data = []
    today = datetime.now()
    for i in range(7):
        day = today - timedelta(days=i+1)
        filename = os.path.join(DATA_DIR, f'sensor_data_{day.strftime("%d%m%Y")}.json')
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                daily_data = json.load(f)
                last_week_data.extend(daily_data)
    print(f"Collected data for last week: {len(last_week_data)} entries")  # Debugging output
    return last_week_data

def calculate_averages(sensor_data):
    if not sensor_data:
        return None
    
    average_moisture = np.mean([entry['moisture'] for entry in sensor_data])
    average_present = np.mean([1 if entry['Present'] else 0 for entry in sensor_data])
    average_duration = np.mean([entry['duration'] for entry in sensor_data])
    average_last_record_duration = np.mean([entry['last record time duration'] for entry in sensor_data])

    return {
        'average_moisture': average_moisture,
        'average_present': average_present,
        'average_duration': average_duration,
        'average_last_record_duration': average_last_record_duration
    }

def weekly_task():
    logging.debug("prepare weekly report")
    
    today = datetime.now()
    graph_files = []
    last_week_data = get_last_week_data()
    averages = calculate_averages(last_week_data)
    for i in range(7):
        day = today - timedelta(days=i+1)
        date_str = day.strftime('%d%m%Y')
        filename = os.path.join(DATA_DIR, f'sensor_data_{date_str}.json')
        
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                daily_data = json.load(f)
                if daily_data:
                    graph_file = generate_combined_graph(daily_data, date_str)
                    graph_files.append(graph_file)

    send_email_with_averages_and_graph(averages, graph_files)


def generate_combined_graph(sensor_data, date_label):
    times = [entry['time'] for entry in sensor_data]
    fig, axs = plt.subplots(4, 1, figsize=(10, 15))

    data_map = {
        'Moisture': [entry['moisture'] for entry in sensor_data],
        'Present': [1 if entry['Present'] else 0 for entry in sensor_data],
        'Duration': [entry['duration'] for entry in sensor_data],
        'Last Record Duration': [entry['last record time duration'] for entry in sensor_data],
    }

    for ax, (label, y_data) in zip(axs, data_map.items()):
        ax.plot(times, y_data, marker='o')
        ax.set_title(f'{label} Over Time - {date_label}')
        ax.set_xlabel('Time')
        ax.set_ylabel(label)
        ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    graph_file = f'combined_graph_{date_label}.png'
    fig.savefig(graph_file)
    plt.close(fig)
    return graph_file

def send_email_with_averages_and_graph(averages,graph_files):
    if read_email()!=None:
        email_addr = read_email()
    else:
        email_addr = email_receiver
    logging.debug(read_email())
    logging.debug(email_addr)
    msg = MIMEMultipart()
    msg['From'] = email_user
    msg['To'] = email_addr
    msg['Subject'] = 'Weekly Sensor Data Summary'

    body = (
        f"Weekly Averages:\n"
        f"Average Moisture: {averages['average_moisture']:.2f}\n"
        f"Average Present Times per Day: {averages['average_present']:.2f}\n"
        f"Average Duration: {averages['average_duration']:.2f}\n"
        f"Average Last Record Time Duration: {averages['average_last_record_duration']:.2f}\n"
    )
    msg.attach(MIMEText(body, 'plain'))

    for graph_file in graph_files:
        with open(graph_file, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename= {graph_file}')
            msg.attach(part)

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(email_user, email_pass)
            server.send_message(msg)
            logging.debug("report sent")
    except Exception as e:
        print(f"Failed to send email: {e}")

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

@app.route('/get-emailrepo',methods=['GET'])
def send_email():
    weekly_task()
    return jsonify({'message': 'Email sent successfully'})

@app.route('/getemail', methods=['POST', 'GET'])
def get_email():
    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        if 'email' not in data or not isinstance(data['email'], str):
            return jsonify({'error': 'Invalid data format. Expected {"email": "emailstr"}'}), 400

        email_data_file = os.path.join('email_data.json')
        with open(email_data_file, 'w') as f:
            json.dump(data, f, indent=4)

        return jsonify({'message': 'Email received and stored successfully'}), 201

    elif request.method == 'GET':
        email_data_file = os.path.join('email_data.json')
        if not os.path.exists(email_data_file):
            return jsonify({'email': ''}), 200

        with open(email_data_file, 'r') as f:
            email_data = json.load(f)

        return jsonify(email_data), 200

def read_email(): 
    email_data_file = os.path.join('email_data.json') 
    if os.path.exists(email_data_file): 
        with open(email_data_file, 'r') as f:
            data = json.load(f) 
            logging.debug(data.get('email'))
            return data.get('email') 
    return None

def save_graph(fig, filename):
    path = os.path.join(GRAPH_DIR, filename)
    fig.savefig(path)
    plt.close(fig)
    return path

if __name__ == '__main__':
    initialize_data_storage()
    scheduler.add_job(daily_task, 'cron', hour=0, minute=0)            #updata data 
    scheduler.add_job(weekly_task, 'cron', day_of_week='sun', hour=20, minute=0)    #Sunday 8.00pm sent report
    scheduler.start()
    app.run(host='0.0.0.0', port=8080,debug=True)