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

email_user = "example@gmail.com"  #the agent robot's account to send email to user, use App passkey provided by Google to login
email_pass = "password"   #App passkey
email_receiver = "example2@gmail.com"  #the user's email
OpenR_API ='1252523523525252525252'

#file store path
DATA_DIR = 'data'
GRAPH_DIR = 'graphs'
EMAIL_DIR = 'email_data'
UPLOAD_FOLDER = 'uploads'
UPLOAD_S_FOLDER = 'uploads_s'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

REPORT_PRO = "prompt/report.txt"
CAP_PRO = 'prompt/CapAnalyzePrompt.txt'


offline = True
if offline:
    import ollama
    TEXT_MODEL = 'llama3.1:8b'
    IMAGE_MODEL = 'llama3.2-vision:11b'
else:
    from openai import OpenAI
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OpenR_API,
    )
    TEXT_MODEL = "deepseek/deepseek-chat-v3-0324:free"
    IMAGE_MODEL = "qwen/qwen2.5-vl-72b-instruct:free"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_S_FOLDER, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(GRAPH_DIR, exist_ok=True)

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_S_FOLDER'] = UPLOAD_S_FOLDER
scheduler = BackgroundScheduler()

HOST = '0.0.0.0'   #public ip for image desc
PORT = 8080
#get the current day to find the file 
def get_data_file():
    today = datetime.now().strftime('%d%m%Y')
    return os.path.join(DATA_DIR, f'sensor_data_{today}.json')

#init new file
def initialize_data_storage():
    data_file = get_data_file()
    if not os.path.exists(data_file):
        with open(data_file, 'w') as f:
            json.dump([], f)

#auto exe task
def daily_task():
    initialize_data_storage()

#get and read the whole week's data
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
    print(f"Collected data for last week: {len(last_week_data)} entries") 
    return last_week_data


def calculate_averages(sensor_data):
    # Filter out None values for each field
    moisture_values = [entry['moisture'] for entry in sensor_data if entry['moisture'] is not None]
    present_values = [1 if entry['Present'] else 0 for entry in sensor_data if entry['Present'] is not None]
    duration_values = [entry['duration'] for entry in sensor_data if entry['duration'] is not None]
    temperature_values = [entry['temperature'] for entry in sensor_data if entry['temperature'] is not None]

    average_moisture = np.mean(moisture_values) if moisture_values else 0
    average_present = np.mean(present_values) if present_values else 0
    average_duration = np.mean(duration_values) if duration_values else 0
    average_temperature = np.mean(temperature_values) if temperature_values else 0

    return {
        'average_moisture': average_moisture,
        'average_present': average_present,
        'average_duration': average_duration,
        'average_temperature': average_temperature,
    }

#include sending a weekly report to the user
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

    send_email_with_averages_and_graph(averages, graph_files,email_user,email_pass,email_receiver)

