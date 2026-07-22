import React, { useState, useRef, useEffect } from 'react'
import './App.css'

const { ipcRenderer } = window.require('electron')

export default function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [provider, setProvider] = useState('anthropic')
  const [providers, setProviders] = useState([])
  const [apiKey, setApiKey] = useState('')
  const [loading, setLoading] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const messagesEnd = useRef(null)

  useEffect(() => {
    // Load providers on startup
    ipcRenderer.invoke('get-providers').then(data => {
      setProviders(data.providers || ['anthropic', 'openai'])
    })
  }, [])

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSendMessage = async () => {
    if (!input.trim()) return

    setMessages(prev => [...prev, { role: 'user', content: input }])
    setLoading(true)

    try {
      const response = await ipcRenderer.invoke('chat', input, 'default')
      if (response.success) {
        setMessages(prev => [...prev, { role: 'assistant', content: response.message }])
      } else {
        setMessages(prev => [...prev, { role: 'error', content: `Error: ${response.error}` }])
      }
    } catch (error) {
      setMessages(prev => [...prev, { role: 'error', content: `Error: ${error.message}` }])
    } finally {
      setInput('')
      setLoading(false)
    }
  }

  const handlePALEnhance = async () => {
    if (!input.trim()) return
    
    try {
      const response = await ipcRenderer.invoke('pal-enhance', input)
      setInput(response.enhanced || input)
    } catch (error) {
      console.error('PAL enhance failed:', error)
    }
  }

  const handleSetProvider = async () => {
    if (!apiKey.trim()) {
      alert('Please enter an API key')
      return
    }
    
    const response = await ipcRenderer.invoke('set-provider', provider, apiKey)
    if (response.status === 'ok') {
      setShowSettings(false)
      setApiKey('')
    }
  }

  return (
    <div className="app-container">
      {/* Header */}
      <div className="header">
        <h1>ROSTR</h1>
        <div className="header-controls">
          <button onClick={() => setShowSettings(!showSettings)} className="settings-btn">
            ⚙️ Settings
          </button>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="settings-panel">
          <div className="settings-content">
            <h2>LLM Configuration</h2>
            <div className="setting-group">
              <label>Provider:</label>
              <select value={provider} onChange={e => setProvider(e.target.value)}>
                {providers.map(p => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
            <div className="setting-group">
              <label>API Key:</label>
              <input
                type="password"
                value={apiKey}
                onChange={e => setApiKey(e.target.value)}
                placeholder="Enter your API key"
              />
            </div>
            <button onClick={handleSetProvider} className="btn-primary">Save</button>
          </div>
        </div>
      )}

      {/* Chat Area */}
      <div className="chat-container">
        <div className="messages">
          {messages.map((msg, i) => (
            <div key={i} className={`message message-${msg.role}`}>
              <div className="message-role">{msg.role}</div>
              <div className="message-content">{msg.content}</div>
            </div>
          ))}
          {loading && <div className="message message-loading">ROSTR thinking...</div>}
          <div ref={messagesEnd} />
        </div>

        {/* Input Area */}
        <div className="input-area">
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyPress={e => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
            placeholder="Type your message... (Shift+Enter for newline)"
            disabled={loading}
          />
          <div className="input-controls">
            <button onClick={handlePALEnhance} className="btn-secondary" disabled={loading}>
              ✨ Enhance with PAL
            </button>
            <button onClick={handleSendMessage} className="btn-primary" disabled={loading}>
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
