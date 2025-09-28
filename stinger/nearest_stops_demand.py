import pandas as pd
import math

def euclidean_distance(lat1, lon1, lat2, lon2):
    return math.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2)

def distribute_demand(buildings_file, stops_file, output_file):
    # Read inputs
    buildings = pd.read_csv(buildings_file)
    stops = pd.read_csv(stops_file)
    
    # Initialize stop demand
    stops["total_demand"] = 0.0
    
    # Loop over buildings
    for _, building in buildings.iterrows():
        lat, lon, demand = building["latitude"], building["longitude"], building["demand"]
        
        # Compute distances to all stops
        stops["distance"] = stops.apply(
            lambda row: euclidean_distance(lat, lon, row["stop_lat"], row["stop_lon"]), axis=1
        )
        
        # Find 3 closest stops
        closest_stops = stops.nsmallest(3, "distance")
        
        # Distribute demand equally
        distributed_demand = demand / 3.0
        stops.loc[closest_stops.index, "total_demand"] += distributed_demand
    
    # Round to nearest integer
    stops["total_demand"] = stops["total_demand"].round(0).astype(int)
    
    # Enforce minimum demand of 10
    stops["total_demand"] = stops["total_demand"].clip(lower=10)
    
    # Save output with latitude and longitude included
    stops[["stop_name", "stop_lat", "stop_lon", "total_demand"]].to_csv(output_file, index=False)

# Example usage:
if __name__ == "__main__":
    distribute_demand("./data/buildings.csv", "./data/stops.csv", "stops_with_demand.csv")
