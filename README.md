# Sensor Data Monitoring System

This project is a comprehensive sensor data monitoring system using Flask, Nginx, and Docker. It collects, processes, and visualizes sensor data, providing valuable insights through automated reports.

## Features

- **Data Collection**: Collects sensor data such as moisture, presence, duration, and temperature.
- **Data Visualization**: Generates graphs to visualize sensor data trends over time.
- **Automated Reporting**: Sends weekly reports via email with data summaries and graphs.
- **LLM Generated Report**: The report sent to the user weekly is analyzed by llama3.1:8B.
- **Photo Upload**: Allows uploading and retrieving recent photos.
- **Email Notifications**: Sends reminders and alerts based on sensor data analysis.

## Requirements

- Python 3.9
- Docker
- Docker Compose
- Ollama

## Setup

1. **Clone the Repository**
   
   ```bash
   git clone https://github.com/yourusername/your-repo-name.git
   cd your-repo-name
   ```

3. **Environment Variables**
   
   Ensure you have your email credentials set up in `app.py` for sending emails:
   ```python
   email_user = "your-email@gmail.com"    #created by gmail app password
   email_pass = "your-email-password"
   email_receiver = "receiver-email@gmail.com"
   ```

4. **Build and Run Docker Containers**
   
   Use Docker Compose to build and run the containers:
   ```bash
   docker-compose up --build
   ```

5. **Access the Application**
   
   - The Flask application will be available at `http://localhost:8080`.
   - The Nginx server will proxy requests at `http://localhost`.
   - Configure the nginx.conf, set server_name to the address you want to use.
     
## UI

- **UI**: `http://Youraddress:8080`
  
## API Endpoints

- **Upload Photo**: `POST /upload-photo`
- **Get Recent Photo**: `GET /get_recphoto`
- **Submit Sensor Data**: `POST /submit-data`
- **Get Graph**: `GET /get-graph/<graph_type>`
- **Get Data**: `GET /get-data`
- **Send Email Report**: `GET /get-emailrepo`
- **Set/Get Email**: `POST/GET /getemail`
- **Email Reminder**: `GET /email_reminder/<default_sin_ID>`

## Graph Types

- `duration`
- `moisture`
- `present`
- `wet_area`
- `temperature`

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

