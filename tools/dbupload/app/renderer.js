require('@fortawesome/fontawesome-free/js/all') // import fontawesome icons

const {
    ipcRenderer
} = require('electron')
const {
    MongoClient
} = require('mongodb')

let client

function notify(options) {
    new Notification(options.title, options)
}

function initClient(credentials) {
    const cluster = 'dev-galactic.upyio.mongodb.net'
    const params =
        'retryWrites=true&w=1&readPreference=primary&wtimeoutMS=600000&ssl=true'
    const uri = `mongodb+srv://${credentials.username}:${credentials.password}@${cluster}/techdev?${params}`

    client = new MongoClient(uri)
}

async function update(data) {
    try {
        await client.connect()
        const database = client.db('techdev')
        const collection = database.collection('imaging')
        const docCount = await collection.countDocuments({})

        // update data id based on document number
        data['id'] = docCount + 1

        await collection.insertOne(data, (err, res) => {
            if (err) {
                // unsure how to mitigate
                if (err.name !== 'MongoServerSelectionError') throw err
            }

            // ensure that the client will close upon finish/error
            client.close()
        })
    } finally {
        console.log('New document inserted')
        notify({
            title: 'Database update',
            body: 'New document inserted to the database',
            // icon: path.join(__dirname, '..', 'assets', 'icons', 'cellino_icon_greyscale.png')
        })
    }
}

// check when content is loaded
function docReady(fn) {
    // check if DOM is already available
    if (
        document.readyState === 'complete' ||
        document.readyState === 'interactive'
    ) {
        // call on next available tick
        setTimeout(fn, 1)
    } else {
        document.addEventListener('DOMContentLoaded', fn)
    }
}

docReady(() => {
    let defaultData

    var params = {
        general: document.getElementById('general'),
        acquisition: document.getElementById('acquisition'),
        illumination: document.getElementById('illumination'),
    }

    function setFieldValues(data) {
        for (const key in data) {
            for (const param in data[key]) {
                try {
                    if (data[key][param])
                        document.getElementById(param).value = data[key][param]
                } catch (err) {
                    console.log(err)
                }
            }
        }
    }

    function getData() {
        let userData = {
            general: {},
            acquisition: {},
            illumination: {},
        }

        for (const key in params) {
            var inputs = params[key].getElementsByTagName('input')
            for (let i in inputs) {
                if (inputs[i].id) {
                    if (inputs[i].value != '') {
                        if (isNaN(inputs[i].value))
                            userData[key][inputs[i].id] = inputs[i].value
                        else
                            userData[key][inputs[i].id] = Number(inputs[i].value)
                    }
                    else userData[key][inputs[i].id] = null
                }
            }
        }
        return userData
    }

    ipcRenderer.on('credentials:get', (e, credentials) => {
        initClient(credentials)
    })

    ipcRenderer.on('params:get', (e, defaults) => {
        defaultData = defaults
        setFieldValues(defaultData)
    })

    document.getElementById('clear').onclick = () => {
        for (const key in params) {
            params[key].reset()
        }
    }

    document.getElementById('reset').onclick = () => setFieldValues(defaultData)

    document.getElementById('save').onclick = () => {
        var data = getData()
        ipcRenderer.send('params:set', data)
        console.log('Settings saved')
        notify({
            title: 'Settings update',
            body: 'New settings saved to local storage',
            // icon: path.join(__dirname, '..', 'assets', 'icons', 'cellino_icon_greyscale.png')
        })
    }

    document.getElementById('submit').onclick = () => {
        var data = getData()
        // rearrange data object
        data = {
            id: null,
            mode: data['general']['mode'],
            target: data['general']['target'],
            date: Date(),
            url: data['general']['url'],
            acquisition: data['acquisition'],
            illumination: data['illumination'],
        }
        update(data).catch(console.dir)
    }
})