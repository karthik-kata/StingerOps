/** @type {import('cedar-os').CedarConfig} */
export default {
  // AI Provider Configuration
  ai: {
    provider: 'openai',
    apiKey: process.env.VITE_OPENAI_API_KEY || 'demo-key',
    model: 'gpt-4',
  },
  
  // Project Configuration
  project: {
    id: 'bus-system',
    name: 'Bus System AI Guide',
    description: 'AI-powered guidance for the CSV Map Processor bus system',
  },
  
  // Chat Configuration
  chat: {
    theme: 'light',
    placeholder: 'Ask me anything about the bus system...',
    welcomeMessage: 'Hello! I\'m your Cedar AI guide for the Bus System. I can help you with CSV uploads, map navigation, data visualization, and more. What would you like to know?',
  },
  
  // State Access (for AI to interact with app state)
  state: {
    // Allow AI to read/write to these state keys
    allowedKeys: ['csvData', 'classesData', 'stopsData', 'busCount'],
    // Define actions AI can perform
    actions: [
      {
        name: 'upload_csv',
        description: 'Upload a CSV file to the system',
        parameters: {
          type: 'object',
          properties: {
            file: { type: 'string', description: 'CSV file content' },
            dataType: { type: 'string', enum: ['classes', 'stops', 'general'] }
          }
        }
      },
      {
        name: 'set_bus_count',
        description: 'Set the number of buses in the system',
        parameters: {
          type: 'object',
          properties: {
            count: { type: 'number', minimum: 1, maximum: 20 }
          }
        }
      }
    ]
  },
  
  // UI Configuration
  ui: {
    position: 'bottom-right',
    size: 'medium',
    showHeader: true,
    showMinimize: true,
    showClose: true,
  }
}
