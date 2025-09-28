import { useState } from 'react'
import api from './api'

const RouteOptimization = ({ onOptimizationComplete, onError }) => {
  const [isOptimizing, setIsOptimizing] = useState(false)
  const [optimizationResults, setOptimizationResults] = useState(null)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [params, setParams] = useState({
    fleet_size: 12,
    target_lines: 12,
    k_transfers: 2,
    transfer_penalty: 5.0,
    speed_kmh: 30.0,
    algorithm: 'genetic',
    use_existing_data: true
  })

  const handleParamChange = (key, value) => {
    setParams(prev => ({
      ...prev,
      [key]: parseFloat(value) || parseInt(value) || value
    }))
  }

  const runOptimization = async () => {
    setIsOptimizing(true)
    setOptimizationResults(null)
    
    try {
      const result = await api.optimizeRoutes(params)
      setOptimizationResults(result)
      if (onOptimizationComplete) {
        onOptimizationComplete(result)
      }
    } catch (error) {
      if (onError) {
        onError(`Optimization failed: ${error.message}`)
      }
    } finally {
      setIsOptimizing(false)
    }
  }

  const runTestOptimization = async () => {
    setIsOptimizing(true)
    setOptimizationResults(null)
    
    try {
      const result = await api.testOptimization()
      setOptimizationResults(result)
      if (onOptimizationComplete) {
        onOptimizationComplete(result)
      }
    } catch (error) {
      if (onError) {
        onError(`Test optimization failed: ${error.message}`)
      }
    } finally {
      setIsOptimizing(false)
    }
  }

  const formatMetric = (value, suffix = '') => {
    if (value === undefined || value === null) return 'N/A'
    if (typeof value === 'number') {
      return value.toLocaleString() + suffix
    }
    return value.toString()
  }

  return (
    <div className="route-optimization">
      <div className="optimization-header">
        <h3>🚌 Route Optimization</h3>
        <p>Generate optimal bus routes using AI-powered Stinger algorithm</p>
      </div>

      {/* Quick Actions */}
      <div className="quick-actions">
        <button 
          onClick={runTestOptimization}
          disabled={isOptimizing}
          className="test-button"
        >
          {isOptimizing ? '⏳ Running...' : '🧪 Test with Sample Data'}
        </button>
        <button 
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="toggle-advanced"
        >
          ⚙️ {showAdvanced ? 'Hide' : 'Show'} Advanced Options
        </button>
      </div>

      {/* Advanced Parameters */}
      {showAdvanced && (
        <div className="optimization-params">
          <h4>Optimization Parameters</h4>
          
          <div className="params-grid">
            <div className="param-group">
              <label htmlFor="fleet-size">Fleet Size</label>
              <input
                id="fleet-size"
                type="number"
                min="1"
                max="50"
                value={params.fleet_size}
                onChange={(e) => handleParamChange('fleet_size', e.target.value)}
                disabled={isOptimizing}
              />
              <small>Number of available buses (1-50)</small>
            </div>

            <div className="param-group">
              <label htmlFor="target-lines">Max Routes</label>
              <input
                id="target-lines"
                type="number"
                min="1"
                max="20"
                value={params.target_lines}
                onChange={(e) => handleParamChange('target_lines', e.target.value)}
                disabled={isOptimizing}
              />
              <small>Maximum routes to generate (1-20)</small>
            </div>

            <div className="param-group">
              <label htmlFor="k-transfers">Max Transfers</label>
              <input
                id="k-transfers"
                type="number"
                min="0"
                max="5"
                value={params.k_transfers}
                onChange={(e) => handleParamChange('k_transfers', e.target.value)}
                disabled={isOptimizing}
              />
              <small>Maximum transfers allowed (0-5)</small>
            </div>

            <div className="param-group">
              <label htmlFor="transfer-penalty">Transfer Penalty</label>
              <input
                id="transfer-penalty"
                type="number"
                min="0"
                max="30"
                step="0.5"
                value={params.transfer_penalty}
                onChange={(e) => handleParamChange('transfer_penalty', e.target.value)}
                disabled={isOptimizing}
              />
              <small>Time penalty in minutes (0-30)</small>
            </div>

            <div className="param-group">
              <label htmlFor="speed">Bus Speed</label>
              <input
                id="speed"
                type="number"
                min="10"
                max="80"
                step="5"
                value={params.speed_kmh}
                onChange={(e) => handleParamChange('speed_kmh', e.target.value)}
                disabled={isOptimizing}
              />
              <small>Average speed in km/h (10-80)</small>
            </div>

            <div className="param-group">
              <label htmlFor="algorithm">Algorithm</label>
              <select
                id="algorithm"
                value={params.algorithm}
                onChange={(e) => handleParamChange('algorithm', e.target.value)}
                disabled={isOptimizing}
              >
                <option value="genetic">Demand-Driven (Recommended)</option>
                <option value="greedy">Iterative</option>
                <option value="both">Both (Compare)</option>
              </select>
              <small>Optimization algorithm</small>
            </div>
          </div>

          <div className="run-optimization">
            <button 
              onClick={runOptimization}
              disabled={isOptimizing}
              className="optimize-button"
            >
              {isOptimizing ? '⏳ Optimizing Routes...' : '🚀 Run Optimization'}
            </button>
          </div>
        </div>
      )}

      {/* Optimization Progress */}
      {isOptimizing && (
        <div className="optimization-progress">
          <div className="progress-spinner"></div>
          <div className="progress-text">
            <h4>Optimizing Routes...</h4>
            <p>This may take 30-60 seconds. The Stinger algorithm is analyzing demand patterns and generating optimal routes.</p>
          </div>
        </div>
      )}

      {/* Results Display */}
          {optimizationResults && (
        <div className="optimization-results">
          <div className="results-header">
            <h4>✅ Optimization Complete</h4>
            {optimizationResults.data?.success ? (
              <span className="success-badge">Success</span>
            ) : (
              <span className="error-badge">Failed</span>
            )}
          </div>

          {optimizationResults.data?.success && optimizationResults.data?.results && (
            <>
              {/* Metrics Summary */}
              <div className="metrics-summary">
                <h5>Performance Metrics</h5>
                <div className="metrics-grid">
                  <div className="metric">
                    <span className="metric-value">
                      {formatMetric(optimizationResults.data.results?.total_routes, '')}
                    </span>
                    <span className="metric-label">Routes Generated</span>
                  </div>
                  <div className="metric">
                    <span className="metric-value">
                      {formatMetric(optimizationResults.data.results?.metrics?.total_cost, '')}
                    </span>
                    <span className="metric-label">Total Cost</span>
                  </div>
                  <div className="metric">
                    <span className="metric-value">
                      {formatMetric((optimizationResults.data.results?.metrics?.demand_coverage * 100).toFixed(1), '%')}
                    </span>
                    <span className="metric-label">Coverage</span>
                  </div>
                  <div className="metric">
                    <span className="metric-value">
                      {formatMetric(optimizationResults.data.results?.metrics?.efficiency?.toFixed(4), '')}
                    </span>
                    <span className="metric-label">Efficiency</span>
                  </div>
                </div>
              </div>

              {/* Routes List */}
              <div className="routes-list">
                <h5>Generated Routes</h5>
                {optimizationResults.data.results?.routes?.map((route, index) => (
                  <div key={route.route_id} className="route-card">
                    <div className="route-header">
                      <h6>Route {route.route_number}: {route.route_id}</h6>
                      <div className="route-stats">
                        <span>{route.stops_count} stops</span>
                        <span>{route.cycle_minutes.toFixed(1)} min cycle</span>
                        <span>Efficiency: {route.efficiency.toFixed(2)}</span>
                      </div>
                    </div>
                    <div className="route-stops">
                      <strong>Stops:</strong>
                      <ol className="stops-list">
                        {route.stops?.slice(0, 5).map((stop, stopIndex) => (
                          <li key={stopIndex}>
                            {stop.stop_name}
                            <small>({stop.latitude.toFixed(4)}, {stop.longitude.toFixed(4)})</small>
                          </li>
                        ))}
                        {route.stops?.length > 5 && (
                          <li className="more-stops">
                            ... and {route.stops.length - 5} more stops
                          </li>
                        )}
                      </ol>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}

          {!optimizationResults.data?.success && (
            <div className="error-details">
              <p>Error: {optimizationResults.data?.error || optimizationResults.error || 'Unknown error occurred'}</p>
            </div>
          )}
        </div>
      )}

      {/* Style definitions */}
      <style jsx>{`
        .route-optimization {
          padding: 20px;
          border: 1px solid #ddd;
          border-radius: 8px;
          background: white;
          margin: 10px 0;
        }

        .optimization-header h3 {
          margin: 0 0 10px 0;
          color: #333;
        }

        .optimization-header p {
          margin: 0;
          color: #666;
          font-size: 14px;
        }

        .quick-actions {
          display: flex;
          gap: 10px;
          margin: 20px 0;
        }

        .test-button, .toggle-advanced, .optimize-button {
          padding: 10px 16px;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          font-weight: 500;
          transition: all 0.2s;
        }

        .test-button {
          background: #e3f2fd;
          color: #1976d2;
        }

        .test-button:hover:not(:disabled) {
          background: #bbdefb;
        }

        .toggle-advanced {
          background: #f5f5f5;
          color: #333;
        }

        .toggle-advanced:hover {
          background: #e0e0e0;
        }

        .optimize-button {
          background: #4caf50;
          color: white;
          width: 100%;
          padding: 12px;
          font-size: 16px;
        }

        .optimize-button:hover:not(:disabled) {
          background: #45a049;
        }

        .optimize-button:disabled, .test-button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .optimization-params {
          margin: 20px 0;
          padding: 20px;
          border: 1px solid #e0e0e0;
          border-radius: 6px;
          background: #fafafa;
        }

        .params-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 15px;
          margin: 15px 0;
        }

        .param-group {
          display: flex;
          flex-direction: column;
        }

        .param-group label {
          font-weight: 500;
          margin-bottom: 5px;
          color: #333;
        }

        .param-group input, .param-group select {
          padding: 8px;
          border: 1px solid #ccc;
          border-radius: 4px;
          font-size: 14px;
        }

        .param-group small {
          color: #666;
          font-size: 12px;
          margin-top: 2px;
        }

        .optimization-progress {
          display: flex;
          align-items: center;
          gap: 15px;
          padding: 20px;
          background: #e8f5e8;
          border-radius: 6px;
          margin: 20px 0;
        }

        .progress-spinner {
          width: 24px;
          height: 24px;
          border: 3px solid #e0e0e0;
          border-top: 3px solid #4caf50;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .progress-text h4 {
          margin: 0 0 5px 0;
          color: #2e7d32;
        }

        .progress-text p {
          margin: 0;
          color: #2e7d32;
          font-size: 14px;
        }

        .optimization-results {
          margin: 20px 0;
          border: 1px solid #e0e0e0;
          border-radius: 6px;
          overflow: hidden;
        }

        .results-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 15px 20px;
          background: #f0f8ff;
          border-bottom: 1px solid #e0e0e0;
        }

        .results-header h4 {
          margin: 0;
          color: #1976d2;
        }

        .success-badge {
          background: #4caf50;
          color: white;
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 500;
        }

        .error-badge {
          background: #f44336;
          color: white;
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 500;
        }

        .metrics-summary, .routes-list {
          padding: 20px;
        }

        .metrics-summary {
          border-bottom: 1px solid #e0e0e0;
        }

        .metrics-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
          gap: 15px;
          margin: 15px 0 0 0;
        }

        .metric {
          text-align: center;
          padding: 15px;
          background: #f8f9fa;
          border-radius: 6px;
        }

        .metric-value {
          display: block;
          font-size: 20px;
          font-weight: bold;
          color: #1976d2;
          margin-bottom: 5px;
        }

        .metric-label {
          font-size: 12px;
          color: #666;
          text-transform: uppercase;
        }

        .routes-list h5 {
          margin: 0 0 15px 0;
          color: #333;
        }

        .route-card {
          border: 1px solid #e0e0e0;
          border-radius: 6px;
          margin-bottom: 15px;
          overflow: hidden;
        }

        .route-header {
          padding: 15px;
          background: #f8f9fa;
          border-bottom: 1px solid #e0e0e0;
        }

        .route-header h6 {
          margin: 0 0 8px 0;
          color: #333;
        }

        .route-stats {
          display: flex;
          gap: 15px;
          font-size: 12px;
          color: #666;
        }

        .route-stops {
          padding: 15px;
        }

        .stops-list {
          margin: 10px 0;
          padding-left: 20px;
        }

        .stops-list li {
          margin-bottom: 5px;
          font-size: 14px;
        }

        .stops-list small {
          color: #666;
          margin-left: 8px;
        }

        .more-stops {
          color: #666;
          font-style: italic;
        }

        .error-details {
          padding: 20px;
          color: #d32f2f;
          background: #ffebee;
        }
      `}</style>
    </div>
  )
}

export default RouteOptimization