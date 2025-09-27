"use client"

import { useState, useEffect } from 'react'
import { CedarCopilot, setCedarStore, useChatInput, useMessages, useThreadMessages, useCedarStore } from 'cedar-os'

// Cedar Chat Interface Component using Cedar-OS hooks
const CedarChatInterface = ({ busCount, csvData, classesData, stopsData }) => {
  console.log('🌲 CedarChatInterface - Starting to render...')
  
  // Use Cedar-OS hooks
  const { inputValue, setInputValue, handleSubmit, isSubmitting } = useChatInput()
  const { messages, addMessage } = useMessages()
  const { threadMessages } = useThreadMessages()
  const cedarStore = useCedarStore()
  
  console.log('🌲 Cedar-OS hooks initialized:', { 
    inputValue, 
    messagesCount: messages?.length || 0, 
    threadMessagesCount: threadMessages?.length || 0,
    cedarStore: !!cedarStore,
    setInputValue: typeof setInputValue,
    handleSubmit: typeof handleSubmit
  })

  // Fallback state management if Cedar-OS hooks don't work
  const [localInputValue, setLocalInputValue] = useState('')
  const [localMessages, setLocalMessages] = useState([])
  const [isLocalSubmitting, setIsLocalSubmitting] = useState(false)

  // Use local state if Cedar-OS hooks aren't working
  const effectiveInputValue = inputValue !== undefined ? inputValue : localInputValue
  const effectiveSetInputValue = setInputValue || setLocalInputValue
  const effectiveMessages = messages || localMessages
  const effectiveIsSubmitting = isSubmitting !== undefined ? isSubmitting : isLocalSubmitting

  console.log('🌲 Effective values:', { 
    effectiveInputValue, 
    effectiveMessagesCount: effectiveMessages?.length || 0,
    effectiveIsSubmitting
  })
  
  return (
    <div style={{ 
      height: '100%', 
      width: '100%', 
      background: 'white',
      display: 'flex',
      flexDirection: 'column'
    }}>
      <div style={{ 
        padding: '10px', 
        background: '#4CAF50', 
        color: 'white', 
        textAlign: 'center',
        fontSize: '14px',
        fontWeight: 'bold'
      }}>
        🌲 Cedar-OS Chat Interface (Hooks)
      </div>
      
      {/* Messages Area */}
      <div style={{ 
        flex: 1, 
        padding: '20px', 
        overflowY: 'auto',
        border: '2px solid #4CAF50',
        borderRadius: '8px',
        margin: '20px',
        background: '#ffffff',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        {effectiveMessages && effectiveMessages.length > 0 ? (
          effectiveMessages.map((message, index) => (
            <div key={index} style={{ 
              marginBottom: '15px', 
              padding: '15px', 
              background: message.role === 'user' ? '#e3f2fd' : '#f8f9fa',
              borderRadius: '12px',
              border: message.role === 'user' ? '1px solid #bbdefb' : '1px solid #e9ecef',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
            }}>
              <div style={{ 
                fontWeight: 'bold', 
                color: message.role === 'user' ? '#1976d2' : '#4CAF50',
                marginBottom: '8px',
                fontSize: '14px'
              }}>
                {message.role === 'user' ? '👤 You' : '🌲 Cedar-OS AI'}
              </div>
              <div style={{ 
                color: '#333333',
                lineHeight: '1.5',
                fontSize: '14px'
              }}>
                {message.content}
              </div>
            </div>
          ))
        ) : (
          <div style={{ 
            textAlign: 'center', 
            color: '#666666', 
            marginTop: '50px',
            fontSize: '16px',
            fontWeight: '500',
            padding: '20px'
          }}>
            <div style={{ marginBottom: '20px' }}>
              🌲 <strong>Cedar-OS AI</strong> is ready to help!
            </div>
            <div style={{ fontSize: '14px', color: '#888', lineHeight: '1.6' }}>
              I can help you with:
              <br />• Finding bus stops and routes
              <br />• Understanding your uploaded data
              <br />• Navigating the Georgia Tech campus
              <br />• Using the CSV upload features
              <br />• Planning your bus journey
            </div>
            <div style={{ marginTop: '15px', fontSize: '12px', color: '#aaa' }}>
              Current data: {csvData ? csvData.length + ' general rows' : 'No general data'} • 
              {classesData ? classesData.length + ' classes' : ' No classes'} • 
              {stopsData ? stopsData.length + ' stops' : ' No stops'} • 
              {busCount || 5} buses configured
            </div>
          </div>
        )}
      </div>
      
      {/* Input Area */}
      <div style={{ 
        padding: '20px', 
        borderTop: '2px solid #e0e0e0',
        background: '#ffffff',
        boxShadow: '0 -2px 8px rgba(0,0,0,0.1)'
      }}>
        <form onSubmit={(e) => {
          e.preventDefault()
          console.log('🌲 Form submitted with value:', effectiveInputValue)
          if (effectiveInputValue && effectiveInputValue.trim()) {
            // Add user message
            const newMessage = { role: 'user', content: effectiveInputValue }
            if (addMessage) {
              addMessage(newMessage)
            } else {
              setLocalMessages(prev => [...prev, newMessage])
            }
            
            // Clear input
            if (effectiveSetInputValue) {
              effectiveSetInputValue('')
            }
            
            // Call real OpenAI API with bus system context
            setIsLocalSubmitting(true)
            
            // Create system context about the bus system with actual data
            const systemContext = `You are Cedar-OS AI, an intelligent assistant for the Georgia Tech Bus System. You help users navigate bus routes, find stops, and understand the transit system.

BUS SYSTEM CONTEXT:
- This is a Georgia Tech campus bus system with multiple routes
- Users can upload CSV files with bus stops, classes, and general location data
- The system displays bus stops on a map with route information
- Users can configure the number of buses (currently set to ${busCount || 5})
- The map shows Georgia Tech campus and surrounding areas

CURRENT DATA STATUS:
- General CSV Data: ${csvData ? csvData.length + ' rows uploaded' : 'No data uploaded'}
- Classes Data: ${classesData ? classesData.length + ' classes uploaded' : 'No classes uploaded'}
- Bus Stops Data: ${stopsData ? stopsData.length + ' stops uploaded' : 'No stops uploaded'}

CAPABILITIES:
- Help users find bus stops and routes
- Explain how to use the CSV upload features
- Assist with navigation around Georgia Tech campus
- Answer questions about the bus system interface
- Provide guidance on uploading and managing data
- Analyze uploaded data and provide insights
- Help with route planning and stop information

Be helpful, friendly, and specific to the Georgia Tech bus system context. If users ask about specific data, refer to the current data status above.`

            // Prepare messages for API call with system context
            const apiMessages = [
              { role: 'system', content: systemContext },
              ...effectiveMessages,
              { role: 'user', content: effectiveInputValue }
            ]
            
            console.log('🌲 Calling OpenAI API with bus system context:', apiMessages)
            
            fetch('https://api.openai.com/v1/chat/completions', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${import.meta.env.VITE_OPENAI_API_KEY}`
              },
              body: JSON.stringify({
                model: 'gpt-3.5-turbo',
                messages: apiMessages,
                max_tokens: 600,
                temperature: 0.7
              })
            })
            .then(response => {
              if (!response.ok) {
                throw new Error(`OpenAI API error: ${response.status} - ${response.statusText}`)
              }
              return response.json()
            })
            .then(data => {
              console.log('🌲 OpenAI API response:', data)
              const aiMessage = { 
                role: 'assistant', 
                content: data.choices[0].message.content
              }
              if (addMessage) {
                addMessage(aiMessage)
              } else {
                setLocalMessages(prev => [...prev, aiMessage])
              }
              setIsLocalSubmitting(false)
            })
            .catch(error => {
              console.error('🌲 OpenAI API error:', error)
              const errorMessage = { 
                role: 'assistant', 
                content: `❌ Cedar-OS AI Error: ${error.message}. Please check your API key and try again.` 
              }
              if (addMessage) {
                addMessage(errorMessage)
              } else {
                setLocalMessages(prev => [...prev, errorMessage])
              }
              setIsLocalSubmitting(false)
            })
          }
        }} style={{ display: 'flex', gap: '12px' }}>
          <input
            type="text"
            value={effectiveInputValue || ''}
            onChange={(e) => {
              console.log('🌲 Input changed:', e.target.value)
              if (effectiveSetInputValue) {
                effectiveSetInputValue(e.target.value)
              }
            }}
            placeholder="Type your message here..."
            style={{
              flex: 1,
              padding: '14px 16px',
              border: '2px solid #4CAF50',
              borderRadius: '12px',
              fontSize: '14px',
              color: '#333333',
              background: '#ffffff',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              outline: 'none',
              transition: 'border-color 0.2s ease'
            }}
            disabled={effectiveIsSubmitting}
            onFocus={(e) => e.target.style.borderColor = '#2e7d32'}
            onBlur={(e) => e.target.style.borderColor = '#4CAF50'}
          />
          <button
            type="submit"
            disabled={effectiveIsSubmitting || !effectiveInputValue}
            style={{
              padding: '14px 28px',
              background: effectiveIsSubmitting ? '#cccccc' : '#4CAF50',
              color: '#ffffff',
              border: 'none',
              borderRadius: '12px',
              cursor: effectiveIsSubmitting ? 'not-allowed' : 'pointer',
              fontSize: '14px',
              fontWeight: 'bold',
              boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
              transition: 'background-color 0.2s ease'
            }}
            onMouseEnter={(e) => {
              if (!effectiveIsSubmitting && effectiveInputValue) {
                e.target.style.background = '#45a049'
              }
            }}
            onMouseLeave={(e) => {
              if (!effectiveIsSubmitting) {
                e.target.style.background = '#4CAF50'
              }
            }}
          >
            {effectiveIsSubmitting ? 'Sending...' : 'Send'}
          </button>
        </form>
      </div>
      
      <div style={{ 
        margin: '10px 20px', 
        padding: '12px', 
        background: '#f8f9fa', 
        borderRadius: '8px',
        fontSize: '12px',
        color: '#495057',
        border: '1px solid #dee2e6',
        fontFamily: 'monospace'
      }}>
        <strong>Debug Info:</strong> Cedar-OS hooks active | API Key: {import.meta.env.VITE_OPENAI_API_KEY?.length || 0} chars | Messages: {effectiveMessages?.length || 0} | Input: "{effectiveInputValue}" | Using: {inputValue !== undefined ? 'Cedar-OS' : 'Local'} state | Bus System: {busCount || 5} buses, {csvData?.length || 0} general, {classesData?.length || 0} classes, {stopsData?.length || 0} stops
      </div>
    </div>
  )
}

const CedarGuide = ({ isOpen, onClose, busCount, csvData, classesData, stopsData }) => {
  const [isMinimized, setIsMinimized] = useState(false)
  const [isCedarLoaded, setIsCedarLoaded] = useState(false)
  const [cedarError, setCedarError] = useState(null)

  useEffect(() => {
    // Initialize Cedar-OS store
    try {
      console.log('🌲 Initializing Cedar-OS...')
      console.log('API Key available:', !!import.meta.env.VITE_OPENAI_API_KEY)
      console.log('API Key length:', import.meta.env.VITE_OPENAI_API_KEY?.length || 0)
      console.log('CedarCopilot type:', typeof CedarCopilot)
      console.log('setCedarStore type:', typeof setCedarStore)
      
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

  console.log('🌲 CedarGuide render - isOpen:', isOpen, 'isCedarLoaded:', isCedarLoaded, 'cedarError:', cedarError)

  if (!isOpen) {
    console.log('🌲 CedarGuide not open, returning null')
    return null
  }

  console.log('🌲 CedarGuide rendering chat interface')
  console.log('🌲 API Key available:', !!import.meta.env.VITE_OPENAI_API_KEY)
  console.log('🌲 API Key length:', import.meta.env.VITE_OPENAI_API_KEY?.length || 0)

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
                    <CedarChatInterface 
                      busCount={busCount}
                      csvData={csvData}
                      classesData={classesData}
                      stopsData={stopsData}
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