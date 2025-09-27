#!/usr/bin/env python3
import requests
import json

# Test Django API
API_BASE = "http://localhost:8000/api"

def test_api():
    try:
        # Test API status
        response = requests.get(f"{API_BASE}/status/")
        print(f"API Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Test bus count
        response = requests.get(f"{API_BASE}/bus-count/get_bus_count/")
        print(f"\nBus Count: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Test setting bus count
        response = requests.post(f"{API_BASE}/bus-count/set_bus_count/", 
                               json={"count": 3})
        print(f"\nSet Bus Count: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Test getting bus stops
        response = requests.get(f"{API_BASE}/bus-stops/")
        print(f"\nBus Stops: {response.status_code}")
        print(f"Count: {len(response.json())}")
        
    except Exception as e:
        print(f"Error testing API: {e}")

if __name__ == "__main__":
    test_api()
