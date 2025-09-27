"use client"

import { useState, useEffect } from 'react'
import { CedarCopilot, setCedarStore } from 'cedar-os'

const CedarGuide = ({ isOpen, onClose }) => {
  const [isMinimized, setIsMinimized] = useState(false)
  const [isCedarLoaded, setIsCedarLoaded] = useState(false)
  const [cedarError, setCedarError] = useState(null)

  useEffect(() => {
    // Initialize Cedar-OS store
    try {
      console.log('🌲 Initializing Cedar-OS...')
      console.log('API Key available:', !!import.meta.env.VITE_OPENAI_API_KEY)
      console.log('API Key length:', import.meta.env.VITE_OPENAI_API_KEY?.length || 0)
      
      setCedarStore({
        providerConfig: {
          provider: "openai",
          apiKey: import.meta.env.VITE_OPENAI_API_KEY,
          model: "gpt-3.5-turbo"
        }
      })
      console.log('✅ Cedar-OS store initialized')
      setIsCedarLoaded(true)
    } catch (error) {
      console.error('❌ Cedar-OS initialization error:', error)
      setCedarError(error.message)
    }
  }, [])

  if (!isOpen) return null

  return (
    <div className={`cedar-guide ${isMinimized ? 'minimized' : ''}`}>
      <div className="chat-header" onClick={() => setIsMinimized(!isMinimized)}>
        <div className="chat-title">
          <span className="chat-icon">🌲</span>
          <span>Cedar AI Guide</span>
          <span className="cedar-status">✓ Real Cedar-OS</span>
        </div>
        <div className="chat-controls">
          <button 
            className="minimize-btn"
            onClick={(e) => {
              e.stopPropagation()
              setIsMinimized(!isMinimized)
            }}
            title={isMinimized ? 'Expand chat' : 'Minimize chat'}
          >
            {isMinimized ? '▲' : '▼'}
          </button>
          <button 
            className="close-btn"
            onClick={(e) => {
              e.stopPropagation()
              onClose()
            }}
            title="Close chat"
          >
            ×
          </button>
        </div>
      </div>
      
      {!isMinimized && (
        <div className="cedar-copilot-container">
          {cedarError ? (
            <div className="cedar-error">
              <p>❌ Cedar-OS Error: {cedarError}</p>
              <p>Check console for details</p>
            </div>
          ) : isCedarLoaded ? (
            <CedarCopilot
              llmProvider={{
                provider: "openai",
                apiKey: import.meta.env.VITE_OPENAI_API_KEY,
                model: "gpt-3.5-turbo"
              }}
            />
          ) : (
            <div className="cedar-loading">
              <div className="loading-spinner"></div>
              <p>Loading Cedar-OS...</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default CedarGuide