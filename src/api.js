const API_BASE_URL = 'http://localhost:8000/api'

class BusSystemAPI {
  // CSV Upload
  async uploadCSV(file, dataType) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('data_type', dataType)

    const response = await fetch(`${API_BASE_URL}/csv-upload/upload_csv/`, {
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
    const response = await fetch(`${API_BASE_URL}/bus-count/set_bus_count/`, {
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
    const response = await fetch(`${API_BASE_URL}/bus-count/get_bus_count/`)
    
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
