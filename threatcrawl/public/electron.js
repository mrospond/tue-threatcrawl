const path = require("path");
const { app, BrowserWindow, ipcMain, nativeImage, Tray, Menu } = require("electron");
const isDev = require("electron-is-dev");
const WebSocket = require('ws');
const { ObjectId } = require('mongodb');
const connection = require('./connection');
const fs = require('fs');
const util = require('util');
const del = require('del');
const { PythonShell } = require('python-shell');
const { spawn } = require('child_process');

// Get the path to the directory for the webpages during training
const WEBPAGE_DIRECTORY_PATH = path.resolve(process.env['HOME'], './Documents/temporary/') + '/'; //path.resolve(__dirname, './temporary/') + '/';
global.WEBPAGE_DIRECTORY_PATH = WEBPAGE_DIRECTORY_PATH;

// Handle creating/removing shortcuts on Windows when installing/uninstalling
if (require("electron-squirrel-startup")) {
    app.quit();
}

// Some magic
app.commandLine.appendSwitch('disable-site-isolation-trials')

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on("window-all-closed", () => {
    if (process.platform === "darwin") {
        app.dock.hide(); // for macOS
    }
});

app.on("activate", () => {
    // On macOS it's common to re-create a window in the app when the
    // dock icon is clicked and there are no other windows open.
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow("start");
    }
});

// Parallelize all the initialization to increase startup performance
Promise.all([
    // Connect to the database
    connection.connect(),

    // This method will be called when Electron has finished
    // initialization and is ready to create browser windows.
    // Some APIs can only be used after this event occurs.
    app.whenReady()
])
    .then(_ => main())
    .catch(error => {
        console.error('Error during initialization of the electron app: ', error);
        console.error('The app will shut down because the error is unrecoverable.')
        app.quit();
    });

// This is the entry point of the app, once everything is initialized
function main() {

    // Retrieve configurations
    retrieveConfigurations()
    .then(result => {
        // Save the configurations to a global variable
        global.configurations = result;
    })
    .catch(error => {
        console.error('Error while retrieving stored configurations: ', error);
    })

    // On startup create a start screen
    createWindow('start');

    // Initiate a websocket for communication with the trainer
    const wss = new WebSocket.Server({ port: 8080 });
    wss.on('connection', connectionHandler);
}

// Get saved configurations from database
async function retrieveConfigurations() {
    // Get data
    const configurations = await connection.db.collection('configurations').find().toArray();

    // Return these values
    return configurations;
}

// Delete saved configuration from database
async function deleteConfiguration(configId) {
    // Delete configuration
    const result = await connection.db.collection('configurations').deleteOne({_id: ObjectId(configId)});

    // Output feedback
    if (result.deletedCount === 1) {
        console.log("Successfully deleted entry.");
    } else {
        console.log("No entry deleted, no match.");
    }
}

// Save the webpage from the database to a file for the viewer
async function writeWebpageToFile(webpage_id) {
    const mkdir = util.promisify(fs.mkdir);
    const writeFile = util.promisify(fs.writeFile);
    const webpage = await connection.db.collection('full webpage').findOne({ _id: ObjectId(webpage_id) });
    const ASSETS_DIRECTORY = `${WEBPAGE_DIRECTORY_PATH}${webpage['file_name']}_files/`;

    // Clear the directory as there might be data from a previous session
    await del(WEBPAGE_DIRECTORY_PATH, { force: true });
    await mkdir(ASSETS_DIRECTORY, { recursive: true });
    await writeFile(WEBPAGE_DIRECTORY_PATH + 'index.html', webpage['file_contents']);

    // Promises for writing the webpage to the correct directory
    const writePromises = webpage['folder_names']
        .map((name, index) => ({
            'name': name,
            'object_id': webpage['folder_contents'][index]
        }))
        .map(async file => {
            const content = await connection.retrieveFile(file['object_id']);

            return writeFile(ASSETS_DIRECTORY + file['name'], content, 'binary');
        });

    // Await the defined promises to ensure it is all written to disk
    await Promise.all(writePromises)
        .catch(error => {
            console.warn('Not all assets are written to to disk, the webpage might be incomplete. This warning is a result of the following error: ', error);
        });
}

// Get structure identifiers from database for the given platform
async function retrieveIdentifiers(platform_url) {
    // Get data
    const documents = await connection.db.collection('resource identifier').find({ platform_url }).toArray();
    const grouped_identifiers = {};

    // Loop over structures defined
    for (const document of documents) {
        // Get the page type of current structure
        const type = document.page_type.enum_value; 

        // Skip if a structure for this pagetype has already been found
        if (grouped_identifiers[type] !== undefined) {
            console.warn('Encountered multiple structures for the same pagetype. The first structure will be used, the others will be ignored');
            continue;
        }

        const structure = { };
        const date_formats = { };

        // Loop over structural elements of the page structure
        for (const [label, {date_format, identifier_type, identifier}] of Object.entries(document.structural_elements)) {
            // Save identifier
            structure[label] = {
                [identifier_type]: identifier
            };
            // Save date format
            date_formats[label] = date_format;
        }

        // Store structure and date_format in identifiers
        grouped_identifiers[type] = {structure, date_formats};
    }

    return grouped_identifiers;
}

