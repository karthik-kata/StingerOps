# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

TBD is a HackGT project featuring a Georgia Tech Bus System with AI-powered guidance through **Cedar OS integration**. The project consists of a React + Vite frontend with Google Maps integration, a Django REST API backend for data management, and **Stinger route optimization engine** for intelligent bus route planning.

### Key Technologies
- **Frontend**: React 18 + Vite (using Rolldown), Tailwind CSS, Framer Motion
- **AI Integration**: Cedar OS with OpenAI GPT-4 support
- **Maps**: Google Maps JavaScript API
- **Backend**: Django REST Framework with SQLite
- **Route Optimization**: Stinger - Python-based optimization engine using hub-and-spoke algorithms
- **CSV Processing**: Papa Parse for client-side processing

## Development Commands

### Frontend Development
```bash
# Install dependencies
npm install

# Start development server (default: http://localhost:5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linter
npm run lint
```

### Backend Development
```bash
# Navigate to backend directory
cd bus_system_backend

# Install Python dependencies
pip install django djangorestframework django-cors-headers pandas numpy

# Apply database migrations
python manage.py makemigrations
python manage.py migrate

# Start Django development server (http://localhost:8000)
python manage.py runserver 8000

# Create superuser for admin access
python manage.py createsuperuser
```

### Route Optimization (Stinger)
```bash
# Navigate to stinger directory
cd stinger

# Install required packages
pip install pandas numpy

# Run demand distribution algorithm
python nearest_stops_demand.py

# Run route optimization with default parameters
python tlpf_ktransfers.py

# Run with custom parameters (example)
python tlpf_ktransfers.py --fleet 15 --target-lines 10 --algorithm both
```

### Running Both Services
The application requires both frontend and backend servers running simultaneously:
1. **Backend**: `python manage.py runserver 8000` (in `bus_system_backend/`)
2. **Frontend**: `npm run dev` (in root directory)
3. **Route Optimization**: Run Stinger algorithms as needed (in `stinger/` directory)

## Architecture Overview

### Frontend Architecture
- **App.jsx**: Main application component managing state and CSV upload workflow
- **GoogleMap.jsx**: Google Maps integration with marker rendering for stops/classes
- **CedarGuide.jsx**: Cedar OS AI integration providing intelligent assistance
- **api.js**: Centralized API client for backend communication
- **FallbackMap.jsx**: Fallback when Google Maps fails to load

### Backend Architecture
- **Django Models**: `Building`, `BusStop`, `Course`, `ClassSession`, `Bus`, `Route`, `RouteStop`, `RouteAssignment`
- **ViewSets**: RESTful API endpoints with custom actions for CSV upload and bus management
- **Services**: `CSVProcessingService`, `BusManagementService`, `RouteService`, `AnalyticsService`
- **CORS Configuration**: Allows requests from Vite dev servers (ports 5173-5191)

### Route Optimization Architecture (Stinger)
- **nearest_stops_demand.py**: Distributes building demand across nearest bus stops using euclidean distance
- **tlpf_ktransfers.py**: Main route optimization engine with multiple algorithms:
  - **Hub-and-Spoke Model**: Creates efficient routes connecting high-demand destinations
  - **Demand-Driven Optimization**: Prioritizes routes based on actual usage patterns
  - **K-Transfer Routing**: Calculates optimal paths with transfer penalties
  - **Iterative Improvement**: Refines route selection through multiple optimization passes

### Data Flow
1. **CSV Upload**: Files processed both client-side (Papa Parse) and server-side (Django)
2. **Route Optimization Pipeline**: 
   - Frontend CSV data → Stinger algorithms → Optimized routes → Django backend
   - Building/demand data processed by `nearest_stops_demand.py`
   - Route optimization performed by `tlpf_ktransfers.py`
   - Results modeled and stored in Django Route/RouteStop models
3. **State Management**: React state synchronized with Django backend via API calls
4. **AI Integration**: Cedar OS provides context-aware assistance with access to app state
5. **Map Rendering**: Google Maps displays optimized routes with custom markers and route lines

### Cedar OS Integration
The project implements **real Cedar OS** (not custom implementation):
- **CedarCopilot Component**: Official Cedar OS React component
- **AI Provider**: OpenAI GPT-4 with bus system context
- **State Access**: AI can read/modify app state (csvData, classesData, stopsData, busCount)
- **Actions**: AI can trigger CSV uploads and bus count changes
- **Configuration**: `cedar.config.js` defines AI capabilities and UI settings

## Environment Setup

### Required Environment Variables
```bash
# Frontend (.env)
VITE_OPENAI_API_KEY=your_openai_api_key_here
VITE_GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
```

### Configuration Files
- **cedar.config.js**: Cedar OS AI configuration with system actions
- **vite.config.js**: Vite build configuration with React plugin
- **tailwind.config.js**: Tailwind CSS configuration
- **eslint.config.js**: ESLint rules for code quality

## API Endpoints

### CSV Upload
- `POST /api/csv-upload/` - Upload CSV files with data_type parameter
- **Planned**: `POST /api/route-optimization/` - Trigger Stinger optimization with uploaded data

### Bus Management  
- `GET /api/bus-count/` - Get current active bus count
- `POST /api/bus-count/` - Set number of buses
- **Planned**: `POST /api/buses/` - Create/update bus fleet

### Data Retrieval
- `GET /api/buildings/` - Get all buildings
- `GET /api/bus-stops/` - Get all bus stops
- `GET /api/courses/` - Get all courses
- `GET /api/class-sessions/` - Get all class sessions  
- `GET /api/buses/` - Get all buses
- `GET /api/routes/` - Get all optimized routes with stops
- `GET /api/route-assignments/` - Get bus-to-route assignments
- `GET /api/system-overview/` - Get analytics and system health
- `GET /api/status/` - API health check

