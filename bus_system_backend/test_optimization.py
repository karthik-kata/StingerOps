#!/usr/bin/env python3
"""
Test script for route optimization integration
"""
import os
import sys
import django
from django.conf import settings

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bus_system_backend.settings')
django.setup()

# Now we can import Django models and services
from api.services import RouteOptimizationService
from api.models import Building, BusStop

def test_stinger_integration():
    """Test the Stinger integration with sample data."""
    print("=" * 60)
    print("Testing Stinger Route Optimization Integration")
    print("=" * 60)
    
    # Test data (same as in the optimization test view)
    buildings_data = [
  {
    "building_name": "760 SPRING STREET",
    "demand": 30,
    "latitude": 33.77780591,
    "longitude": -84.38983261
  },
  {
    "building_name": "ALLEN SUSTAINABLE EDUCATION BLDG",
    "demand": 198,
    "latitude": 33.7763486,
    "longitude": -84.39775187
  },
  {
    "building_name": "BOGGS BUILDING",
    "demand": 282,
    "latitude": 33.7759127,
    "longitude": -84.39861597
  },
  {
    "building_name": "BUNGER-HENRY BUILDING",
    "demand": 42,
    "latitude": 33.77582055,
    "longitude": -84.39698768
  },
  {
    "building_name": "CALLAWAY MANUFACTURING RESEARCH CENTER",
    "demand": 96,
    "latitude": 33.77775425,
    "longitude": -84.39849622
  },
  {
    "building_name": "CHERRY EMERSON BUILDING",
    "demand": 116,
    "latitude": 33.77805339,
    "longitude": -84.39740763
  },
  {
    "building_name": "CLOUGH UNDERGRADUATE LEARNING COMMONS",
    "demand": 758,
    "latitude": 33.77543753,
    "longitude": -84.39390424
  },
  {
    "building_name": "COLLEGE OF COMPUTING",
    "demand": 421,
    "latitude": 33.77755663,
    "longitude": -84.39758288
  },
  {
    "building_name": "COLLEGE OF DESIGN EAST",
    "demand": 393,
    "latitude": 33.7762653,
    "longitude": -84.3952311
  },
  {
    "building_name": "COLLEGE OF DESIGN WEST",
    "demand": 88,
    "latitude": 33.77620995,
    "longitude": -84.39576983
  },
  {
    "building_name": "ENGINEERING SCIENCE & MECHANICS BUILDING",
    "demand": 143,
    "latitude": 33.77216951,
    "longitude": -84.39511521
  },
  {
    "building_name": "FORD ENVIRONMENTAL SCIENCE & TECHNOLOGY BUILDING",
    "demand": 376,
    "latitude": 33.77847339,
    "longitude": -84.39402606
  },
  {
    "building_name": "GUGGENHEIM AEROSPACE BUILDING",
    "demand": 96,
    "latitude": 33.77241768,
    "longitude": -84.39561051
  },
  {
    "building_name": "HOWEY PHYSICS BUILDING",
    "demand": 991,
    "latitude": 33.77769409,
    "longitude": -84.39847445
  },
  {
    "building_name": "INSTRUCTIONAL CENTER",
    "demand": 908,
    "latitude": 33.77564391,
    "longitude": -84.4004773
  },
  {
    "building_name": "KENDEDA BUILDING FOR INNOVATIVE SUSTAINABLE DESIGN",
    "demand": 304,
    "latitude": 33.77881365,
    "longitude": -84.3981406
  },
  {
    "building_name": "KLAUS ADVANCED COMPUTING BUILDING",
    "demand": 655,
    "latitude": 33.77710051,
    "longitude": -84.3949246
  },
  {
    "building_name": "LOVE MANUFACTURING BLDG (MRDC II)",
    "demand": 198,
    "latitude": 33.77699716,
    "longitude": -84.40182977
  },
  {
    "building_name": "MANUFACTURING RELATED DISCIPLINES COMPLEX (MRDC)",
    "demand": 229,
    "latitude": 33.77719823,
    "longitude": -84.40058242
  },
  {
    "building_name": "MASON BLDG (CIVIL & ENVIRONMENTAL ENGINEERING)",
    "demand": 343,
    "latitude": 33.77695121,
    "longitude": -84.39953569
  },
  {
    "building_name": "MOLECULAR SCIENCES & ENGINEERING BUILDING",
    "demand": 338,
    "latitude": 33.78010218,
    "longitude": -84.39447513
  },
  {
    "building_name": "PAPER TRICENTENIAL BUILDING RENEWABLE BIPRODUCTS INSTITUTE)",
    "demand": 223,
    "latitude": 33.78138685,
    "longitude": -84.40234365
  },
  {
    "building_name": "SCHELLER COLLEGE OF BUSINESS",
    "demand": 1232,
    "latitude": 33.77665282,
    "longitude": -84.38724716
  },
  {
    "building_name": "SKILES CLASSROOM BUILDING",
    "demand": 896,
    "latitude": 33.77390366,
    "longitude": -84.39469797
  },
  {
    "building_name": "SMITH BUILDING (SOCIAL SCIENCES)",
    "demand": 407,
    "latitude": 33.77432195,
    "longitude": -84.39904401
  },
  {
    "building_name": "STUDENT SUCCESS CENTER",
    "demand": 142,
    "latitude": 33.77347239,
    "longitude": 84.3887925
  },
  {
    "building_name": "SWANN BUILDING",
    "demand": 75,
    "latitude": 33.7718634,
    "longitude": -84.39421869
  },
  {
    "building_name": "TECH SQUARE RESEARCH BLDG",
    "demand": 243,
    "latitude": 33.77765773,
    "longitude": -84.38984682
  },
  {
    "building_name": "VAN LEER BLDG (ELECTRICAL & COMPUTER ENGINERING)",
    "demand": 406,
    "latitude": 33.77622264,
    "longitude": -84.39632843
  },
  {
    "building_name": "WEBER SPACE SCIENCE & TECHNOLOGY BUILDING III",
    "demand": 232,
    "latitude": 33.77293218,
    "longitude": -84.39653845
  },
  {
    "building_name": "WHITAKER BLDG (BIOMEDICAL ENGINEERING)",
    "demand": 158,
    "latitude": 33.77859506,
    "longitude": -84.39679846
  }
]
    
    stops_data = [
  {
    "stop_name": "Baker Building",
    "stop_lat": 33.78034577,
    "stop_lon": -84.39922995
  },
  {
    "stop_name": "Kendeda Building",
    "stop_lat": 33.77836,
    "stop_lon": -84.39956
  },
  {
    "stop_name": "Hemphill Ave & Curran St",
    "stop_lat": 33.78465382,
    "stop_lon": -84.40596684
  },
  {
    "stop_name": "Center St. Apartments & Hemphill Ave",
    "stop_lat": 33.77971,
    "stop_lon": -84.402416
  },
  {
    "stop_name": "GT Competition Center (575 14th Street)",
    "stop_lat": 33.78636825,
    "stop_lon": -84.40532109
  },
  {
    "stop_name": "14th St & State St",
    "stop_lat": 33.78613,
    "stop_lon": -84.3988
  },
  {
    "stop_name": "GTRI Conference Center",
    "stop_lat": 33.786282,
    "stop_lon": -84.395591
  },
  {
    "stop_name": "McCamish & 10th St.",
    "stop_lat": 33.78161169,
    "stop_lon": -84.39261135
  },
  {
    "stop_name": "Graduate Living Center",
    "stop_lat": 33.781533,
    "stop_lon": -84.396217
  },
  {
    "stop_name": "Cherry Emerson",
    "stop_lat": 33.778179,
    "stop_lon": -84.397328
  },
  {
    "stop_name": "10th St & MARTA EB",
    "stop_lat": 33.781368,
    "stop_lon": -84.386411
  },
  {
    "stop_name": "Piedmont Road EB",
    "stop_lat": 33.791475,
    "stop_lon": -84.374274
  },
  {
    "stop_name": "Clifton Road at Wesley EB",
    "stop_lat": 33.803435,
    "stop_lon": -84.333579
  },
  {
    "stop_name": "HSRB Emory",
    "stop_lat": 33.79411327,
    "stop_lon": -84.3172317
  },
  {
    "stop_name": "Woodruff Circle Transit Hub",
    "stop_lat": 33.792915,
    "stop_lon": -84.321659
  },
  {
    "stop_name": "Clifton Road at Wesley WB",
    "stop_lat": 33.803577,
    "stop_lon": -84.333504
  },
  {
    "stop_name": "Piedmont Road WB",
    "stop_lat": 33.79188,
    "stop_lon": -84.374156
  },
  {
    "stop_name": "10th St & MARTA WB",
    "stop_lat": 33.781522,
    "stop_lon": -84.386407
  },
  {
    "stop_name": "Klaus Building EB",
    "stop_lat": 33.777097,
    "stop_lon": -84.395484
  },
  {
    "stop_name": "Klaus Building WB",
    "stop_lat": 33.777485,
    "stop_lon": -84.395576
  },
  {
    "stop_name": "Nanotechnology",
    "stop_lat": 33.77832,
    "stop_lon": -84.398084
  },
  {
    "stop_name": "MARTA Midtown Station",
    "stop_lat": 33.78082162,
    "stop_lon": -84.38640592
  },
  {
    "stop_name": "Technology Square WB",
    "stop_lat": 33.77692,
    "stop_lon": -84.38978
  },
  {
    "stop_name": "5th Street Bridge WB",
    "stop_lat": 33.776943,
    "stop_lon": -84.391707
  },
  {
    "stop_name": "5th Street Bridge EB",
    "stop_lat": 33.77683087,
    "stop_lon": -84.39202062
  },
  {
    "stop_name": "Technology Square EB",
    "stop_lat": 33.7768,
    "stop_lon": -84.38975
  },
  {
    "stop_name": "College of Business",
    "stop_lat": 33.77677,
    "stop_lon": -84.387753
  },
  {
    "stop_name": "Academy of Medicine",
    "stop_lat": 33.778536,
    "stop_lon": -84.38724
  },
  {
    "stop_name": "Clough Commons",
    "stop_lat": 33.775274,
    "stop_lon": -84.396138
  },
  {
    "stop_name": "Publix at the Plaza",
    "stop_lat": 33.78067,
    "stop_lon": -84.388671
  },
  {
    "stop_name": "North Avenue Apts - To West Campus",
    "stop_lat": 33.769921,
    "stop_lon": -84.391754
  },
  {
    "stop_name": "Brown Residence Hall",
    "stop_lat": 33.771857,
    "stop_lon": -84.39192
  },
  {
    "stop_name": "Techwood Dr & Field Residence Hall",
    "stop_lat": 33.77406,
    "stop_lon": -84.39192
  },
  {
    "stop_name": "Techwood & 5th  - North",
    "stop_lat": 33.776757,
    "stop_lon": -84.39206
  },
  {
    "stop_name": "Russ Chandler Stadium",
    "stop_lat": 33.77699,
    "stop_lon": -84.39405
  },
  {
    "stop_name": "8th St & Hemphill Ave\u00a0",
    "stop_lat": 33.779631,
    "stop_lon": -84.40274
  },
  {
    "stop_name": "Paper Tricentennial",
    "stop_lat": 33.780598,
    "stop_lon": -84.404657
  },
  {
    "stop_name": "West Village",
    "stop_lat": 33.779616,
    "stop_lon": -84.404709
  },
  {
    "stop_name": "Ferst Dr & Hemphill Ave",
    "stop_lat": 33.77845,
    "stop_lon": -84.400824
  },
  {
    "stop_name": "Techwood Dr & 5th St - South",
    "stop_lat": 33.77646417,
    "stop_lon": -84.39209913
  },
  {
    "stop_name": "Techwood Dr & Bobby Dodd Way",
    "stop_lat": 33.77435646,
    "stop_lon": -84.39199586
  },
  {
    "stop_name": "COP & North Ave.",
    "stop_lat": 33.77066517,
    "stop_lon": -84.39218483
  },
  {
    "stop_name": "Couch Park",
    "stop_lat": 33.77796239,
    "stop_lon": -84.40201458
  },
  {
    "stop_name": "CRC & Stamps Health",
    "stop_lat": 33.7751,
    "stop_lon": -84.40265
  },
  {
    "stop_name": "North Avenue Apts - To East Campus",
    "stop_lat": 33.770206,
    "stop_lon": -84.391765
  },
  {
    "stop_name": "Fitten Hall",
    "stop_lat": 33.778273,
    "stop_lon": -84.404191
  },
  {
    "stop_name": "Ferst Drive & Student Center",
    "stop_lat": 33.77340351,
    "stop_lon": -84.39958306
  },
  {
    "stop_name": "Weber Building Loop",
    "stop_lat": 33.77315003,
    "stop_lon": -84.39701207
  },
  {
    "stop_name": "Ferst Dr & Cherry St",
    "stop_lat": 33.77228,
    "stop_lon": -84.39548
  },
  {
    "stop_name": "Student Center",
    "stop_lat": 33.77342787,
    "stop_lon": -84.39917304
  },
  {
    "stop_name": "Exhibition Hall",
    "stop_lat": 33.7749231,
    "stop_lon": -84.40253652
  },
  {
    "stop_name": "NARA",
    "stop_lat": 33.77075374,
    "stop_lon": -84.40354832
  },
  {
    "stop_name": "Science Square",
    "stop_lat": 33.76945105,
    "stop_lon": -84.40269918
  },
  {
    "stop_name": "Krone Engineered Biosystems Building on State St.",
    "stop_lat": 33.780209,
    "stop_lon": -84.399009
  },
  {
    "stop_name": "10th St\u00a0& Hemphill Ave",
    "stop_lat": 33.78162,
    "stop_lon": -84.40408
  },
  {
    "stop_name": "16th & Village St.",
    "stop_lat": 33.788701,
    "stop_lon": -84.402862
  },
  {
    "stop_name": "10th St at Holly St",
    "stop_lat": 33.781456,
    "stop_lon": -84.396152
  },
  {
    "stop_name": "Hemphill Ave & Curran St SB",
    "stop_lat": 33.78463356,
    "stop_lon": -84.40610449
  },
  {
    "stop_name": "Fowler Street NB",
    "stop_lat": 33.77653863,
    "stop_lon": -84.39357952
  },
  {
    "stop_name": "Fowler Street SB",
    "stop_lat": 33.77654174,
    "stop_lon": -84.39369976
  },
  {
    "stop_name": "Clifton Road & Gatewood EB",
    "stop_lat": 33.797186,
    "stop_lon": -84.322526
  },
  {
    "stop_name": "Clifton Road & Gatewood WB",
    "stop_lat": 33.796905,
    "stop_lon": -84.322092
  },
  {
    "stop_name": "Georgia Tech Police Department",
    "stop_lat": 33.781098,
    "stop_lon": -84.403725
  },
  {
    "stop_name": "Weber Building",
    "stop_lat": 33.772782,
    "stop_lon": -84.396964
  }
]
    
    print(f"Testing with {len(buildings_data)} buildings and {len(stops_data)} stops")
    print("\n1. Testing Stinger path detection...")
    
    try:
        stinger_path = RouteOptimizationService.get_stinger_path()
        print(f"   ✓ Stinger path: {stinger_path}")
        
        if not os.path.exists(stinger_path):
            print(f"   ✗ Stinger directory not found at {stinger_path}")
            return False
            
    except Exception as e:
        print(f"   ✗ Error detecting Stinger path: {e}")
        return False
    
    print("\n2. Testing data preparation...")
    try:
        buildings_file, sources_file, stops_file = RouteOptimizationService.prepare_optimization_data(
            buildings_data, stops_data
        )
        print(f"   ✓ Buildings file: {buildings_file}")
        print(f"   ✓ Sources file: {sources_file}")
        print(f"   ✓ Stops file: {stops_file}")
        
        # Verify files were created
        for file_path in [buildings_file, sources_file, stops_file]:
            if os.path.exists(file_path):
                print(f"   ✓ File exists: {os.path.basename(file_path)}")
            else:
                print(f"   ✗ File missing: {file_path}")
                
    except Exception as e:
        print(f"   ✗ Error preparing data: {e}")
        return False
    
    print("\n3. Testing route optimization...")
    try:
        optimization_result = RouteOptimizationService.run_stinger_optimization(
            buildings_data=buildings_data,
            stops_data=stops_data,
            fleet_size=5,
            target_lines=3,
            k_transfers=2,
            algorithm='genetic'
        )
        
        if optimization_result.get('success'):
            print("   ✓ Optimization completed successfully!")
            results = optimization_result.get('results', {})
            
            print(f"   ✓ Generated {results.get('total_routes', 0)} routes")
            
            metrics = results.get('metrics', {})
            if metrics:
                print(f"   ✓ Metrics - Cost: {metrics.get('total_cost', 'N/A')}, "
                      f"Coverage: {metrics.get('demand_coverage', 'N/A'):.2%}, "
                      f"Efficiency: {metrics.get('efficiency', 'N/A')}")
            
            # Print route details
            routes = results.get('routes', [])
            for i, route in enumerate(routes[:2], 1):  # Show first 2 routes
                print(f"   ✓ Route {i}: {route.get('route_id')} with {route.get('stops_count')} stops")
                stops = route.get('stops', [])
                for stop in stops[:3]:  # Show first 3 stops
                    print(f"      - {stop.get('stop_name')} ({stop.get('latitude'):.4f}, {stop.get('longitude'):.4f})")
                if len(stops) > 3:
                    print(f"      ... and {len(stops) - 3} more stops")
            
            return True
        else:
            print(f"   ✗ Optimization failed: {optimization_result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"   ✗ Error running optimization: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_django_models():
    """Test Django models integration."""
    print("\n4. Testing Django models integration...")
    
    try:
        # Test creating some sample data
        building = Building.objects.create(
            name="Test Building",
            latitude=33.77543753,
            longitude=-84.39390424
        )
        print(f"   ✓ Created building: {building}")
        
        bus_stop = BusStop.objects.create(
            name="Test Stop",
            latitude=33.777097,
            longitude=-84.395484,
            building=building
        )
        print(f"   ✓ Created bus stop: {bus_stop}")
        
        # Clean up
        bus_stop.delete()
        building.delete()
        print("   ✓ Test data cleaned up")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Error testing Django models: {e}")
        return False

if __name__ == "__main__":
    success = True
    
    try:
        # Test Django models first
        if not test_django_models():
            success = False
        
        # Test Stinger integration
        if not test_stinger_integration():
            success = False
            
    except Exception as e:
        print(f"Fatal error: {e}")
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ALL TESTS PASSED! Stinger integration is working correctly.")
        print("\nNext steps:")
        print("1. Start Django server: python3 manage.py runserver 8000")
        print("2. Test optimization endpoint: POST /api/optimization/test/")
        print("3. Upload CSV data via: POST /api/csv-upload/")
        print("4. Run optimization with real data: POST /api/optimize-routes/")
    else:
        print("❌ SOME TESTS FAILED! Check the errors above.")
    print("=" * 60)
    
    sys.exit(0 if success else 1)