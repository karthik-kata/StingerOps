#!/usr/bin/env python3
"""
Debug script to test Stinger output parsing
"""
import os
import sys
import subprocess
import re

def test_stinger_output():
    """Test parsing of actual Stinger output."""
    # Change to stinger directory
    stinger_path = "/Users/antonychackieth/IdeaProjects/TBD/stinger"
    
    # Run stinger optimization
    optimization_cmd = [
        'python3', 'tlpf_ktransfers.py',
        '--fleet', '5',
        '--target-lines', '3'
    ]
    
    result = subprocess.run(
        optimization_cmd,
        cwd=stinger_path,
        capture_output=True,
        text=True
    )
    
    print("=== RAW STINGER OUTPUT ===")
    print(result.stdout)
    print("=== END RAW OUTPUT ===\n")
    
    # Test parsing
    lines = result.stdout.strip().split('\n')
    routes = []
    parsing_routes = False
    parsing_details = False
    
    print("=== PARSING TEST ===")
    for i, line in enumerate(lines):
        line = line.strip()
        print(f"Line {i}: '{line}'")
        
        if 'Final Selected Lines' in line:
            print("  -> Found 'Final Selected Lines', starting route parsing")
            parsing_routes = True
            continue
        
        if 'Detailed Route Information' in line:
            print("  -> Found 'Detailed Route Information', switching to detail parsing")
            parsing_details = True
            parsing_routes = False
            continue
        
        if parsing_routes and line and not line.startswith('-'):
            # Try multiple regex patterns
            patterns = [
                r'\\s*(\\d+)\\. (\\w+)\\s+\\|\\s+(\\d+) stops\\s+\\|.*cycle=\\s*([\\d.]+) min.*demand=\\s*([\\d.]+).*efficiency=([\\d.]+)',
                r'\\s*(\\d+)\\. (\\w+)\\s+\\|\\s+(\\d+) stops\\s+\\|.*cycle=([\\d.]+) min.*demand=([\\d.]+).*efficiency=([\\d.]+)',
                r'(\\d+)\\. (\\w+)\\s+\\|.*?(\\d+) stops.*?cycle=([\\d.]+) min.*?demand=([\\d.]+).*?efficiency=([\\d.]+)'
            ]
            
            for j, pattern in enumerate(patterns):
                match = re.match(pattern, line)
                if match:
                    print(f"  -> Pattern {j+1} MATCHED: {match.groups()}")
                    routes.append({
                        'route_number': int(match.group(1)),
                        'route_id': match.group(2),
                        'stops_count': int(match.group(3)),
                        'cycle_minutes': float(match.group(4)),
                        'demand_coverage': float(match.group(5)),
                        'efficiency': float(match.group(6))
                    })
                    break
                else:
                    print(f"  -> Pattern {j+1} no match")
    
    print(f"\n=== PARSED {len(routes)} ROUTES ===")
    for route in routes:
        print(f"Route: {route}")

if __name__ == "__main__":
    test_stinger_output()