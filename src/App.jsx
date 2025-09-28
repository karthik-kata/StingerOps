"use client"

import { useState, useCallback, useEffect } from 'react'
import Papa from 'papaparse'
import GoogleMap from './GoogleMap'
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
  const [showAboutModal, setShowAboutModal] = useState(false)
  const [busCount, setBusCount] = useState(5)
  const [uploadType, setUploadType] = useState('general') // 'general', 'classes', 'stops'

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
    setError(null)
  }

  // Handle bus count changes
  const handleBusCountChange = useCallback(async (newCount) => {
    try {
      await api.setBusCount(newCount)
      setBusCount(newCount)
    } catch (error) {
      setError(`Error updating bus count: ${error.message}`)
    }
  }, [])

  // Load data from API on component mount
  useEffect(() => {
    const loadData = async () => {
      try {
        // Load bus count
        const busData = await api.getBusCount()
        setBusCount(busData.count)
        
        // Load existing data
        const [stops, classes] = await Promise.all([
          api.getBusStops(),
          api.getClasses()
        ])
        
        if (stops.length > 0) {
          setStopsData(stops)
        }
        if (classes.length > 0) {
          setClassesData(classes)
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
                  busCount={busCount}
                  apiKey={apiKey} 
                />
              </div>

      {/* Floating Upload Button */}
      <button 
        className="floating-upload-button"
        onClick={() => setShowUploadModal(true)}
        title="Upload CSV File"
      >
        📁 Upload CSV
      </button>

      {/* About Button */}
      <button 
        className="about-button"
        onClick={() => setShowAboutModal(true)}
        title="Learn how to use this website"
      >
        ℹ️ About
      </button>


              {/* Data Status Indicator */}
              {(csvData || classesData || stopsData) && (
                <div className="data-status">
                  {csvData && <span>📍 {csvData.length} general rows</span>}
                  {classesData && <span>📚 {classesData.length} classes</span>}
                  {stopsData && <span>🚏 {stopsData.length} stops</span>}
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
                      {(csvData || classesData || stopsData) && (
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


      </div>
  )
}

export default App
