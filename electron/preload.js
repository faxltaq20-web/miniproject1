const { contextBridge, ipcRenderer } = require('electron');

// Expose a safe, minimal API to the renderer (frontend)
// No nodeIntegration — only these whitelisted channels are accessible
contextBridge.exposeInMainWorld('electronAPI', {
    minimize: () => ipcRenderer.send('window-minimize'),
    maximize: () => ipcRenderer.send('window-maximize'),
    close:    () => ipcRenderer.send('window-close'),
    isElectron: true,
});