// Handler for incoming messages from the trainer
function handleMessage(websocket, message) {
    // On open message, open a training screen and retrieve identifiers for the needed web page
    if (message.action === 'open training screen') {
        const webpage_id = message.data;
        const platform_url = message.platform_url

        Promise.all([
            retrieveIdentifiers(platform_url),
            writeWebpageToFile(webpage_id)
        ])
            .then(result => {
                // Save needed info to global variables
                global.identifiers = result[0];
                global.webpage_id = webpage_id;
                global.platform_url = platform_url;
                global.trained_structure = null;
                global.pageType = "";

                // Create training screen
                createWindow('training');
            })
            .catch(error =>
                console.error('Could not write webpage to disk, training cancelled.\nCause: ', error)
            );
    }

    // On double check, save the received structure to a global and open double check screen
    if (message.action === 'doublecheck') {
        const trained_structure = message.data;

        global.trained_structure = trained_structure;
        createWindow('doublecheck');
    }

    // Terminate when told
    if (message.action === 'terminate') {
        app.quit()
    }

}

// Instantiate websocket with handler on connection
function connectionHandler(websocket) {
    // Add message handler
    websocket.on('message', serialized_message => {
        try {
            const message = JSON.parse(serialized_message);

            handleMessage(websocket, message);
        } catch (e) {
            console.warn('Malformed message ignored: ', serialized_message);
        }
    });

    // Remove previous listeners 
    ipcMain.removeAllListeners('structure');
    ipcMain.removeAllListeners('confirmation');

    // When the structure data is received, forward it to the trainer
    ipcMain.on('structure', (event, data) => {
        global.pageType = data.page_type;
        websocket.send(JSON.stringify(data));
    });

    // When the confirmation is received, either send this to the trainer or restart the training window to adjust
    ipcMain.on('confirmation', (event, correct) => {
        if (correct) {
            websocket.send('structure is correct');
        } else {
            createWindow("training");
        }
    });
}

// General function to create a GUI window
function createWindow(page_path) {
    if (!tray) { // if tray hasn't been created already.
        createTray()
    }

    // Create the browser window.
    const win = new BrowserWindow({
        icon: path.join(__dirname, '/THREATcrawl-logo.png'),
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
            enableRemoteModule: true,
            webSecurity: false
        }
    });

    win.maximize();

    // and load the index.html of the app.
    // win.loadFile("index.html");
    win.loadURL(
        isDev
            ? "http://localhost:3000/" + page_path
            : `file://${path.join(__dirname, "../build/index.html#" + page_path)}`
    );

    // Open the DevTools.
    if (isDev) {
        // win.webContents.openDevTools({ mode: "detach" });
        win.webContents.openDevTools();
    }
}

// Store selected config in a global
ipcMain.on('selectConfig', (event, configuration) => {
    global.selectedConfiguration = configuration;
});

// Reset selected config saved in global
ipcMain.on('resetConfig', (event) => {
    global.selectedConfiguration = null;
});

// Delete configuration from global and database when delete signal arrives
ipcMain.on('deleteConfig', (event, data) => {
    // Remove configuration from the global list
    global.configurations = global.configurations.filter(config => { return config !== data.configuration })

    // Delete configuration from the database
    deleteConfiguration(data.id).then()
        .catch(error => {console.error('Something went wrong with deleting: ', error)})
});

// When the reset signal is received, reset the structure and restart the training screen
ipcMain.on('reset', (event, data) => {
    global.identifiers = {...global.identifiers, [data]: {}}
    global.pageType = data;
    global.trained_structure = null;
});

// When the start configuration is received, start the crawler
ipcMain.on('start-crawler', (event, message) => {
    const command = `gnome-terminal -- python3 main.py "${message.username}" "${message.password}" ${message.configuration_id}`;
    const appPath = app.getAppPath();
    const path = isDev 
        ? appPath + '/src/python'
        : appPath.slice(0, -8) + '/python';

    spawn(command, {cwd: path, shell: true});
});

// When the configuration is to be saved, save it to the database and reply with the id
ipcMain.on('save-configuration', async (event, configuration) => {
    const result = await connection.db.collection('configurations').insertOne(configuration);

    if (result.result.n < 1) {
        throw new Error('Could not save configuration to the database: ' + JSON.stringify(result));
    }

    // Get id from the result
    const id = ObjectId(result.ops[0]._id).toString();

    event.reply('save-configuration', id);
});


// Create a tray menu item to ensure the app stays running
let tray = null;
function createTray() {
    const icon = path.join(__dirname, '/THREATcrawl-logo.png');
    const trayIcon = nativeImage.createFromPath(icon)
    tray = new Tray(trayIcon.resize({ width: 16 }));
    const contextMenu = Menu.buildFromTemplate([
        {
            label: 'Quit',
            click: () => {
                app.quit();
            }
        }
    ])

    tray.setContextMenu(contextMenu)
}