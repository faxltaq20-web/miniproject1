const { app, BrowserWindow, ipcMain, shell, dialog, Menu } = require('electron');
const path = require('path');
const { spawn, exec } = require('child_process');
const net = require('net');
const fs = require('fs');

// ── Kill native menu immediately at module load ─────────────────────────────
// This runs before any window is created — most reliable timing
Menu.setApplicationMenu(null);
app.applicationMenu = null;

// ── Hook: remove menu from EVERY window as soon as it's created ─────────────
app.on('browser-window-created', (_, win) => {
    win.removeMenu();                   // native SetMenu(hwnd, NULL)
    win.setMenuBarVisibility(false);    // belt-and-suspenders
});

// ── Resolve Resource Root ───────────────────────────────────────────────────
// Packaged: extraResources land in process.resourcesPath (…/resources/).
// Dev:      files sit one level above electron/.
// Fallback: if the packaged bundle can't find MAIN_PROJECT under resources
//           (older sideloaded exe), fall back to sibling of the exe folder.
function resolveResourceRoot() {
    if (app.isPackaged) {
        const primary = process.resourcesPath;
        if (primary && fs.existsSync(path.join(primary, 'MAIN_PROJECT'))) {
            return primary;
        }
        // Legacy layout (portable exe with tree beside it)
        const portableDir = process.env.PORTABLE_EXECUTABLE_DIR;
        if (portableDir) return path.resolve(portableDir, '..');
        return path.resolve(path.dirname(app.getPath('exe')), '..', '..');
    }
    return path.join(__dirname, '..');
}

const RESOURCE_ROOT    = resolveResourceRoot();
const MAIN_PROJECT_DIR = path.join(RESOURCE_ROOT, 'MAIN_PROJECT');

// Python executable — platform-aware paths for the bundled venv.
function resolveVenvPython() {
    if (process.platform === 'win32') {
        return path.join(RESOURCE_ROOT, 'venv', 'Scripts', 'python.exe');
    }
    return path.join(RESOURCE_ROOT, 'venv', 'bin', 'python');
}
const VENV_PYTHON = resolveVenvPython();
const PYTHON_EXE  = fs.existsSync(VENV_PYTHON)
    ? VENV_PYTHON
    : (process.platform === 'win32' ? 'python' : 'python3');

const PREFERRED_PORT = 8000;
let   BACKEND_URL    = `http://127.0.0.1:${PREFERRED_PORT}`;

// ── State ──────────────────────────────────────────────────────────────────
let mainWindow    = null;
let splashWindow  = null;
let backendProcess = null;

// ── Splash Window ──────────────────────────────────────────────────────────
function createSplashWindow() {
    splashWindow = new BrowserWindow({
        width: 480, height: 320,
        frame: false, resizable: false,
        center: true, alwaysOnTop: true, transparent: true,
        webPreferences: { nodeIntegration: false }
    });
    splashWindow.removeMenu();
    splashWindow.loadFile(path.join(__dirname, 'splash.html'));
}

// ── Main App Window ─────────────────────────────────────────────────────────
function createMainWindow() {
    mainWindow = new BrowserWindow({
        width: 1400, height: 900,
        minWidth: 900, minHeight: 600,
        show: false, center: true,
        frame: false,               // remove native OS frame & title bar
        titleBarStyle: 'hidden',    // suppress residual title bar on Windows
        autoHideMenuBar: true,      // hide menu bar even if frame appears
        thickFrame: false,          // remove thick border on Windows
        title: 'ResearchSense',
        icon: path.join(__dirname, 'assets', 'icon.ico'),
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            nodeIntegration: false,
            contextIsolation: true,
        }
    });

    // Belt-and-suspenders: remove menu directly on this window too
    mainWindow.removeMenu();
    mainWindow.setMenuBarVisibility(false);

    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
        shell.openExternal(url); return { action: 'deny' };
    });
    mainWindow.on('closed', () => (mainWindow = null));
}

// ── Port Helpers ─────────────────────────────────────────────────────────────
function findFreePort(startPort, maxTries = 10) {
    return new Promise((resolve, reject) => {
        function tryPort(port) {
            if (port >= startPort + maxTries) { reject(new Error('No free port found')); return; }
            const server = net.createServer();
            server.listen(port, '127.0.0.1', () => server.close(() => resolve(port)));
            server.on('error', () => tryPort(port + 1));
        }
        tryPort(startPort);
    });
}

