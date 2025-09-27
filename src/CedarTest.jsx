import React from 'react'
import { CedarCopilot, setCedarStore } from 'cedar-os'

const CedarTest = () => {
  console.log('🧪 CedarTest component rendering...')
  
  React.useEffect(() => {
    console.log('🧪 CedarTest useEffect - initializing Cedar-OS...')
    try {
      setCedarStore({
        providerConfig: {
          provider: "openai",
          apiKey: import.meta.env.VITE_OPENAI_API_KEY,
          model: "gpt-3.5-turbo"
        }
      })
      console.log('🧪 CedarTest - Cedar-OS store initialized successfully')
    } catch (error) {
      console.error('🧪 CedarTest - Cedar-OS initialization error:', error)
    }
  }, [])

  console.log('🧪 CedarTest - About to render CedarCopilot')
  
  return (
    <div style={{ 
      position: 'fixed', 
      top: '10px', 
      left: '10px', 
      width: '400px', 
      height: '500px', 
      background: 'white', 
      border: '3px solid #ff0000', 
      borderRadius: '10px',
      zIndex: 99999,
      padding: '20px',
      boxShadow: '0 0 20px rgba(255,0,0,0.5)'
    }}>
      <h3>🧪 Cedar-OS Test (RED BORDER)</h3>
      <p>API Key: {import.meta.env.VITE_OPENAI_API_KEY ? 'Present' : 'Missing'}</p>
      <p>API Key length: {import.meta.env.VITE_OPENAI_API_KEY?.length || 0}</p>
      <div style={{ height: '300px', border: '2px solid #00ff00', margin: '10px 0', background: '#f0f0f0' }}>
        <p>About to render CedarCopilot...</p>
        <CedarCopilot
          llmProvider={{
            provider: "openai",
            apiKey: import.meta.env.VITE_OPENAI_API_KEY,
            model: "gpt-3.5-turbo"
          }}
        />
        <p>CedarCopilot rendered above</p>
      </div>
    </div>
  )
}

export default CedarTest
