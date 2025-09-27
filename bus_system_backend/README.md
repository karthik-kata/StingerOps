# Bus System Backend

A Django REST API backend for the Bus System application.

## Features

- **CSV Upload**: Upload classes and stops data via CSV files
- **Bus Management**: Create and manage bus fleet
- **Data Models**: 
  - BusStop: Bus stop locations with routes
  - Class: Class schedules with locations
  - Bus: Individual bus information
  - Route: Bus routes connecting stops

## API Endpoints

### CSV Upload
- `POST /api/csv-upload/upload_csv/` - Upload CSV files
  - Body: `file` (CSV file), `data_type` (classes/stops/general)

### Bus Management
- `GET /api/bus-count/get_bus_count/` - Get current bus count
- `POST /api/bus-count/set_bus_count/` - Set bus count
  - Body: `{"count": number}`

### Data Retrieval
- `GET /api/bus-stops/` - Get all bus stops
- `GET /api/classes/` - Get all classes
- `GET /api/buses/` - Get all buses
- `GET /api/routes/` - Get all routes

### Status
- `GET /api/status/` - API health check

## Setup

1. **Install Dependencies**:
   ```bash
   pip install django djangorestframework django-cors-headers
   ```

2. **Run Migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

3. **Start Server**:
   ```bash
   python manage.py runserver 8000
   ```

## CORS Configuration

The API is configured to accept requests from:
- `http://localhost:3000` (React default)
- `http://localhost:5173-5191` (Vite default ports)

## Database

Uses SQLite by default. Models include:
- **BusStop**: Name, coordinates, routes
- **Class**: Course info, location, schedule
- **Bus**: Bus number, capacity, location
- **Route**: Route name, stops, buses

## Usage

The frontend automatically connects to this API when both servers are running:
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173` (or other Vite port)
