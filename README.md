# Sensor Data and Graphs Server

## Overview

This project is a Flask-based server that collects sensor data, generates graphs, and sends weekly email reports. It includes features for storing data in JSON files, generating graphs from the data, and sending emails with the graph attachments. The server also provides endpoints for submitting data, retrieving graphs, and fetching stored data.

## Features

- Collects and stores sensor data in JSON format.
- Generates graphs based on the sensor data.
- Sends a weekly email report with the generated graphs.
- Provides a web interface to display graphs and input data.
- API endpoints for submitting data, fetching data, and retrieving graphs.

## Requirements

- Docker
- Docker Compose

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/yourrepository.git
    cd yourrepository
    ```

2. Set up email credentials:
    Update the `email_user`, `email_pass`, and `email_receiver` variables in the script with your email credentials.

    ```python
    email_user = "your_email@gmail.com"
    email_pass = "your_app_password"
    email_receiver = "target_user_email@gmail.com"
    ```

3. Build and run the Docker containers:
    ```bash
    docker-compose up --build
    ```

4. **Important**: Update the Nginx `server_name` directive in the `nginx.conf` file with the IP address you want to use.

## Usage

1. Access the web interface:
    Open your browser and go to the IP address you set in the Nginx `server_name` (e.g., `http://your-ip-address`) to view the web interface.

## API Endpoints

### Submit Data

- **Endpoint**: `/submit-data`
- **Method**: `POST`
- **Description**: Submits sensor data to the server.
- **Request Body**:
    ```json
    {
        "Present": true,
        "duration": 10,
        "wet area": true,
        "moisture": 30,
        "last record time duration": 5
    }
    ```

### Get Data

- **Endpoint**: `/get-data`
- **Method**: `GET`
- **Description**: Fetches the stored sensor data.
- **Response**:
    ```json
    [
        {
            "Present": true,
            "duration": 10,
            "wet area": true,
            "moisture": 30,
            "last record time duration": 5,
            "time": "12:00:00"
        },
        ...
    ]
    ```

### Get Graph

- **Endpoint**: `/get-graph/<graph_type>`
- **Method**: `GET`
- **Description**: Retrieves the graph for the specified type.
- **Response**: Returns the graph image.

### Get Email Report

- **Endpoint**: `/get-emailrepo`
- **Method**: `GET`
- **Description**: Sends the weekly email report with the generated graphs.
- **Response**:
    ```json
    {
        "message": "Email sent successfully"
    }
    ```

### Submit Email Address

- **Endpoint**: `/getemail`
- **Method**: `POST`
- **Description**: Receives the user's email address and stores it in a new JSON file.
- **Request Body**:
    ```json
    {
        "email": "emailstr"
    }
    ```

### Fetch Stored Email Address

- **Endpoint**: `/getemail`
- **Method**: `GET`
- **Description**: Fetches the stored email address from the server.
- **Response**:
    ```json
    {
        "email": "emailstr"
    }
    ```