function killPortIfBusy(port) {
    // netstat/taskkill are Windows-only; findFreePort already handed us a
    // port that was free a moment ago, so on other platforms just skip.
    if (process.platform !== 'win32') return Promise.resolve();
    return new Promise((resolve) => {
        exec(`netstat -ano | findstr ":${port}" | findstr "LISTENING"`, (err, stdout) => {
            if (!stdout) { resolve(); return; }
            let pending = 0;
            stdout.trim().split('\n').forEach(line => {
                const pid = line.trim().split(/\s+/).pop();
                if (pid && /^\d+$/.test(pid) && pid !== '0') {
                    pending++;
                    exec(`taskkill /PID ${pid} /F`, () => { if (--pending === 0) setTimeout(resolve, 600); });
                }
            });
            if (pending === 0) resolve();
        });
    });
}

// ── Backend Startup ──────────────────────────────────────────────────────────
function startBackend(port) {
    return new Promise((resolve, reject) => {
        BACKEND_URL = `http://127.0.0.1:${port}`;
        console.log(`[Electron] RESOURCE_ROOT  : ${RESOURCE_ROOT}`);
        console.log(`[Electron] MAIN_PROJECT   : ${MAIN_PROJECT_DIR}`);
        console.log(`[Electron] Python         : ${PYTHON_EXE}`);
        console.log(`[Electron] Port           : ${port}`);

        if (!fs.existsSync(PYTHON_EXE)) {
            reject(new Error(`Python not found at:\n${PYTHON_EXE}`)); return;
        }
        if (!fs.existsSync(MAIN_PROJECT_DIR)) {
            reject(new Error(`MAIN_PROJECT not found at:\n${MAIN_PROJECT_DIR}`)); return;
        }

        backendProcess = spawn(
            PYTHON_EXE,
            ['-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', String(port)],
            { cwd: MAIN_PROJECT_DIR, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] }
        );

        const timeout = setTimeout(() => {
            reject(new Error(`Backend on port ${port} did not signal readiness in 30s`));
        }, 30000);

        function onData(chunk) {
            const text = chunk.toString();
            process.stdout.write(`[Python] ${text}`);
            if (text.includes('Application startup complete') || text.includes('Uvicorn running on')) {
                clearTimeout(timeout);
                resolve();
            }
        }
        backendProcess.stdout.on('data', onData);
        backendProcess.stderr.on('data', onData);
        backendProcess.on('exit', (code) => {
            clearTimeout(timeout);
            reject(new Error(`Backend process exited early (code=${code})`));
        });
    });
}

function killBackend() {
    if (backendProcess) {
        try { backendProcess.kill('SIGTERM'); } catch (_) {}
        setTimeout(() => { try { backendProcess.kill('SIGKILL'); } catch (_) {} }, 2000);
        backendProcess = null;
    }
}

// ── IPC ───────────────────────────────────────────────────────────────────────
ipcMain.on('window-minimize', () => mainWindow?.minimize());
ipcMain.on('window-maximize', () => mainWindow?.isMaximized() ? mainWindow.unmaximize() : mainWindow?.maximize());
ipcMain.on('window-close',    () => mainWindow?.close());

// ── App Lifecycle ─────────────────────────────────────────────────────────────
app.whenReady().then(async () => {
    // Re-apply at ready time for good measure
    Menu.setApplicationMenu(null);

    createSplashWindow();
    createMainWindow();

    try {
        const port = await findFreePort(PREFERRED_PORT);
        await killPortIfBusy(port);
        await startBackend(port);
        console.log(`[Electron] Backend ready → ${BACKEND_URL}`);
        mainWindow.loadURL(BACKEND_URL);
        mainWindow.once('ready-to-show', () => {
            splashWindow?.close(); splashWindow = null;
            mainWindow.show();
        });
    } catch (err) {
        console.error('[Electron] Startup failed:', err.message);
        splashWindow?.close();
        dialog.showErrorBox('ResearchSense — Startup Failed', err.message);
        app.quit();
    }
});

app.on('window-all-closed', () => { killBackend(); app.quit(); });
app.on('before-quit', killBackend);
