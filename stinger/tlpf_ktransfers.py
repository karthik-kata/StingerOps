# tlpf_ktransfers_improved.py
# Improved Transit Line Planning with hub-and-spoke + demand-driven route construction.

import math
import argparse
import heapq
import pandas as pd
import random
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict, deque


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0088
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))

def travel_minutes(lat1, lon1, lat2, lon2, speed_kmh=30.0):
    km = haversine_km(lat1, lon1, lat2, lon2)
    return (km / max(speed_kmh, 1e-6)) * 60.0

@dataclass
class Stop:
    stop_id: str
    name: str
    lat: float
    lon: float
    kind: str

@dataclass
class Line:
    line_id: str
    stops: List[str]
    cycle_minutes: float
    demand_coverage: float = 0.0
    efficiency_score: float = 0.0

@dataclass
class RouteSolution:
    lines: List[Line]
    total_cost: float
    demand_coverage: float
    efficiency: float

# ------------------ DATA LOADING ------------------

def load_sources(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["stop_id"] = df["source_name"]
    df["name"] = df["source_name"]
    df["lat"] = df["latitude"]
    df["lon"] = df["longitude"]
    df["demand"] = df["demand"].fillna(1.0)
    return df[["stop_id","name","lat","lon","demand"]].copy()

def load_destinations(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["stop_id"] = df["stop_name"]
    df["name"] = df["stop_name"]
    df["lat"] = df["stop_lat"]
    df["lon"] = df["stop_lon"]
    df["demand"] = df["total_demand"].fillna(0.0)
    return df[["stop_id","name","lat","lon","demand"]].copy()

def build_equal_split_od(sources: pd.DataFrame, destinations: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, s in sources.iterrows():
        total = float(s["demand"]) if pd.notna(s["demand"]) else 1.0
        if len(destinations) == 0:
            continue
        share = total / len(destinations)
        for _, d in destinations.iterrows():
            rows.append({"o": s["stop_id"], "d": d["stop_id"], "demand": share})
    return pd.DataFrame(rows)

def build_stops(sources: pd.DataFrame, destinations: pd.DataFrame) -> Dict[str, Stop]:
    stops = {}
    for _, r in sources.iterrows():
        stops[r["stop_id"]] = Stop(r["stop_id"], str(r["name"]), float(r["lat"]), float(r["lon"]), "source")
    for _, r in destinations.iterrows():
        stops[r["stop_id"]] = Stop(r["stop_id"], str(r["name"]), float(r["lat"]), float(r["lon"]), "destination")
    return stops

# ------------------ ROUTING CORE ------------------

def route_length_minutes(stops_order: List[str], stop_lookup: Dict[str, Stop], speed_kmh=30.0, layover_frac=0.1) -> float:
    total = 0.0
    for i in range(len(stops_order) - 1):
        a = stop_lookup[stops_order[i]]
        b = stop_lookup[stops_order[i+1]]
        total += travel_minutes(a.lat, a.lon, b.lat, b.lon, speed_kmh)
    a = stop_lookup[stops_order[-1]]
    b = stop_lookup[stops_order[0]]
    total += travel_minutes(a.lat, a.lon, b.lat, b.lon, speed_kmh)
    return total * (1.0 + layover_frac)

def nearest_order(stops: List[str], stop_lookup: Dict[str, Stop]) -> List[str]:
    """Simple nearest neighbor ordering for stops."""
    if not stops:
        return []
    remaining = set(stops)
    order = [stops[0]]
    remaining.remove(stops[0])
    while remaining:
        cur = order[-1]
        nxt = min(remaining, key=lambda s: haversine_km(
            stop_lookup[cur].lat, stop_lookup[cur].lon,
            stop_lookup[s].lat, stop_lookup[s].lon))
        order.append(nxt)
        remaining.remove(nxt)
    return order

def build_hub_and_spoke_routes(stops: Dict[str, Stop], od_matrix: pd.DataFrame, 
                              target_lines: int = 8, speed_kmh: float = 30.0) -> List[Line]:
    """Build routes using hub-and-spoke model with demand-driven optimization."""
    
    # Calculate demand by stop
    demand_by_stop = od_matrix.groupby('d')['demand'].sum().to_dict()
    
    # Identify high-demand stops (hubs)
    sorted_stops = sorted(demand_by_stop.items(), key=lambda x: x[1], reverse=True)
    hub_stops = [stop_id for stop_id, demand in sorted_stops[:min(6, len(sorted_stops))] 
                 if demand > 0 and stop_id in stops]
    
    # Identify source stops
    source_stops = [sid for sid, stop in stops.items() if stop.kind == "source"]
    
    print(f"Identified {len(hub_stops)} hub stops: {[stops[sid].name for sid in hub_stops[:3]]}...")
    print(f"Source stops: {[stops[sid].name for sid in source_stops]}")
    
    lines = []
    line_id = 0
    
    # Create direct routes from sources to high-demand destinations
    for source in source_stops:
        if source not in stops:
            continue
            
        # Find top destinations for this source
        source_demand = od_matrix[od_matrix['o'] == source].sort_values('demand', ascending=False)
        top_dests = source_demand.head(8)['d'].tolist()
        
        if not top_dests:
            continue
            
        # Create route: source -> top destinations
        route_stops = [source] + top_dests
        route_stops = [s for s in route_stops if s in stops]  # Filter valid stops
        
        if len(route_stops) < 2:
            continue
            
        # Optimize route order
        optimized_route = optimize_route_greedy(route_stops, stops, speed_kmh)
        cyc_min = route_length_minutes(optimized_route, stops, speed_kmh)
        
        # Calculate metrics
        demand_coverage = sum(demand_by_stop.get(sid, 0.0) for sid in optimized_route)
        efficiency = demand_coverage / max(cyc_min, 1.0)
        
        lines.append(Line(
            line_id=f"H_{line_id}",
            stops=optimized_route,
            cycle_minutes=cyc_min,
            demand_coverage=demand_coverage,
            efficiency_score=efficiency
        ))
        line_id += 1
    
    # Create cross-campus routes connecting major hubs
    if len(hub_stops) >= 2:
        for i in range(min(3, len(hub_stops) - 1)):
            # Create routes connecting different hub areas
            start_hub = hub_stops[i]
            end_hub = hub_stops[(i + 1) % len(hub_stops)]
            
            # Find intermediate stops with high demand
            intermediate_candidates = []
            for sid, demand in demand_by_stop.items():
                if sid in stops and sid not in [start_hub, end_hub] and demand > 0:
                    # Check if it's roughly between the hubs
                    start_pos = (stops[start_hub].lat, stops[start_hub].lon)
                    end_pos = (stops[end_hub].lat, stops[end_hub].lon)
                    stop_pos = (stops[sid].lat, stops[sid].lon)
                    
                    # Simple check: if stop is not too far from the line between hubs
                    dist_to_line = point_to_line_distance(stop_pos, start_pos, end_pos)
                    if dist_to_line < 0.01:  # ~1km threshold
                        intermediate_candidates.append((sid, demand))
            
            # Sort by demand and take top candidates
            intermediate_candidates.sort(key=lambda x: x[1], reverse=True)
            intermediate_stops = [sid for sid, _ in intermediate_candidates[:4]]
            
            # Create route
            route_stops = [start_hub] + intermediate_stops + [end_hub]
            route_stops = [s for s in route_stops if s in stops]
            
            if len(route_stops) >= 3:
                optimized_route = optimize_route_greedy(route_stops, stops, speed_kmh)
                cyc_min = route_length_minutes(optimized_route, stops, speed_kmh)
                
                demand_coverage = sum(demand_by_stop.get(sid, 0.0) for sid in optimized_route)
                efficiency = demand_coverage / max(cyc_min, 1.0)
                
                lines.append(Line(
                    line_id=f"C_{line_id}",
                    stops=optimized_route,
                    cycle_minutes=cyc_min,
                    demand_coverage=demand_coverage,
                    efficiency_score=efficiency
                ))
                line_id += 1
    
    # Create local feeder routes for high-demand areas
    for hub in hub_stops[:3]:  # Top 3 hubs
        if hub not in stops:
            continue
            
        # Find nearby high-demand stops
        hub_pos = (stops[hub].lat, stops[hub].lon)
        nearby_stops = []
        
        for sid, demand in demand_by_stop.items():
            if sid in stops and sid != hub and demand > 0:
                stop_pos = (stops[sid].lat, stops[sid].lon)
                dist = haversine_km(hub_pos[0], hub_pos[1], stop_pos[0], stop_pos[1])
                if dist < 0.5:  # Within 500m
                    nearby_stops.append((sid, demand, dist))
        
        # Sort by demand and distance
        nearby_stops.sort(key=lambda x: (x[1], -x[2]), reverse=True)
        selected_nearby = [sid for sid, _, _ in nearby_stops[:5]]
        
        if selected_nearby:
            route_stops = [hub] + selected_nearby
            optimized_route = optimize_route_greedy(route_stops, stops, speed_kmh)
            cyc_min = route_length_minutes(optimized_route, stops, speed_kmh)
            
            demand_coverage = sum(demand_by_stop.get(sid, 0.0) for sid in optimized_route)
            efficiency = demand_coverage / max(cyc_min, 1.0)
            
            lines.append(Line(
                line_id=f"F_{line_id}",
                stops=optimized_route,
                cycle_minutes=cyc_min,
                demand_coverage=demand_coverage,
                efficiency_score=efficiency
            ))
            line_id += 1
    
    # Sort lines by efficiency and return top ones
    lines.sort(key=lambda x: x.efficiency_score, reverse=True)
    return lines[:target_lines]

def point_to_line_distance(point, line_start, line_end):
    """Calculate distance from point to line segment."""
    px, py = point
    x1, y1 = line_start
    x2, y2 = line_end
    
    # Convert to approximate km (rough approximation)
    A = px - x1
    B = py - y1
    C = x2 - x1
    D = y2 - y1
    
    dot = A * C + B * D
    len_sq = C * C + D * D
    
    if len_sq == 0:
        return math.sqrt(A * A + B * B)
    
    param = dot / len_sq
    
    if param < 0:
        xx, yy = x1, y1
    elif param > 1:
        xx, yy = x2, y2
    else:
        xx = x1 + param * C
        yy = y1 + param * D
    
    dx = px - xx
    dy = py - yy
    return math.sqrt(dx * dx + dy * dy)

def optimize_route_greedy(stops: List[str], stop_lookup: Dict[str, Stop], 
                         speed_kmh: float = 30.0) -> List[str]:
    """Greedy optimization for route ordering."""
    if len(stops) <= 2:
        return stops
    
    # Start with the stop that has highest demand
    remaining = set(stops)
    route = []
    
    # Find starting point (highest demand or first if no demand data)
    start_stop = stops[0]
    route.append(start_stop)
    remaining.remove(start_stop)
    
    # Greedily add nearest stops
    while remaining:
        current = route[-1]
        current_pos = (stop_lookup[current].lat, stop_lookup[current].lon)
        
        # Find nearest remaining stop
        nearest = min(remaining, key=lambda s: haversine_km(
            current_pos[0], current_pos[1],
            stop_lookup[s].lat, stop_lookup[s].lon
        ))
        
        route.append(nearest)
        remaining.remove(nearest)
    
    return route

def optimize_route_2opt(stops: List[str], stop_lookup: Dict[str, Stop], 
                       speed_kmh: float = 30.0) -> List[str]:
    """2-opt optimization for better route ordering."""
    if len(stops) <= 2:
        return stops
    
    # Start with nearest neighbor
    current = nearest_order(stops, stop_lookup)
    best_cost = route_length_minutes(current, stop_lookup, speed_kmh)
    improved = True
    
    while improved:
        improved = False
        for i in range(1, len(current) - 1):
            for j in range(i + 1, len(current)):
                # Try 2-opt swap
                new_route = current[:i] + current[i:j+1][::-1] + current[j+1:]
                new_cost = route_length_minutes(new_route, stop_lookup, speed_kmh)
                
                if new_cost < best_cost:
                    current = new_route
                    best_cost = new_cost
                    improved = True
                    break
            if improved:
                break
    
    return current

# ------------------ K-TRANSFER ROUTING ------------------

def build_line_indices(lines: List[Line]) -> Dict[str, Dict[str, int]]:
    return {ln.line_id: {sid: i for i, sid in enumerate(ln.stops)} for ln in lines}

def build_stop_to_lines(lines: List[Line]) -> Dict[str, List[str]]:
    mapping = {}
    for ln in lines:
        for sid in ln.stops:
            mapping.setdefault(sid, []).append(ln.line_id)
    return mapping

def build_adj_times(lines: List[Line], stops: Dict[str, Stop], speed_kmh=30.0):
    adj = {}
    for ln in lines:
        times = []
        for i in range(len(ln.stops)-1):
            a = stops[ln.stops[i]]
            b = stops[ln.stops[i+1]]
            times.append(travel_minutes(a.lat, a.lon, b.lat, b.lon, speed_kmh))
        adj[ln.line_id] = times
    return adj

def shortest_time_k_transfers(o: str, d: str, lines: List[Line], stops: Dict[str, Stop],
                              wait_by_line: Dict[str, float], transfer_penalty_min: float, k_max: int,
                              speed_kmh: float = 30.0) -> float:
    if not lines:
        return float("inf")
    line_idx = build_line_indices(lines)
    stop2lines = build_stop_to_lines(lines)
    if o not in stop2lines or d not in stop2lines:
        return float("inf")
    adj_times = build_adj_times(lines, stops, speed_kmh)
    line_to_stops = {ln.line_id: ln.stops for ln in lines}

    pq, dist = [], {}
    for lid in stop2lines[o]:
        i = line_idx[lid][o]
        c0 = wait_by_line.get(lid, 0.0)
        dist[(lid, i, 0)] = c0
        heapq.heappush(pq, (c0, lid, i, 0))

    while pq:
        cost, lid, i, k = heapq.heappop(pq)
        if cost != dist.get((lid,i,k), float("inf")):
            continue
        cur_stop = line_to_stops[lid][i]
        if cur_stop == d:
            return cost
        if i < len(line_to_stops[lid]) - 1:
            t_leg = adj_times[lid][i]
            ns = (lid, i+1, k)
            nc = cost + t_leg
            if nc < dist.get(ns, float("inf")):
                dist[ns] = nc
                heapq.heappush(pq, (nc, *ns))
        if k < k_max:
            for lid2 in stop2lines[cur_stop]:
                if lid2 == lid: continue
                j = line_idx[lid2][cur_stop]
                nc = cost + transfer_penalty_min + wait_by_line.get(lid2, 0.0)
                ns = (lid2, j, k+1)
                if nc < dist.get(ns, float("inf")):
                    dist[ns] = nc
                    heapq.heappush(pq, (nc, *ns))
    return float("inf")

# ------------------ IMPROVED OPTIMIZATION ------------------

def evaluate_solution_improved(lines: List[Line], od: pd.DataFrame, stops: Dict[str, Stop],
                              fleet_buses: int, k_transfers: int, transfer_penalty_min: float,
                              speed_kmh: float = 30.0, f_min: float = 1.0) -> Tuple[float, float, float]:
    """Evaluate a solution with improved metrics."""
    if not lines:
        return 1e9, 0.0, 0.0
    
    freq = max(f_min, fleet_buses / len(lines))
    headway = 60.0 / freq
    wait_by_line = {ln.line_id: 0.5 * headway for ln in lines}
    
    total_cost = 0.0
    total_demand = 0.0
    covered_demand = 0.0
    accessible_pairs = 0
    
    for _, row in od.iterrows():
        o, d, dem = row["o"], row["d"], float(row["demand"])
        total_demand += dem
        
        best = shortest_time_k_transfers(o, d, lines, stops,
                                        wait_by_line, transfer_penalty_min, k_transfers, speed_kmh)
        if math.isfinite(best):
            total_cost += dem * best
            covered_demand += dem
            accessible_pairs += 1
        else:
            # Fallback to direct travel
            a, b = stops[o], stops[d]
            fallback_cost = travel_minutes(a.lat, a.lon, b.lat, b.lon, speed_kmh) + transfer_penalty_min
            total_cost += dem * fallback_cost
    
    demand_coverage = covered_demand / max(total_demand, 1.0)
    accessibility = accessible_pairs / len(od) if len(od) > 0 else 0.0
    efficiency = covered_demand / max(total_cost, 1.0)
    
    return total_cost, demand_coverage, efficiency

def optimize_routes_iterative(candidates: List[Line], od: pd.DataFrame, stops: Dict[str, Stop],
                             fleet_buses: int, k_transfers: int, transfer_penalty_min: float,
                             speed_kmh: float = 30.0) -> List[Line]:
    """Iterative optimization that actually works well."""
    
    # Start with the most efficient lines
    candidates.sort(key=lambda x: x.efficiency_score, reverse=True)
    
    selected = []
    remaining = candidates.copy()
    
    # Greedy selection with better evaluation
    while remaining:
        best_line = None
        best_improvement = -float('inf')
        
        for line in remaining:
            # Try adding this line
            test_selection = selected + [line]
            cost, coverage, efficiency = evaluate_solution_improved(
                test_selection, od, stops, fleet_buses, k_transfers, transfer_penalty_min, speed_kmh)
            
            # Calculate improvement
            if selected:
                old_cost, old_coverage, old_efficiency = evaluate_solution_improved(
                    selected, od, stops, fleet_buses, k_transfers, transfer_penalty_min, speed_kmh)
                improvement = (coverage - old_coverage) * 1000 - (cost - old_cost) / 1000
            else:
                improvement = coverage * 1000 - cost / 1000
            
            if improvement > best_improvement:
                best_improvement = improvement
                best_line = line
        
        # Only add if it improves the solution significantly
        if best_line and best_improvement > 0:
            selected.append(best_line)
            remaining.remove(best_line)
        else:
            break
    
    return selected

def optimize_routes_demand_driven(candidates: List[Line], od: pd.DataFrame, stops: Dict[str, Stop],
                                 fleet_buses: int, k_transfers: int, transfer_penalty_min: float,
                                 speed_kmh: float = 30.0) -> List[Line]:
    """Demand-driven optimization focusing on actual demand patterns."""
    
    # Group OD pairs by source
    sources = od['o'].unique()
    source_routes = {}
    
    for source in sources:
        source_od = od[od['o'] == source].sort_values('demand', ascending=False)
        top_destinations = source_od.head(10)['d'].tolist()
        
        # Find lines that serve this source and its top destinations
        relevant_lines = []
        for line in candidates:
            if source in line.stops:
                # Count how many top destinations this line serves
                served_dests = sum(1 for dest in top_destinations if dest in line.stops)
                if served_dests > 0:
                    relevant_lines.append((line, served_dests, line.efficiency_score))
        
        # Sort by destinations served and efficiency
        relevant_lines.sort(key=lambda x: (x[1], x[2]), reverse=True)
        source_routes[source] = [line for line, _, _ in relevant_lines[:3]]  # Top 3 per source
    
    # Select best routes across all sources
    selected = []
    used_lines = set()
    
    # Add best route for each source
    for source, routes in source_routes.items():
        for route in routes:
            if route.line_id not in used_lines:
                selected.append(route)
                used_lines.add(route.line_id)
                break  # Only one route per source initially
    
    # Add additional high-efficiency routes that don't conflict
    remaining = [line for line in candidates if line.line_id not in used_lines]
    remaining.sort(key=lambda x: x.efficiency_score, reverse=True)
    
    for line in remaining:
        if len(selected) >= fleet_buses // 2:  # Limit number of routes
            break
        
        # Check if this line adds value without too much overlap
        overlap = 0
        for selected_line in selected:
            overlap += len(set(line.stops) & set(selected_line.stops))
        
        if overlap < len(line.stops) * 0.7:  # Less than 70% overlap
            selected.append(line)
            used_lines.add(line.line_id)
    
    return selected

# Removed old genetic algorithm - replaced with better demand-driven optimization

# ------------------ GREEDY SELECTION (FALLBACK) ------------------

def greedy_select_lines(od: pd.DataFrame, lines: List[Line], stops: Dict[str, Stop],
                        fleet_buses: int, k_transfers: int, transfer_penalty_min: float,
                        speed_kmh: float = 30.0, f_min: float = 1.0) -> List[Line]:
    """Fallback greedy selection method."""
    selected, remaining = [], list(lines)

    def total_cost(lines_subset: List[Line]) -> float:
        if not lines_subset:
            return 1e9
        freq = max(f_min, fleet_buses / max(len(lines_subset), 1))
        headway = 60.0 / freq
        wait_by_line = {ln.line_id: 0.5 * headway for ln in lines_subset}
        total = 0.0
        for _, row in od.iterrows():
            o, d, dem = row["o"], row["d"], float(row["demand"])
            best = shortest_time_k_transfers(o, d, lines_subset, stops,
                                             wait_by_line, transfer_penalty_min, k_transfers, speed_kmh)
            if not math.isfinite(best):
                a, b = stops[o], stops[d]
                best = travel_minutes(a.lat, a.lon, b.lat, b.lon, speed_kmh) + transfer_penalty_min
            total += dem * best
        return total

    improved = True
    while remaining and improved:
        improved = False
        base_cost = total_cost(selected)
        best_line, best_cost = None, base_cost
        for ln in remaining:
            new_cost = total_cost(selected + [ln])
            if new_cost < best_cost:
                best_cost, best_line = new_cost, ln
        if best_line:
            selected.append(best_line)
            remaining.remove(best_line)
            improved = True
    return selected

# ------------------ MAIN ------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", default="./data/sources.csv")
    ap.add_argument("--destinations", default="stops_with_demand.csv")
    ap.add_argument("--fleet", type=int, default=12)
    ap.add_argument("--target-lines", type=int, default=12)
    ap.add_argument("--k-transfers", type=int, default=2)
    ap.add_argument("--transfer-penalty", type=float, default=5.0)
    ap.add_argument("--speed-kmh", type=float, default=30.0)
    ap.add_argument("--algorithm", choices=["genetic", "greedy", "both"], default="genetic",
                    help="Optimization algorithm to use")
    ap.add_argument("--generations", type=int, default=100,
                    help="Number of generations for genetic algorithm")
    ap.add_argument("--population-size", type=int, default=50,
                    help="Population size for genetic algorithm")
    args = ap.parse_args()

    print("Loading data...")
    src = load_sources(args.sources)
    dst = load_destinations(args.destinations)
    od = build_equal_split_od(src, dst)
    stops = build_stops(src, dst)

    print(f"Loaded {len(src)} sources and {len(dst)} destinations")
    print(f"Total OD pairs: {len(od)}")

    # Build improved candidate lines using hub-and-spoke model
    print("Building candidate lines with hub-and-spoke model...")
    cands = build_hub_and_spoke_routes(stops, od, target_lines=args.target_lines, speed_kmh=args.speed_kmh)
    print(f"Generated {len(cands)} candidate lines")

    # Optimize using selected algorithm
    if args.algorithm == "genetic" or args.algorithm == "both":
        print(f"Running improved demand-driven optimization...")
        selected = optimize_routes_demand_driven(cands, od, stops,
                                               fleet_buses=args.fleet,
                                               k_transfers=args.k_transfers,
                                               transfer_penalty_min=args.transfer_penalty,
                                               speed_kmh=args.speed_kmh)
        
        # Evaluate the solution
        cost, coverage, efficiency = evaluate_solution_improved(
            selected, od, stops, args.fleet, args.k_transfers, args.transfer_penalty, args.speed_kmh)
        
        print(f"\nImproved Algorithm Results:")
        print(f"Total Cost: {cost:.2f}")
        print(f"Demand Coverage: {coverage:.2%}")
        print(f"Efficiency: {efficiency:.4f}")
        
    elif args.algorithm == "greedy":
        print("Running iterative optimization...")
        selected = optimize_routes_iterative(cands, od, stops,
                                           fleet_buses=args.fleet,
                                           k_transfers=args.k_transfers,
                                           transfer_penalty_min=args.transfer_penalty,
                                           speed_kmh=args.speed_kmh)
    
    if args.algorithm == "both":
        print("\n" + "="*50)
        print("Comparing with Iterative Algorithm...")
        iterative_selected = optimize_routes_iterative(cands, od, stops,
                                                     fleet_buses=args.fleet,
                                                     k_transfers=args.k_transfers,
                                                     transfer_penalty_min=args.transfer_penalty,
                                                     speed_kmh=args.speed_kmh)
        
        iterative_cost, iterative_coverage, iterative_efficiency = evaluate_solution_improved(
            iterative_selected, od, stops, args.fleet, args.k_transfers, args.transfer_penalty, args.speed_kmh)
        
        print(f"Iterative Results:")
        print(f"Total Cost: {iterative_cost:.2f}")
        print(f"Demand Coverage: {iterative_coverage:.2%}")
        print(f"Efficiency: {iterative_efficiency:.4f}")
        
        print(f"\nImprovement over Iterative:")
        print(f"Cost: {((iterative_cost - cost) / iterative_cost * 100):+.1f}%")
        print(f"Coverage: {((coverage - iterative_coverage) / iterative_coverage * 100):+.1f}%")
        print(f"Efficiency: {((efficiency - iterative_efficiency) / iterative_efficiency * 100):+.1f}%")

    # Report final results
    if selected:
        freq = max(1.0, args.fleet / len(selected))
        headway, wait = 60.0 / freq, 30.0 / freq
    else:
        headway = wait = None

    print(f"\nFinal Selected Lines ({len(selected)} lines):")
    print("-" * 60)
    for i, ln in enumerate(selected, 1):
        print(f"{i:2d}. {ln.line_id:8s} | {len(ln.stops):2d} stops | "
              f"cycle={ln.cycle_minutes:5.1f} min | "
              f"demand={ln.demand_coverage:6.0f} | "
              f"efficiency={ln.efficiency_score:6.2f}")
    
    if headway:
        print(f"\nService Characteristics:")
        print(f"Equal headway across {len(selected)} lines: ~{headway:.1f} min")
        print(f"Mean wait time: ~{wait:.1f} min")
        print(f"Total fleet utilization: {len(selected)} buses")
    
    # Print route details
    print(f"\nDetailed Route Information:")
    print("=" * 60)
    for i, ln in enumerate(selected, 1):
        print(f"\nRoute {i}: {ln.line_id}")
        print(f"Stops ({len(ln.stops)}):")
        for j, stop_id in enumerate(ln.stops):
            stop = stops[stop_id]
            print(f"  {j+1:2d}. {stop.name:30s} ({stop.lat:.4f}, {stop.lon:.4f})")
        print(f"Cycle time: {ln.cycle_minutes:.1f} minutes")
        print(f"Demand coverage: {ln.demand_coverage:.0f}")
        print(f"Efficiency score: {ln.efficiency_score:.2f}")

if __name__ == "__main__":
    main()
