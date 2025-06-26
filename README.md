# MeowAi - Smart Litter Box Monitoring System

This project is a comprehensive sensor data monitoring system using Flask, Nginx, and Docker. It collects, processes, and visualizes cat litter box sensor data, providing valuable insights through automated reports.

## Features

- **Data Collection**: Collects sensor data including moisture, presence detection, duration, temperature, and waste detection
- **AI-Powered Analysis**: Uses llama3 models for intelligent report generation and image analysis
- **Data Visualization**: Generates graphs to visualize sensor data trends over time
- **Automated Reporting**: Sends weekly reports via email with data summaries and graphs
- **Photo Monitoring**: Allows uploading and retrieving photos of the litter box
- **Email Notifications**: Sends reminders and alerts based on sensor data analysis
- **Responsive UI**: Works on both desktop and mobile devices

## System Architecture

```
├── app.py                # Main Flask application
├── Dockerfile            # Flask app container configuration
├── Dockerfile-nginx      # Nginx container configuration
├── docker-compose.yml    # Orchestration configuration
├── nginx.conf            # Nginx server configuration
├── requirements.txt      # Python dependencies
├── graph.html            # Desktop dashboard UI
├── graphphone.html       # Mobile dashboard UI
├── data/                 # Sensor data storage
├── graphs/               # Generated graph images
├── email_data/           # User email storage
├── uploads/              # Uploaded litter box photos
├── uploads_s/            # Uploaded waste photos for analysis
├── prompt/               # LLM prompt templates
└── README.md             # Project documentation
```

## Requirements

- Docker
- Docker Compose
- Ollama (with required models)
- Google App Password for email

## Setup & Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/meowai.git
   cd meowai
   ```

2. **Install Ollama Models**
   ```bash
   ollama pull llama3.1:8b
   ollama pull llama3.2-vision:11b
   ```

3. **Configure Email Settings**
   Edit `app.py` with your email credentials:
   ```python
   email_user = "your-email@gmail.com"  # Use Google App Password
   email_pass = "your-app-password"
   email_receiver = "default-receiver@gmail.com"
   ```

4. **Configure Nginx**
   Edit `nginx.conf`:
   ```nginx
   server_name your-domain.com;  # Or your server IP
   ```

5. **Build and Launch**
   ```bash
   docker-compose up --build -d
   ```

## Accessing the System

- **Web Interface**: `http://your-domain.com:8080` (desktop) or `http://your-domain.com:8080/phone` (mobile)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/upload-photo/<type>` | POST | Upload litter box (0) or waste (1) photos |
| `/get_recphoto/<type>` | GET | Get latest litter box (0) or waste (1) photo |
| `/submit-data` | POST | Submit sensor data (JSON) |
| `/get-graph/<type>` | GET | Get graph image (duration, moisture, etc) |
| `/get-data` | GET | Get latest sensor data |
| `/get-emailrepo` | GET | Trigger immediate email report |
| `/getemail` | POST/GET | Set/Get user email address |
| `/email_reminder/<id>` | GET | Trigger reminder (1=no-use, 2=cleaning) |

## Graph Types

- `duration`: Usage duration in seconds
- `moisture`: Moisture percentage
- `present`: Presence detection
- `wet_area`: Wet area detection
- `temperature`: Temperature in Celsius
- `no. of faeces`: number of faeces

## Customization

1. **LLM Models**: 
   - Edit `TEXT_MODEL` and `IMAGE_MODEL` in `app.py`
   - Set `offline = False` to use OpenRouter instead of Ollama

2. **Report Prompts**:
   - Modify `prompt/report.txt` for weekly report format
   - Modify `prompt/CapAnalyzePrompt.txt` for waste analysis

3. **Scheduling**:
   - Edit `weekly_task` cron settings in `app.py`:
   ```python
   scheduler.add_job(weekly_task, 'cron', day_of_week='sun', hour=20, minute=0)
   ```

## Troubleshooting

1. **Email Not Sending**:
   - Verify Google App Password is correct
   - Check Less Secure Apps access in Google account
   - Check Docker logs: `docker-compose logs flask`

2. **Photo Upload Issues**:
   - Verify directory permissions: `chmod -R 755 uploads/`
   - Check allowed file types: `ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}`

3. **LLM Analysis Failures**:
   - Confirm models are downloaded: `ollama list`
   - Check prompt files exist in `prompt/` directory

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.
