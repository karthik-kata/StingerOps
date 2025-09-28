"use client"

import { useState, useCallback, useEffect } from 'react'
import Papa from 'papaparse'
import GoogleMap from './GoogleMap'
import RouteOptimization from './RouteOptimization'
import api from './api'
import './App.css'

function App() {
  const [csvData, setCsvData] = useState(null)
  const [classesData, setClassesData] = useState(null)
  const [stopsData, setStopsData] = useState(null)
  const [isDragOver, setIsDragOver] = useState(false)
  const [error, setError] = useState(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [apiKey] = useState(import.meta.env.VITE_GOOGLE_MAPS_API_KEY)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [showOptimizationModal, setShowOptimizationModal] = useState(false)
  const [showAboutModal, setShowAboutModal] = useState(false)
  const [busCount, setBusCount] = useState(5)
  const [uploadType, setUploadType] = useState('general') // 'general', 'classes', 'stops'
  const [optimizedRoutes, setOptimizedRoutes] = useState(null)
  const [buildingsData, setBuildingsData] = useState(null)
  const [sourcesData, setSourcesData] = useState(null)

  const handleFileUpload = useCallback(async (file, type = uploadType) => {
    if (!file) return
    
    if (file.type !== 'text/csv' && !file.name.endsWith('.csv')) {
      setError('Please upload a CSV file')
      return
    }

    setIsProcessing(true)
    setError(null)

    try {
      // Upload to Django API
      const result = await api.uploadCSV(file, type)
      
      // Also parse locally for immediate display
      Papa.parse(file, {
        header: true,
        skipEmptyLines: true,
        complete: (results) => {
          setIsProcessing(false)
          if (results.errors.length > 0) {
            setError(`Error parsing CSV: ${results.errors[0].message}`)
            return
          }
          
          // Store data based on type
          switch (type) {
            case 'classes':
              setClassesData(results.data)
              break
            case 'stops':
              setStopsData(results.data)
              break
            case 'buildings':
              setBuildingsData(results.data)
              break
            case 'sources':
              setSourcesData(results.data)
              break
            default:
              setCsvData(results.data)
          }
        },
        error: (error) => {
          setIsProcessing(false)
          setError(`Error reading file: ${error.message}`)
        }
      })
    } catch (error) {
      setIsProcessing(false)
      setError(`Error uploading to server: ${error.message}`)
    }
  }, [uploadType])

  const handleFileInputChange = (e) => {
    const file = e.target.files[0]
    handleFileUpload(file)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragOver(false)
    const file = e.dataTransfer.files[0]
    handleFileUpload(file)
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    setIsDragOver(false)
  }

  const resetData = () => {
    setCsvData(null)
    setClassesData(null)
    setStopsData(null)
    setBuildingsData(null)
    setSourcesData(null)
    setOptimizedRoutes(null)
    setError(null)
  }

  // Handle optimization completion
  const handleOptimizationComplete = useCallback((result) => {
    console.log('Optimization result:', result)
    if (result?.data?.results?.routes) {
      console.log('Setting optimized routes:', result.data.results.routes)
      setOptimizedRoutes(result.data.results.routes)
    } else {
      console.log('No routes found in result:', result)
    }
  }, [])

  // Handle optimization errors
  const handleOptimizationError = useCallback((errorMessage) => {
    setError(errorMessage)
  }, [])

  // Handle bus count changes
  const handleBusCountChange = useCallback(async (newCount) => {
    try {
      await api.setBusCount(newCount)
      setBusCount(newCount)
    } catch (error) {
      setError(`Error updating bus count: ${error.message}`)
    }
  }, [])
  
  // Test function to create mock routes for visualization testing
  const createTestRoutes = useCallback(() => {
    const testRoutes = [
      {
        route_number: 1,
        route_id: 'TEST_1',
        stops_count: 3,
        cycle_minutes: 15.5,
        demand_coverage: 1200,
        efficiency: 85.5,
        stops: [
          { stop_order: 1, stop_name: 'Klaus Building', latitude: 33.777097, longitude: -84.395484 },
          { stop_order: 2, stop_name: 'Student Center', latitude: 33.77342787, longitude: -84.39917304 },
          { stop_order: 3, stop_name: 'Tech Tower', latitude: 33.7756, longitude: -84.3963 }
        ]
      },
      {
        route_number: 2,
        route_id: 'TEST_2',
        stops_count: 4,
        cycle_minutes: 22.0,
        demand_coverage: 950,
        efficiency: 72.3,
        stops: [
          { stop_order: 1, stop_name: 'College of Business', latitude: 33.77677, longitude: -84.387753 },
          { stop_order: 2, stop_name: 'Library', latitude: 33.7750, longitude: -84.3960 },
          { stop_order: 3, stop_name: 'Recreation Center', latitude: 33.7745, longitude: -84.4020 },
          { stop_order: 4, stop_name: 'North Campus', latitude: 33.7780, longitude: -84.3980 }
        ]
      }
    ]
    console.log('Setting test routes:', testRoutes)
    setOptimizedRoutes(testRoutes)
  }, [])

  // Load data from API on component mount
  useEffect(() => {
    const loadData = async () => {
      try {
        // Load bus count
        const busData = await api.getBusCount()
        setBusCount(busData.count)
        
        // Load existing data
        const [stops, classes, buildings, sources] = await Promise.all([
          api.getBusStops(),
          api.getClasses(),
          api.getBuildings(),
          api.getSources()
        ])
        
        if (stops.length > 0) {
          setStopsData(stops)
        }
        if (classes.length > 0) {
          setClassesData(classes)
        }
        if (buildings.length > 0) {
          setBuildingsData(buildings)
        }
        if (sources.length > 0) {
          setSourcesData(sources)
        }
      } catch (error) {
        console.log('No existing data or API not available:', error.message)
      }
    }
    
    loadData()
  }, [])


  const hasLocationData = csvData && csvData.some(row => {
    const possibleLatFields = ['lat', 'latitude', 'y', 'coord_y', 'y_coord']
    const possibleLngFields = ['lng', 'lng', 'longitude', 'x', 'coord_x', 'x_coord']
    
    const hasLat = possibleLatFields.some(field => row[field] && !isNaN(parseFloat(row[field])))
    const hasLng = possibleLngFields.some(field => row[field] && !isNaN(parseFloat(row[field])))
    
    return hasLat && hasLng
  })

  return (
    <div className="app">
              {/* Full Screen Map */}
              <div className="fullscreen-map">
                <GoogleMap 
                  csvData={csvData} 
                  classesData={classesData}
                  stopsData={stopsData}
                  buildingsData={buildingsData}
                  sourcesData={sourcesData}
                  optimizedRoutes={optimizedRoutes}
                  busCount={busCount}
                  apiKey={apiKey} 
                />
              </div>

      {/* Floating Action Buttons */}
      <div className="floating-buttons">
        <button 
          className="floating-button upload-button"
          onClick={() => setShowUploadModal(true)}
          title="Upload CSV Files"
        >
          📁 Upload Data
        </button>
        <button 
          className="floating-button optimize-button"
          onClick={() => setShowOptimizationModal(true)}
          title="Optimize Routes"
        >
          🚌 Optimize Routes
        </button>
        <button 
          className="floating-button test-button"
          onClick={createTestRoutes}
          title="Test Route Visualization"
        >
          🧪 Test Routes
        </button>
      </div>

      {/* About Button */}
      <button 
        className="about-button"
        onClick={() => setShowAboutModal(true)}
        title="Learn how to use this website"
      >
        ℹ️ About
      </button>


              {/* Data Status Indicator */}
              {(csvData || classesData || stopsData || buildingsData || sourcesData || optimizedRoutes) && (
                <div className="data-status">
                  {csvData && <span>📍 {csvData.length} general rows</span>}
                  {classesData && <span>📚 {classesData.length} classes</span>}
                  {stopsData && <span>🚏 {stopsData.length} stops</span>}
                  {buildingsData && <span>🏢 {buildingsData.length} buildings</span>}
                  {sourcesData && <span>🏠 {sourcesData.length} sources</span>}
                  {optimizedRoutes && <span>🚌 {optimizedRoutes.length} routes</span>}
                  {hasLocationData && <span>• Location data detected</span>}
                </div>
              )}

              {/* Upload Modal */}
              {showUploadModal && (
                <div className="upload-modal">
                  <div className="upload-modal-content">
                    <div className="modal-header">
                      <h2>Upload CSV Files & Configure Buses</h2>
                      <button 
                        className="close-button"
                        onClick={() => setShowUploadModal(false)}
                      >
                        ×
                      </button>
                    </div>
                    
                    <div className="modal-body">
                      {/* Bus Count Control */}
                      <div className="bus-control-section">
                        <h3>🚌 Bus Configuration</h3>
                        <div className="bus-count-control">
                          <label htmlFor="bus-count">Number of Buses:</label>
                          <input
                            type="number"
                            id="bus-count"
                            min="1"
                            max="20"
                            value={busCount}
                            onChange={(e) => handleBusCountChange(parseInt(e.target.value) || 1)}
                            className="bus-count-input"
                          />
                        </div>
                      </div>

                      {/* CSV Upload Tabs */}
                      <div className="csv-upload-tabs">
                        <div className="tab-buttons">
                          <button 
                            className={`tab-button ${uploadType === 'general' ? 'active' : ''}`}
                            onClick={() => setUploadType('general')}
                          >
                            📍 General Data
                          </button>
                          <button 
                            className={`tab-button ${uploadType === 'classes' ? 'active' : ''}`}
                            onClick={() => setUploadType('classes')}
                          >
                            📚 Classes
                          </button>
                          <button 
                            className={`tab-button ${uploadType === 'stops' ? 'active' : ''}`}
                            onClick={() => setUploadType('stops')}
                          >
                            🚏 Stops
                          </button>
                          <button 
                            className={`tab-button ${uploadType === 'buildings' ? 'active' : ''}`}
                            onClick={() => setUploadType('buildings')}
                          >
                            🏢 Buildings
                          </button>
                          <button 
                            className={`tab-button ${uploadType === 'sources' ? 'active' : ''}`}
                            onClick={() => setUploadType('sources')}
                          >
                            🏠 Sources
                          </button>
                        </div>

                        <div className="tab-content">
                          {/* General Data Tab */}
                          {uploadType === 'general' && (
                            <div className="upload-section">
                              <h3>General Data CSV</h3>
                              <p>Upload general location data or any CSV with coordinates</p>
                              <div 
                                className={`upload-area ${isDragOver ? 'drag-over' : ''}`}
                                onDrop={handleDrop}
                                onDragOver={handleDragOver}
                                onDragLeave={handleDragLeave}
                              >
                                <div className="upload-content">
                                  <div className="upload-icon">📁</div>
                                  <h4>Upload General CSV</h4>
                                  <p>Drag and drop your CSV file here, or click to browse</p>
                                  <input
                                    type="file"
                                    accept=".csv"
                                    onChange={(e) => handleFileUpload(e.target.files[0], 'general')}
                                    className="file-input"
                                    id="general-csv-upload"
                                  />
                                  <label htmlFor="general-csv-upload" className="upload-button">
                                    Choose File
                                  </label>
                                </div>
                              </div>
                            </div>
                          )}

                          {/* Classes Tab */}
                          {uploadType === 'classes' && (
                            <div className="upload-section">
                              <h3>Classes CSV</h3>
                              <p>Upload class schedule data with locations and times</p>
                              <div 
                                className={`upload-area ${isDragOver ? 'drag-over' : ''}`}
                                onDrop={(e) => {
                                  e.preventDefault()
                                  setIsDragOver(false)
                                  const file = e.dataTransfer.files[0]
                                  handleFileUpload(file, 'classes')
                                }}
                                onDragOver={handleDragOver}
                                onDragLeave={handleDragLeave}
                              >
                                <div className="upload-content">
                                  <div className="upload-icon">📚</div>
                                  <h4>Upload Classes CSV</h4>
                                  <p>Drag and drop your classes CSV file here, or click to browse</p>
                                  <input
                                    type="file"
                                    accept=".csv"
                                    onChange={(e) => handleFileUpload(e.target.files[0], 'classes')}
                                    className="file-input"
                                    id="classes-csv-upload"
                                  />
                                  <label htmlFor="classes-csv-upload" className="upload-button">
                                    Choose File
                                  </label>
                                </div>
                              </div>
                            </div>
                          )}

                          {/* Stops Tab */}
                          {uploadType === 'stops' && (
                            <div className="upload-section">
                              <h3>Stops CSV</h3>
                              <p>Upload bus stop data with coordinates and route information</p>
                              <div 
                                className={`upload-area ${isDragOver ? 'drag-over' : ''}`}
                                onDrop={(e) => {
                                  e.preventDefault()
                                  setIsDragOver(false)
                                  const file = e.dataTransfer.files[0]
                                  handleFileUpload(file, 'stops')
                                }}
                                onDragOver={handleDragOver}
                                onDragLeave={handleDragLeave}
                              >
                                <div className="upload-content">
                                  <div className="upload-icon">🚏</div>
                                  <h4>Upload Stops CSV</h4>
                                  <p>Drag and drop your stops CSV file here, or click to browse</p>
                                  <input
                                    type="file"
                                    accept=".csv"
                                    onChange={(e) => handleFileUpload(e.target.files[0], 'stops')}
                                    className="file-input"
                                    id="stops-csv-upload"
                                  />
                                  <label htmlFor="stops-csv-upload" className="upload-button">
                                    Choose File
                                  </label>
                                </div>
                              </div>
                            </div>
                          )}

                          {/* Buildings Tab */}
                          {uploadType === 'buildings' && (
                            <div className="upload-section">
                              <h3>Buildings CSV</h3>
                              <p>Upload building data with demand information for route optimization</p>
                              <div 
                                className={`upload-area ${isDragOver ? 'drag-over' : ''}`}
                                onDrop={(e) => {
                                  e.preventDefault()
                                  setIsDragOver(false)
                                  const file = e.dataTransfer.files[0]
                                  handleFileUpload(file, 'buildings')
                                }}
                                onDragOver={handleDragOver}
                                onDragLeave={handleDragLeave}
                              >
                                <div className="upload-content">
                                  <div className="upload-icon">🏢</div>
                                  <h4>Upload Buildings CSV</h4>
                                  <p>Required columns: building_name, demand, latitude, longitude</p>
                                  <input
                                    type="file"
                                    accept=".csv"
                                    onChange={(e) => handleFileUpload(e.target.files[0], 'buildings')}
                                    className="file-input"
                                    id="buildings-csv-upload"
                                  />
                                  <label htmlFor="buildings-csv-upload" className="upload-button">
                                    Choose File
                                  </label>
                                </div>
                              </div>
                            </div>
                          )}

                          {/* Sources Tab */}
                          {uploadType === 'sources' && (
                            <div className="upload-section">
                              <h3>Sources CSV</h3>
                              <p>Upload origin points data (dorms, parking lots, etc.) for route optimization</p>
                              <div 
                                className={`upload-area ${isDragOver ? 'drag-over' : ''}`}
                                onDrop={(e) => {
                                  e.preventDefault()
                                  setIsDragOver(false)
                                  const file = e.dataTransfer.files[0]
                                  handleFileUpload(file, 'sources')
                                }}
                                onDragOver={handleDragOver}
                                onDragLeave={handleDragLeave}
                              >
                                <div className="upload-content">
                                  <div className="upload-icon">🏠</div>
                                  <h4>Upload Sources CSV</h4>
                                  <p>Required columns: source_name, latitude, longitude, demand</p>
                                  <input
                                    type="file"
                                    accept=".csv"
                                    onChange={(e) => handleFileUpload(e.target.files[0], 'sources')}
                                    className="file-input"
                                    id="sources-csv-upload"
                                  />
                                  <label htmlFor="sources-csv-upload" className="upload-button">
                                    Choose File
                                  </label>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Processing and Error States */}
                      {isProcessing && (
                        <div className="processing">
                          <div className="spinner"></div>
                          <p>Processing {uploadType} CSV file...</p>
                        </div>
                      )}
                      
                      {error && (
                        <div className="error">
                          <p>{error}</p>
      </div>
                      )}

                      {/* Data Preview Section */}
                      {(csvData || classesData || stopsData || buildingsData) && (
                        <div className="data-preview-section">
                          <div className="data-header">
                            <h3>Data Preview</h3>
                            <button onClick={resetData} className="reset-button">
                              Clear All Data
        </button>
                          </div>
                          
                          <div className="data-summary">
                            {csvData && (
                              <div className="data-summary-item">
                                <h4>📍 General Data: {csvData.length} rows</h4>
                                <p>Columns: {csvData.length > 0 ? Object.keys(csvData[0]).length : 0}</p>
                              </div>
                            )}
                            {classesData && (
                              <div className="data-summary-item">
                                <h4>📚 Classes: {classesData.length} rows</h4>
                                <p>Columns: {classesData.length > 0 ? Object.keys(classesData[0]).length : 0}</p>
                              </div>
                            )}
                            {stopsData && (
                              <div className="data-summary-item">
                                <h4>🚏 Stops: {stopsData.length} rows</h4>
                                <p>Columns: {stopsData.length > 0 ? Object.keys(stopsData[0]).length : 0}</p>
                              </div>
                            )}
                            {buildingsData && (
                              <div className="data-summary-item">
                                <h4>🏢 Buildings: {buildingsData.length} rows</h4>
                                <p>Columns: {buildingsData.length > 0 ? Object.keys(buildingsData[0]).length : 0}</p>
                              </div>
                            )}
                          </div>
                        </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* About Modal */}
      {showAboutModal && (
        <div className="about-modal">
          <div className="about-modal-content">
            <div className="modal-header">
              <h2>🚌 Georgia Tech Bus System</h2>
              <button 
                className="close-button"
                onClick={() => setShowAboutModal(false)}
              >
                ×
              </button>
            </div>
            
            <div className="about-content">
              <div className="about-section">
                <h3>📍 How to Use This Website</h3>
                <p>This interactive map helps you explore Georgia Tech's bus system and upload your own location data.</p>
              </div>

              <div className="about-section">
                <h3>🗺️ Map Features</h3>
                <ul>
                  <li><strong>Georgia Tech Campus View:</strong> The map is centered on Georgia Tech with bus stops already displayed</li>
                  <li><strong>Bus Stop Information:</strong> Click on any red bus stop marker to see route information</li>
                  <li><strong>Interactive Markers:</strong> Click markers to open detailed information windows</li>
                  <li><strong>Close Windows:</strong> Click the red X button to close information windows</li>
                </ul>
              </div>

              <div className="about-section">
                <h3>📁 Upload Your Data</h3>
                <ul>
                  <li><strong>General Data:</strong> Upload any CSV with latitude/longitude coordinates</li>
                  <li><strong>Classes Data:</strong> Upload class schedules with locations and times</li>
                  <li><strong>Stops Data:</strong> Upload bus stop data with route information</li>
                  <li><strong>Bus Configuration:</strong> Adjust the number of buses (1-20)</li>
                </ul>
              </div>

              <div className="about-section">
                <h3>📊 Data Requirements</h3>
                <ul>
                  <li><strong>CSV Format:</strong> Files must be in CSV format (.csv)</li>
                  <li><strong>Coordinates:</strong> Include 'latitude' and 'longitude' columns</li>
                  <li><strong>Bus Stops:</strong> Include 'stop_name' and 'routes_serving' columns</li>
                  <li><strong>Classes:</strong> Include location and time information</li>
                </ul>
              </div>

              <div className="about-section">
                <h3>🎯 Getting Started</h3>
                <ol>
                  <li>Explore the map to see existing Georgia Tech bus stops</li>
                  <li>Click "📁 Upload CSV" to add your own data</li>
                  <li>Choose the appropriate data type (General/Classes/Stops)</li>
                  <li>Upload your CSV file and see it displayed on the map</li>
                  <li>Adjust bus count settings as needed</li>
                </ol>
              </div>

              <div className="about-section">
                <h3>💡 Tips</h3>
                <ul>
                  <li>Use the zoom controls to explore different areas</li>
                  <li>Click and drag to pan around the map</li>
                  <li>Information windows show detailed data for each marker</li>
                  <li>You can upload multiple types of data simultaneously</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}

              {/* Optimization Modal */}
              {showOptimizationModal && (
                <div className="optimization-modal">
                  <div className="optimization-modal-content">
                    <div className="modal-header">
                      <h2>Route Optimization</h2>
                      <button 
                        className="close-button"
                        onClick={() => setShowOptimizationModal(false)}
                      >
                        ×
                      </button>
                    </div>
                    
                    <div className="modal-body">
                      <RouteOptimization 
                        onOptimizationComplete={handleOptimizationComplete}
                        onError={handleOptimizationError}
                      />
                    </div>
                  </div>
                </div>
              )}


      </div>
  )
}

export default App
