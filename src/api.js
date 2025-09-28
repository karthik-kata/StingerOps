const API_BASE_URL = 'http://localhost:8000/api'

class BusSystemAPI {
  // CSV Upload
  async uploadCSV(file, dataType) {
    const formData = new FormData()
    formData.append('file', file)
    
    // Route to specific endpoints based on data type
    let endpoint
    switch (dataType) {
      case 'buildings':
        endpoint = `${API_BASE_URL}/buildings/`
        break
      case 'stops':
        endpoint = `${API_BASE_URL}/bus-stops/`
        break
      case 'sources':
        endpoint = `${API_BASE_URL}/sources/`
        break
      case 'classes':
      case 'general':
      default:
        // Classes and general CSV still use the generic endpoint
        formData.append('data_type', dataType)
        endpoint = `${API_BASE_URL}/csv-upload/`
        break
    }

    const response = await fetch(endpoint, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return await response.json()
  }

  // Bus Count Management
  async setBusCount(count) {
    const response = await fetch(`${API_BASE_URL}/bus-count/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ count }),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return await response.json()
  }

  async getBusCount() {
    const response = await fetch(`${API_BASE_URL}/bus-count/`)
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return await response.json()
  }

  // Data Retrieval
  async getBusStops() {
    const response = await fetch(`${API_BASE_URL}/bus-stops/`)
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return await response.json()
  }

  async getClasses() {
    const response = await fetch(`${API_BASE_URL}/classes/`)
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return await response.json()
  }

  async getBuses() {
    const response = await fetch(`${API_BASE_URL}/buses/`)
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return await response.json()
  }

  async getRoutes() {
    const response = await fetch(`${API_BASE_URL}/routes/`)
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return await response.json()
  }

  // Route Optimization
  async optimizeRoutes(params = {}) {
    const defaultParams = {
      fleet_size: 12,
      target_lines: 12,
      k_transfers: 2,
      transfer_penalty: 5.0,
      speed_kmh: 30.0,
      algorithm: 'genetic',
      use_existing_data: true
    }

    const response = await fetch(`${API_BASE_URL}/optimize-routes/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ ...defaultParams, ...params }),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
    }

    return await response.json()
  }

  async testOptimization() {
    const response = await fetch(`${API_BASE_URL}/optimization/test/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({}),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
    }

    return await response.json()
  }

  async applyOptimizedRoutes(optimizationId, clearExisting = false) {
    const response = await fetch(`${API_BASE_URL}/apply-routes/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        optimization_id: optimizationId, 
        clear_existing: clearExisting 
      }),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
    }

    return await response.json()
  }

  // System Data
  async getBuildings() {
    const response = await fetch(`${API_BASE_URL}/buildings/`)
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return await response.json()
  }

  async getSources() {
    const response = await fetch(`${API_BASE_URL}/sources/`)
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return await response.json()
  }

  async getSystemOverview() {
    const response = await fetch(`${API_BASE_URL}/overview/`)
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return await response.json()
  }

  // API Status
  async getStatus() {
    const response = await fetch(`${API_BASE_URL}/status/`)
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return await response.json()
  }
}

export default new BusSystemAPI()