### Route Optimization (Planned Django Integration)
- `POST /api/optimize-routes/` - Run Stinger optimization on current data
- `GET /api/optimization-results/{job_id}/` - Get optimization results
- `POST /api/routes/{route_id}/apply/` - Apply optimized route to system

## CSV Data Formats

### Bus Stops CSV
Required columns: `stop_name`, `stop_lat`, `stop_lon`
Optional: `routes_serving`, `capacity`, `has_shelter`

### Buildings CSV (for Stinger optimization)
Required columns: `building_name`, `demand`, `latitude`, `longitude`
Used by `nearest_stops_demand.py` for demand distribution

### Sources CSV (for Stinger optimization)
Required columns: `source_name`, `latitude`, `longitude`, `demand`
Represents origin points (dorms, parking) with passenger demand

### Classes CSV  
Required columns: `name`, `course_code`, `building`, `room`, `latitude`, `longitude`, `start_time`, `end_time`, `days`

### General CSV
Flexible format - automatically detects location columns (`lat`/`latitude`, `lng`/`longitude`)

## Development Notes

### Testing Cedar OS Integration
- Set `VITE_OPENAI_API_KEY` in environment to test AI features
- Cedar OS actions defined in `cedar.config.js` allow AI to:
  - Upload CSV files (`upload_csv` action)
  - Modify bus count (`set_bus_count` action)
  - **Planned**: Trigger route optimization (`optimize_routes` action)
  - Access current data state

### Google Maps Integration
- Requires `VITE_GOOGLE_MAPS_API_KEY` for map functionality
- FallbackMap.jsx provides graceful degradation when Maps API unavailable
- Supports custom markers for different data types (stops, classes, general locations)
- **Planned**: Route line rendering for optimized bus routes

### Route Optimization Integration
- Stinger algorithms process CSV data from frontend
- `nearest_stops_demand.py` creates `stops_with_demand.csv`
- `tlpf_ktransfers.py` generates optimized route solutions
- **Django Integration Needed**:
  - API endpoints to trigger Stinger algorithms
  - Background task processing for optimization
  - Data models to store optimization results
  - Service layer to bridge Stinger output with Django models

### Stinger Algorithm Parameters
- `--fleet`: Number of available buses (default: 12)
- `--target-lines`: Maximum number of routes to generate (default: 12)
- `--k-transfers`: Maximum transfers allowed (default: 2)
- `--transfer-penalty`: Time penalty for transfers in minutes (default: 5.0)
- `--speed-kmh`: Average bus speed (default: 30.0)
- `--algorithm`: Optimization method (`genetic`, `greedy`, `both`)

### CORS Configuration
Backend configured to accept requests from:
- `http://localhost:3000` (React default)
- `http://localhost:5173-5191` (Vite port range)

### State Synchronization
- Frontend state (React) mirrors backend data
- API calls made on component mount to load existing data
- Real-time updates when AI actions modify state through Cedar OS
- **Planned**: Real-time optimization progress updates

## Django Integration Plan for Stinger

### Required Models (Already Implemented)
- **Building**: Stores campus buildings with demand data
- **BusStop**: Bus stop locations with capacity and features
- **Route**: Optimized bus routes with metadata
- **RouteStop**: Through model for route-stop relationships with ordering
- **RouteAssignment**: Bus-to-route assignments with schedules

### Services to Implement
```python
# bus_system_backend/api/services/optimization_service.py
class RouteOptimizationService:
    @staticmethod
    def run_stinger_optimization(buildings_data, stops_data, fleet_size):
        # Save CSV data to stinger/data/ directory
        # Execute nearest_stops_demand.py
        # Execute tlpf_ktransfers.py with parameters
        # Parse optimization results
        # Return structured route data
        
    @staticmethod
    def parse_stinger_output(output_text):
        # Parse Stinger algorithm output
        # Convert to Django model format
        # Return routes with stops and metadata
        
    @staticmethod
    def apply_optimized_routes(optimization_results):
        # Create Route and RouteStop objects
        # Update bus assignments
        # Return success/error status
```

### API Endpoints to Add
```python
# bus_system_backend/api/views/optimization_views.py
class RouteOptimizationView(BaseAPIView):
    def post(self, request):
        # Extract buildings and stops from request
        # Validate data format
        # Run Stinger optimization
        # Return optimization results
        
class OptimizationResultsView(BaseAPIView):
    def get(self, request, job_id):
        # Return cached optimization results
        # Include route details and performance metrics
```

### Frontend Integration Steps
1. **Add Stinger API calls** to `src/api.js`
2. **Create optimization UI** for triggering route generation
3. **Display optimized routes** on Google Maps with route lines
4. **Add route management** interface for applying/modifying routes
5. **Integrate with Cedar OS** for AI-powered optimization

## Package Management Notes

### Frontend
- **Vite Override**: Uses `rolldown-vite@7.1.12` instead of standard Vite
- **Cedar OS Packages**: `cedar-os`, `cedar-os-components`, `@cedar-os/backend`
- **Motion Libraries**: Multiple Framer Motion packages for animations
- **Tailwind**: Uses Tailwind CSS v4 with PostCSS integration

### Backend
- **Core Django**: `django`, `djangorestframework`, `django-cors-headers`
- **Data Processing**: `pandas`, `numpy` (for Stinger integration)
- **Task Queue** (planned): `celery`, `redis` for background optimization

### Route Optimization (Stinger)
- **Core Dependencies**: `pandas>=1.3.0`, `numpy>=1.20.0`
- **Algorithm Libraries**: Built-in Python `math`, `heapq`, `collections`
- **Data Processing**: CSV handling via pandas
