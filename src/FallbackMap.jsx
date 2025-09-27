const FallbackMap = ({ csvData }) => {
  return (
    <div className="map-container">
      <div className="map-header">
        <h3>Satellite Map View</h3>
        <div className="map-stats">
          <span>🗺️ Interactive Map Ready</span>
        </div>
      </div>
      <div className="fallback-map">
        <div className="map-placeholder">
          <div className="map-icon">🌍</div>
          <h3>Satellite Map View</h3>
          <p>Enter your Google Maps API key to enable interactive satellite view</p>
          <div className="map-features">
            <div className="feature">
              <span className="feature-icon">🛰️</span>
              <span>Satellite Imagery</span>
            </div>
            <div className="feature">
              <span className="feature-icon">📍</span>
              <span>Location Markers</span>
            </div>
            <div className="feature">
              <span className="feature-icon">🔍</span>
              <span>Zoom & Pan</span>
            </div>
            <div className="feature">
              <span className="feature-icon">🗺️</span>
              <span>Multiple Map Types</span>
            </div>
          </div>
          {csvData && (
            <div className="data-preview">
              <p><strong>CSV Data Loaded:</strong> {csvData.length} rows</p>
              <p>Location data will be plotted on the map once API key is provided</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default FallbackMap
