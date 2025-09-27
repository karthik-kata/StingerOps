import { useEffect, useRef, useState, useCallback } from 'react'
import { Loader } from '@googlemaps/js-api-loader'
import api from './api'

const GoogleMap = ({ csvData, classesData, stopsData, busCount, apiKey }) => {
  const mapRef = useRef(null)
  const [map, setMap] = useState(null)
  const [markers, setMarkers] = useState([])
  const [isLoaded, setIsLoaded] = useState(false)
  const [error, setError] = useState(null)
  const [userLocation, setUserLocation] = useState(null)
  const [locationError, setLocationError] = useState(null)
  const [showTransit, setShowTransit] = useState(false)
  const [transitLayer, setTransitLayer] = useState(null)
  const [gtBusStops, setGtBusStops] = useState([])
  const [gtBusMarkers, setGtBusMarkers] = useState([])
  const [openInfoWindow, setOpenInfoWindow] = useState(null)

  // Get user's current location
  const getUserLocation = () => {
    if (!navigator.geolocation) {
      setLocationError('Geolocation is not supported by this browser')
      // Set Georgia Tech as default location
      setUserLocation({ lat: 33.7756, lng: -84.3963 })
      return
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const location = {
          lat: position.coords.latitude,
          lng: position.coords.longitude
        }
        setUserLocation(location)
        setLocationError(null)
      },
      (error) => {
        console.warn('Geolocation error:', error.message)
        setLocationError('Unable to get your location')
        // Set Georgia Tech as default location if geolocation fails
        setUserLocation({ lat: 33.7756, lng: -84.3963 })
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 300000 // 5 minutes
      }
    )
  }

  // Extract coordinates from CSV data
  const extractCoordinates = (data) => {
    if (!data || data.length === 0) return []
    
    const coordinates = []
    const possibleLatFields = ['lat', 'latitude', 'y', 'coord_y', 'y_coord']
    const possibleLngFields = ['lng', 'lng', 'longitude', 'x', 'coord_x', 'x_coord']
    
    data.forEach((row, index) => {
      let lat = null
      let lng = null
      
      // Try to find latitude field
      for (const field of possibleLatFields) {
        if (row[field] && !isNaN(parseFloat(row[field]))) {
          lat = parseFloat(row[field])
          break
        }
      }
      
      // Try to find longitude field
      for (const field of possibleLngFields) {
        if (row[field] && !isNaN(parseFloat(row[field]))) {
          lng = parseFloat(row[field])
          break
        }
      }
      
      if (lat !== null && lng !== null) {
        coordinates.push({
          lat,
          lng,
          data: row,
          index
        })
      }
    })
    
    return coordinates
  }

  // Load GT bus stops from CSV
  const loadGtBusStops = async () => {
    try {
      const response = await fetch('/gt_bus_stops_with_routes.csv')
      const csvText = await response.text()
      
      // Parse CSV properly handling quoted fields
      const lines = csvText.split('\n')
      const stops = []
      
      for (let i = 1; i < lines.length; i++) {
        if (lines[i].trim()) {
          const line = lines[i].trim()
          const values = []
          let current = ''
          let inQuotes = false
          
          // Parse CSV line properly handling quoted fields
          for (let j = 0; j < line.length; j++) {
            const char = line[j]
            if (char === '"') {
              inQuotes = !inQuotes
            } else if (char === ',' && !inQuotes) {
              values.push(current.trim())
              current = ''
            } else {
              current += char
            }
          }
          values.push(current.trim()) // Add the last field
          
          if (values.length >= 4) {
            const stop = {
              stop_name: values[0],
              latitude: parseFloat(values[1]),
              longitude: parseFloat(values[2]),
              routes_serving: values[3] || 'Unknown'
            }
            stops.push(stop)
          }
        }
      }
      
      setGtBusStops(stops)
    } catch (error) {
      console.error('Error loading GT bus stops:', error)
    }
  }

  // Load data from API
  const loadApiData = useCallback(async () => {
    try {
      const [apiStops, apiClasses] = await Promise.all([
        api.getBusStops(),
        api.getClasses()
      ])
      
      // Update state with API data
      if (apiStops.length > 0) {
        setGtBusStops(apiStops.map(stop => ({
          stop_name: stop.name,
          latitude: stop.latitude,
          longitude: stop.longitude,
          routes_serving: stop.routes_serving
        })))
      }
    } catch (error) {
      console.log('Error loading API data:', error.message)
    }
  }, [])

  // Get user location when component mounts
  useEffect(() => {
    getUserLocation()
    loadGtBusStops()
    loadApiData()
  }, [loadApiData])

  useEffect(() => {
    if (!apiKey) {
      setError('Google Maps API key is required')
      return
    }

    const loader = new Loader({
      apiKey: apiKey,
      version: 'weekly',
      libraries: ['places']
    })

            loader.load().then(() => {
              if (mapRef.current) {
                // Use user location if available, otherwise default to Georgia Tech
                const center = userLocation || { lat: 33.7756, lng: -84.3963 }
                
                const googleMap = new window.google.maps.Map(mapRef.current, {
                  center: center,
                  zoom: userLocation ? 15 : 16, // Closer zoom for Georgia Tech campus
                  mapTypeId: 'satellite',
                  mapTypeControl: true,
                  mapTypeControlOptions: {
                    style: window.google.maps.MapTypeControlStyle.HORIZONTAL_BAR,
                    position: window.google.maps.ControlPosition.TOP_CENTER,
                    mapTypeIds: [
                      window.google.maps.MapTypeId.ROADMAP,
                      window.google.maps.MapTypeId.SATELLITE,
                      window.google.maps.MapTypeId.HYBRID,
                      window.google.maps.MapTypeId.TERRAIN
                    ]
                  },
                  zoomControl: true,
                  streetViewControl: true,
                  fullscreenControl: true,
                  styles: [
                    {
                      featureType: 'all',
                      elementType: 'labels.text.fill',
                      stylers: [{ color: '#ffffff' }]
                    }
                  ]
                })

                // Create transit layer for bus routes (initially hidden)
                const transitLayerInstance = new window.google.maps.TransitLayer()
                setTransitLayer(transitLayerInstance)

                // Add click listener to map to close info windows when clicking empty space
                googleMap.addListener('click', () => {
                  if (openInfoWindow) {
                    openInfoWindow.close()
                    setOpenInfoWindow(null)
                  }
                })

        
        setMap(googleMap)
        setIsLoaded(true)
        setError(null)
      }
    }).catch((err) => {
      setError(`Failed to load Google Maps: ${err.message}`)
    })
  }, [apiKey, userLocation])

  // Add custom event listener for close button
  useEffect(() => {
    const handleCloseInfoWindow = (event) => {
      console.log('🔴 Close button clicked, event detail:', event.detail)
      if (openInfoWindow) {
        openInfoWindow.close()
        setOpenInfoWindow(null)
      }
    }
    
    window.addEventListener('closeInfoWindow', handleCloseInfoWindow)
    
    return () => {
      window.removeEventListener('closeInfoWindow', handleCloseInfoWindow)
    }
  }, [openInfoWindow])


  useEffect(() => {
    if (map && csvData) {
      // Clear existing markers
      markers.forEach(marker => marker.setMap(null))
      
      const coordinates = extractCoordinates(csvData)
      
      if (coordinates.length > 0) {
        const newMarkers = []
        
        // Create markers for each coordinate
        coordinates.forEach((coord, index) => {
          const marker = new window.google.maps.Marker({
            position: { lat: coord.lat, lng: coord.lng },
            map: map,
            title: `Data Point ${index + 1}`,
            animation: window.google.maps.Animation.DROP
          })
          
          // Create info window
      const infoWindow = new window.google.maps.InfoWindow({
        content: `
          <div style="padding: 10px; max-width: 300px; position: relative;">
            <div style="position: absolute; top: 0px; right: 0px; z-index: 1000; pointer-events: auto; width: 30px; height: 30px; background: #ff4444; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; box-shadow: 0 2px 4px rgba(0,0,0,0.3);" onclick="
              // Close this specific info window by dispatching a custom event with the marker index
              window.dispatchEvent(new CustomEvent('closeInfoWindow', { detail: { markerIndex: ${index} } }));
            ">
              <span style="color: white; font-size: 16px; font-weight: bold; user-select: none; pointer-events: none;">×</span>
            </div>
            <h3 style="margin: 0 0 10px 0; color: #333; padding-right: 25px;">Data Point ${index + 1}</h3>
            <div style="font-size: 12px; color: #666;">
              ${Object.entries(coord.data).map(([key, value]) => 
                `<div><strong>${key}:</strong> ${value}</div>`
              ).join('')}
            </div>
          </div>
        `
      })
          
          marker.addListener('click', () => {
            // Close any currently open info window
            if (openInfoWindow) {
              openInfoWindow.close()
            }
            
            // If clicking the same marker that's already open, close it
            if (openInfoWindow === infoWindow) {
              setOpenInfoWindow(null)
            } else {
              // Open the clicked marker's info window
              infoWindow.open(map, marker)
              setOpenInfoWindow(infoWindow)
            }
          })
          
          newMarkers.push(marker)
        })
        
        setMarkers(newMarkers)
        
        // Fit map to show all markers
        if (coordinates.length > 1) {
          const bounds = new window.google.maps.LatLngBounds()
          coordinates.forEach(coord => {
            bounds.extend({ lat: coord.lat, lng: coord.lng })
          })
          map.fitBounds(bounds)
        } else if (coordinates.length === 1) {
          map.setCenter({ lat: coordinates[0].lat, lng: coordinates[0].lng })
          map.setZoom(15)
        }
      }
    }
  }, [map, csvData])

  if (error) {
    return (
      <div className="map-error">
        <h3>Map Error</h3>
        <p>{error}</p>
        <p>Please check your Google Maps API key configuration.</p>
      </div>
    )
  }

  const centerOnUserLocation = () => {
    if (map && userLocation) {
      map.setCenter(userLocation)
      map.setZoom(15)
    } else if (map) {
      // Try to get location again
      getUserLocation()
    }
  }

  const toggleTransitLayer = () => {
    if (transitLayer) {
      if (showTransit) {
        transitLayer.setMap(null)
      } else {
        transitLayer.setMap(map)
      }
      setShowTransit(!showTransit)
    }
  }

  // Create GT bus stop markers
  const createGtBusStopMarkers = () => {
    if (!map || gtBusStops.length === 0) return

    // Clear existing GT bus stop markers
    gtBusMarkers.forEach(marker => marker.setMap(null))
    
    const newMarkers = []
    
    gtBusStops.forEach((stop, index) => {
      const marker = new window.google.maps.Marker({
        position: { lat: stop.latitude, lng: stop.longitude },
        map: map,
        title: stop.stop_name,
        icon: {
          url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" fill="#FF6B35" stroke="#FFFFFF" stroke-width="2"/>
              <text x="12" y="16" text-anchor="middle" fill="white" font-size="12" font-weight="bold">🚌</text>
            </svg>
          `),
          scaledSize: new window.google.maps.Size(24, 24),
          anchor: new window.google.maps.Point(12, 12)
        },
        animation: window.google.maps.Animation.DROP
      })
      
      // Create info window for each stop
      const routes = stop.routes_serving.split(',').map(route => route.trim())
      const routesHtml = routes.map(route => 
        `<span style="background: #FF6B35; color: white; padding: 2px 6px; border-radius: 10px; font-size: 10px; margin: 2px; display: inline-block;">${route}</span>`
      ).join('')
      
      const infoWindow = new window.google.maps.InfoWindow({
        content: `
          <div style="padding: 12px; max-width: 350px; position: relative;">
            <div style="position: absolute; top: 0px; right: 0px; z-index: 1000; pointer-events: auto; width: 30px; height: 30px; background: #ff4444; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; box-shadow: 0 2px 4px rgba(0,0,0,0.3);" onclick="
              // Close this specific info window by dispatching a custom event with the stop index
              window.dispatchEvent(new CustomEvent('closeInfoWindow', { detail: { stopIndex: ${index} } }));
            ">
              <span style="color: white; font-size: 16px; font-weight: bold; user-select: none; pointer-events: none;">×</span>
            </div>
            <h3 style="margin: 0 0 10px 0; color: #FF6B35; font-size: 16px; font-weight: bold; padding-right: 30px;">${stop.stop_name}</h3>
            <div style="margin: 0 0 8px 0;">
              <p style="margin: 0 0 5px 0; color: #333; font-size: 12px; font-weight: bold;">Routes:</p>
              <div style="line-height: 1.4;">${routesHtml}</div>
            </div>
            <p style="margin: 0; color: #999; font-size: 11px; font-style: italic;">GT Bus Stop</p>
          </div>
        `
      })
      
      marker.addListener('click', () => {
        // Close any currently open info window
        if (openInfoWindow) {
          openInfoWindow.close()
        }
        
        // If clicking the same marker that's already open, close it
        if (openInfoWindow === infoWindow) {
          setOpenInfoWindow(null)
        } else {
          // Open the clicked marker's info window
          infoWindow.open(map, marker)
          setOpenInfoWindow(infoWindow)
        }
      })
      
      newMarkers.push(marker)
    })
    
    setGtBusMarkers(newMarkers)
  }

  // Create GT bus stop markers when map and stops are ready
  useEffect(() => {
    createGtBusStopMarkers()
  }, [map, gtBusStops])

  return (
    <div className="map-container">
      <div className="map-header">
        <h3>Satellite Map View</h3>
                <div className="map-controls">
                  {userLocation && (
                    <button 
                      onClick={centerOnUserLocation}
                      className="my-location-button"
                      title="Center on my location"
                    >
                      📍 My Location
                    </button>
                  )}
                  <button 
                    onClick={toggleTransitLayer}
                    className={`transit-toggle-button ${showTransit ? 'active' : ''}`}
                    title={showTransit ? 'Hide bus routes' : 'Show bus routes'}
                  >
                    {showTransit ? '🚌 Hide Routes' : '🚌 Show Routes'}
                  </button>
                  <div className="map-stats">
                    {csvData && (
                      <span>📍 {markers.length} location{markers.length !== 1 ? 's' : ''} found</span>
                    )}
                    {classesData && (
                      <span>📚 {classesData.length} classes</span>
                    )}
                    {stopsData && (
                      <span>🚏 {stopsData.length} stops</span>
                    )}
                    {gtBusStops.length > 0 && (
                      <span>🚌 {gtBusStops.length} GT bus stop{gtBusStops.length !== 1 ? 's' : ''}</span>
                    )}
                    <span>🚌 {busCount} bus{busCount !== 1 ? 'es' : ''} available</span>
                  </div>
                </div>
      </div>
      <div 
        ref={mapRef} 
        className="google-map"
      />
              {!isLoaded && (
                <div className="map-loading">
                  <div className="spinner"></div>
                  <p>Loading Google Maps...</p>
                  {userLocation ? (
                    <p className="location-info">📍 Centered on your location</p>
                  ) : (
                    <p className="location-info">📍 Centered on Georgia Tech campus</p>
                  )}
                </div>
              )}
      {locationError && (
        <div className="location-warning">
          <p>⚠️ {locationError} - Using default location</p>
        </div>
      )}
    </div>
  )
}

export default GoogleMap
