// main.js

// modules to control application life and create native browser window
const { app, BrowserWindow, ipcMain } = require('electron')
const path = require('path')
const Store = require('./Store')

// set environment
// process.env.NODE_ENV = 'development'
process.env.NODE_ENV = 'production'

const isDev = process.env.NODE_ENV !== 'production' ? true : false
const isMac = process.platform === 'darwin' ? true : false

let mainWindow

// init store
const store = new Store({
    configName: 'user_params',
    defaults: {
        general: {
            id: null,
            mode: 'tie',
            target: 'cells',
            url: '',
            date: null
        },
        acquisition: {
            type: 'scan',
            vertical_range_um: 10,
            vertical_increment_um: 2,
            reconstructions: 5,
            overlap_fovs: 40,
            scan_distance_mm: 22,
            scan_velocity_mm_s: 0.1,
            pixel_size_um: 0.035,
            resolution: '12bit'
        },
        illumination: {
            led_intensity: 100,
            exposure_time_ms: 0.05,
            color: '#FF0000',
            pattern: 'disc',
            pattern_radius_pix: 7,
            pattern_radial_thickness_pix: 3,
            pattern_rotation_deg: 90,
            led_sample_distance_mm: 75,
            na_outer: null,
            na_inner: null
        }
    }
})

const createWindow = () => {
    // create the browser window
    mainWindow = new BrowserWindow({
        width: isDev ? 1300 : 1000,
        height: 600,
        // use absolute path to prevent issues with packaging
        icon: `${__dirname}/assets/icons/cellino_icon_greyscale.png`,
        resizable: isDev,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            nodeIntegration: true,
            contextIsolation: false,
            enableRemoteModule: true,
        }
    })

    // load the index html file for the app
    mainWindow.loadFile(`${__dirname}/app/index.html`)

    // open DevTools
    if (isDev) mainWindow.webContents.openDevTools()
}

app.whenReady().then(() => {
    createWindow()

    mainWindow.webContents.on('dom-ready', () => {
        mainWindow.webContents.send('params:get', store.get())
        mainWindow.webContents.send('credentials:get', {
            username: encodeURIComponent(process.env.CELLINO_MONGO_USERNAME),
            password: encodeURIComponent(process.env.CELLINO_MONGO_PASSWORD)
        })
    })

    ipcMain.on('params:set', (e, data) => {
        store.set(data)
        // update defaults
        mainWindow.webContents.send('params:get', store.get())
    })

    // const mainMenu = Menu.buildFromTemplate(menu)
    // Menu.setApplicationMenu(mainMenu)

    mainWindow.on('close', () => mainWindow = null)

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) createWindow()
    })
})

// incorporate native system behaviors
app.on('window-all-closed', () => {
    if (!isMac) app.quit()
})