#make graphes by the data collected
def generate_graph(sensor_data, graph_type, date_label):
    times = [entry['time'] for entry in sensor_data]
    data_map = {
        'duration': [entry['duration'] for entry in sensor_data],
        'moisture': [entry['moisture'] for entry in sensor_data],
        'present': [1 if entry['Present'] else 0 for entry in sensor_data],
        'wet_area': [1 if entry['wet area'] else 0 for entry in sensor_data],
        'temperature': [entry['temperature'] for entry in sensor_data],
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

#combine those graph
def generate_combined_graph(sensor_data, date_label, folder_path='graphs-day'):
    os.makedirs(folder_path, exist_ok=True)
    times = [entry['time'] for entry in sensor_data]
    fig, axs = plt.subplots(4, 1, figsize=(10, 15))

    data_map = {
        'Moisture': [entry['moisture'] for entry in sensor_data],
        'Present': [1 if entry['Present'] else 0 for entry in sensor_data],
        'Duration': [entry['duration'] for entry in sensor_data],
        'Temperature': [entry['temperature'] for entry in sensor_data],
    }

    for ax, (label, y_data) in zip(axs, data_map.items()):
        ax.plot(times, y_data, marker='o')
        ax.set_title(f'{label} Over Time - {date_label}')
        ax.set_xlabel('Time')
        ax.set_ylabel(label)
        ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    graph_file = os.path.join(folder_path, f'combined_graph_{date_label}.png')
    fig.savefig(graph_file)
    plt.close(fig)
    return graph_file

#send email procedure
def send_email_with_averages_and_graph(averages, graph_files, email_user, email_pass, email_receiver):
    email_addr = read_email() or email_receiver
    logging.debug(email_addr)
    msg = MIMEMultipart()
    msg['From'] = email_user
    msg['To'] = email_addr
    msg['Subject'] = 'Weekly Sensor Data Summary'

    body = (LLM_intergated_Report())
    msg.attach(MIMEText(body, 'plain'))

    for graph_file in graph_files:
        with open(graph_file, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename= {os.path.basename(graph_file)}')
            msg.attach(part)

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(email_user, email_pass)
            server.send_message(msg)
            logging.debug("Report sent")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
    
#check file valid
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#Load content from a text file.
def load_content_from_file(filepath: str) -> str:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File '{filepath}' not found.")
    with open(filepath, 'r',encoding="utf-8") as file:
        return file.read()


#the server thread-----------------------------------------



#for the client uploading new photoes
@app.route('/upload-photo/<type>', methods=['POST'])
def upload_photo(type):
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if type != '0' and type != '1': 
        return jsonify({'error': 'wrong type'}), 400
    
    if file and allowed_file(file.filename):
        now = datetime.now()
        formatted_time = now.strftime("%S%M%H_%d%m%y")
        filename = f"recentcap_{formatted_time}.jpg"
        if type == '0':
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            del_oldest_photo(app.config['UPLOAD_FOLDER'])
            return jsonify({'message': 'File uploaded successfully'}), 201
        elif type == '1':
            file.save(os.path.join(app.config['UPLOAD_S_FOLDER'], filename))
            del_oldest_photo(app.config['UPLOAD_S_FOLDER'])
            return jsonify({'message': 'File uploaded successfully'}), 201
    else:
        return jsonify({'error': 'Invalid file type'}), 400

#for the client getting the latest photoes
@app.route('/get_recphoto/<type>', methods=['GET'])
def get_recphoto(type):
    if type != '0' and type != '1': 
        return jsonify({'error': 'wrong type'}), 400
    
    try:
        if type == '0':
            add = app.config['UPLOAD_FOLDER']
        elif type == '1':
            add = app.config['UPLOAD_S_FOLDER']
        i,j = findNearestPho(add)
        if i:
            return send_file(i, download_name=j, as_attachment=False)
        else:
            return jsonify({'error': 'No files available'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def del_oldest_photo(Path):
    if len(os.listdir(Path)) > 10:
        add = findOldestPho(Path)
        os.remove(add)


def findNearestPho(Path):
    files = os.listdir(Path)
    files = sorted(files, key=lambda x: os.path.getmtime(os.path.join(Path, x)), reverse=True)
    most_recent_file = files[0] if files else None
    return os.path.join(Path, most_recent_file),most_recent_file

def findOldestPho(Path):
    files = os.listdir(Path)
    files = sorted(files, key=lambda x: os.path.getmtime(os.path.join(Path, x)), reverse=True)
    most_recent_file = files[-1] if files else None
    return os.path.join(Path, most_recent_file)

#main webpage    
@app.route('/', methods=['GET'])
def serve_html():
    try:
        return send_file("graph.html")
    except Exception as e:
        logging.error("Error serving HTML: %s", e)
        abort(500, "Internal server error")

#main webpage for mobile devices   
@app.route('/phone', methods=['GET'])
def serve_html_phone():
    try:
        return send_file("graphphone.html")
    except Exception as e:
        logging.error("Error serving HTML: %s", e)
        abort(500, "Internal server error")

#upload new sensor data
@app.route('/submit-data', methods=['POST'])
def submit_data():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    expected_keys = {"Present", "duration", "wet area", "moisture","temperature", "no. of faeces"}

    if not expected_keys.issubset(data.keys()):
        return jsonify({'error': 'Invalid data format'}), 400

    now = datetime.now()
    data['time'] = now.strftime('%H:%M:%S')

    data_file = get_data_file()
    with open(data_file, 'r+') as f:
        sensor_data = json.load(f)

        # Find the most recent record where "Present" is true
        last_present_time = None
        for record in reversed(sensor_data):
            if record['Present']:
                last_present_time = datetime.strptime(record['time'], '%H:%M:%S')
                break

        # Calculate the last record time duration
        if last_present_time:
            if data['Present']:
                last_record_duration = 0
            else:
                last_record_datetime = datetime.combine(now.date(), last_present_time.time())
                time_diff = now - last_record_datetime
                last_record_duration = time_diff.total_seconds() / 60  # Convert seconds to minutes      
        else:
            last_record_duration = 0

        data['last record time duration'] = last_record_duration
        data['frequency'] = len(sensor_data) + 1
        sensor_data.append(data)
        f.seek(0)
        json.dump(sensor_data, f, indent=4)

    return jsonify({'message': 'Data saved successfully'}), 201



#get a specific graph
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

#check the usage of the cat toilet
@app.route('/get-lastgone', methods=['GET'])
def sendpasstime():
    time = getpasstime()
    frequency =  getfequency()
    return jsonify({"last record time duration":time,"frequency":frequency})

#count the number of use of the toilet
def getfequency():
    data_file = get_data_file()
    with open(data_file, 'r+') as f:
            return json.load(f)[-1]["frequency"]
            
#cal the time separation
def getpasstime():
    now = datetime.now()
    data_file = get_data_file()
    with open(data_file, 'r+') as f:
            sensor_data = json.load(f)
            last_present_time = None
            for record in reversed(sensor_data):
                if record['Present']:
                    last_present_time = datetime.strptime(record['time'], '%H:%M:%S')
                    break

            if last_present_time:
                last_record_datetime = datetime.combine(now.date(), last_present_time.time())
                time_diff = now - last_record_datetime
                last_record_duration = time_diff.total_seconds() / 60   
            return last_record_duration
            
#get the history data
@app.route('/get-data', methods=['GET'])
def get_data():
    data_file = get_data_file()
    with open(data_file, 'r') as f:
        sensor_data = json.load(f)
    if len(sensor_data)>1:
        return jsonify(sensor_data[-1]), 200
    else:
        return jsonify({'message': 'no data here'}), 200



#get and upload the user's email address
@app.route('/getemail', methods=['POST', 'GET'])
def get_email():
    email_folder = EMAIL_DIR
    os.makedirs(email_folder, exist_ok=True)
    email_data_file = os.path.join(email_folder, 'email_data.json')

    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        if 'email' not in data or not isinstance(data['email'], str):
            return jsonify({'error': 'Invalid data format. Expected {"email": "emailstr"}'}), 400

        with open(email_data_file, 'w') as f:
            json.dump(data, f, indent=4)

        return jsonify({'message': 'Email received and stored successfully'}), 201

    elif request.method == 'GET':
        if not os.path.exists(email_data_file):
            return jsonify({'email': ''}), 200

        with open(email_data_file, 'r') as f:
            email_data = json.load(f)

        return jsonify(email_data), 200

#send email report immediately
@app.route('/get-emailrepo',methods=['GET'])
def send_email():
    weekly_task()
    return jsonify({'message': 'Email sent successfully'})

#send email reminder immediately
@app.route('/email_reminder/<default_sin_ID>', methods=['GET'])
def email_reminder(default_sin_ID):
    if default_sin_ID == "1":
        LongNoUseWarning()
        return jsonify({'message': 'LongNoUseWarning execute successfully'})
    elif default_sin_ID == "2":
        TooDirtyWarning()
        return jsonify({'message': 'idk execute successfully'})

    return jsonify({'error': 'no corresponding ID'})

#generate a report by LLM model
def LLM_intergated_Report():
    # Collect the last week's sensor data
    last_week_data = get_last_week_data()
    averages = calculate_averages(last_week_data)

    # Prepare the summary of data to send to the LLM
    summary = (
        f"Weekly Data Summary:\n"
        f"- Average Moisture: {averages['average_moisture']:.2f}\n"
        f"- Average Present Times per Day: {averages['average_present']:.2f}\n"
        f"- Average Duration: {averages['average_duration']:.2f}\n"
        f"- Average Temperature: {averages['average_temperature']:.2f}\n"
    )
    messages=[
            {
                'role': 'system',
                'content': load_content_from_file(REPORT_PRO)
            },
            {
                'role': 'user',
                'content': get_image_descri()
            },
            {
                'role': 'user',
                'content': summary
            }
            ]
    print(messages)
    if offline:
        response = ollama.chat(model=TEXT_MODEL, messages=messages)
        generated_report = response['message']['content']
    else:
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "<YOUR_SITE_URL>", # Optional. Site URL for rankings on openrouter.ai.
                "X-Title": "<YOUR_SITE_NAME>", # Optional. Site title for rankings on openrouter.ai.
            },
            extra_body={},
            model=TEXT_MODEL,
            messages=messages
            )
        generated_report = completion.choices[0].message.content
    print(generated_report)
    return generated_report


def get_image_descri():
    if offline:
        try:
            cap_path,i = findNearestPho(app.config['UPLOAD_S_FOLDER'])
            print(cap_path)
            content = load_content_from_file(CAP_PRO)
            print(content)
            response = ollama.chat(
                model= IMAGE_MODEL,
                messages=[{
                    'role': 'user',
                    'content': content,
                    'images': [cap_path]
                }]
            )
            print(response['message']['content'])
            return response['message']['content']
        except FileNotFoundError:
            logging.error(f"Cap analysis prompt file or image '{cap_path}' not found.")
            return "No image description available."
        except Exception as e:
            logging.error(f"Error during cap analysis: {e}")
            return "Error analyzing image."
    else:
        completion = client.chat.completions.create(
        extra_headers={
            "HTTP-Referer": "<YOUR_SITE_URL>", # Optional. Site URL for rankings on openrouter.ai.
            "X-Title": "<YOUR_SITE_NAME>", # Optional. Site title for rankings on openrouter.ai.
        },
        extra_body={},
        model=IMAGE_MODEL,
        messages=[
            {
            "role": "user",
            "content": [
                {
                "type": "text",
                "text": "this is the image of cat's faeces. you should try to describe the shape, appearence and color for medical use. you response should only contain the answer"
                },
                {
                "type": "image_url",
                "image_url": {
                    "url": f"http://{HOST}:{PORT}/get_recphoto/1"
                }
                }
            ]
            }
        ]
        )
    return completion.choices[0].message.content
        
#emergency
def TooDirtyWarning():
    # Example function to send the report via email
    email_addr = read_email() or email_receiver
    msg = MIMEMultipart()
    msg['From'] = email_user
    msg['To'] = email_addr
    msg['Subject'] = 'Attention:  Cat Toilet Needs Immediate Cleaning!'
    body = (
        "I wanted to bring to your attention that the cat toilet has become quite dirty and needs immediate cleaning. It’s important for the health and comfort of our cat to maintain a clean environment."
    )
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(email_user, email_pass)
            server.send_message(msg)
            logging.debug("Report sent successfully")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

#emergency 
def LongNoUseWarning():
    email_addr = read_email() or email_receiver
    logging.debug(email_addr)
    msg = MIMEMultipart()
    msg['From'] = email_user
    msg['To'] = email_addr
    msg['Subject'] = "Attention: The cat hasn't used the toilet for two hours!"
    body = (
        f"It has been {round(getpasstime()/60,1)} hour(s) since your cat last used the toilet. It's important to monitor your pet's habits to ensure their health and well-being. Please check on your cat to make sure everything is alright."
    )
    msg.attach(MIMEText(body, 'plain'))
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(email_user, email_pass)
            server.send_message(msg)
            logging.debug("Report sent")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

#count the time pass of last toilet time
def checktimepast():
    if getpasstime() >= 120 and getpasstime() <= 130:
        email_reminder("1")

#get the email address
def read_email(): 
    email_data_file = os.path.join(EMAIL_DIR,'email_data.json') 
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



#init everything
if __name__ == '__main__':
    initialize_data_storage()
    scheduler.add_job(daily_task, 'cron', hour=0, minute=0)            #updata data 
    scheduler.add_job(weekly_task, 'cron', day_of_week='sun', hour=20, minute=0)    #every Sunday 8.00pm sent report
    scheduler.add_job(checktimepast, 'interval', minutes=10)
    scheduler.start()
    app.run(host=HOST, port=PORT,debug=True)