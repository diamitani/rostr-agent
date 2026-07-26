const { app, BrowserWindow, Menu, ipcMain } = require('electron')
const isDev = require('electron-is-dev')
const path = require('path')
const axios = require('axios')

const API_URL = 'http://localhost:8000'
let mainWindow

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    icon: path.join(__dirname, '../assets/icon.png'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true
    }
  })

  const startUrl = isDev
    ? 'http://localhost:3000'
    : `file://${path.join(__dirname, '../build/index.html')}`
  
  mainWindow.loadURL(startUrl)
  if (isDev) mainWindow.webDevTools.openDevTools()

  mainWindow.on('closed', () => { mainWindow = null })
}

app.on('ready', createWindow)
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})

// IPC handlers for API calls
ipcMain.handle('chat', async (event, message, workspaceId) => {
  try {
    const response = await axios.post(`${API_URL}/api/chat`, {
      message,
      workspace_id: workspaceId,
      provider: 'anthropic'
    })
    return response.data
  } catch (error) {
    return { success: false, error: error.message }
  }
})

ipcMain.handle('pal-enhance', async (event, prompt) => {
  try {
    const response = await axios.post(`${API_URL}/api/pal/enhance`, { prompt })
    return response.data
  } catch (error) {
    return { error: error.message }
  }
})

ipcMain.handle('get-providers', async (event) => {
  try {
    const response = await axios.get(`${API_URL}/api/config/providers`)
    return response.data
  } catch (error) {
    return { providers: ['anthropic', 'openai'] }
  }
})

ipcMain.handle('set-provider', async (event, provider, apiKey) => {
  try {
    const response = await axios.post(
      `${API_URL}/api/config/llm`,
      null,
      { params: { provider, api_key: apiKey } }
    )
    return response.data
  } catch (error) {
    return { status: 'error', error: error.message }
  }
})
