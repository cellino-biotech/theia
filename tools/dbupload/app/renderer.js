require("@fortawesome/fontawesome-free/js/all") // import fontawesome icons

const { ipcRenderer } = require('electron')
const { MongoClient } = require('mongodb')

let client

function initClient(credentials) {
    const cluster = 'dev-galactic.upyio.mongodb.net'
    const params = 'retryWrites=true&w=1&readPreference=primary&wtimeoutMS=600000&ssl=true'
    const uri = `mongodb+srv://${credentials.username}:${credentials.password}@${cluster}/techdev?${params}`

    client = new MongoClient(uri)
}

async function run() {
  try {
    await client.connect()
    const database = client.db("techdev")
    const collection = database.collection("imaging")
    const docCount = await collection.countDocuments({})
    // console.log(docCount)
  } finally {
    // ensure that the client will close upon finish/error
    await client.close()
  }
}

// function to check whether content is loaded
function docReady(fn) {
    // check if DOM is already available
    if (document.readyState === "complete" || document.readyState === "interactive") {
        // call on next available tick
        setTimeout(fn, 1)
    } else {
        document.addEventListener("DOMContentLoaded", fn)
    }
}

docReady(() => {
    ipcRenderer.on('credentials:get', (e, credentials) => {
        initClient(credentials)
        run().catch(console.dir)
    })

    let defaultData

    var params = {
        general: document.getElementById('general'),
        acquisition: document.getElementById('acquisition'),
        illumination: document.getElementById('illumination')
    }

    function setDefaults(data) {
        for (const key in data) {
            for (const param in data[key]) {
                try {
                    if (data[key][param]) document.getElementById(param).value = data[key][param]
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
            illumination: {}
        }

        for (const key in params) {
            var inputs = params[key].getElementsByTagName('input')
            for (let i in inputs) {
                userData[key][inputs[i].id] = inputs[i].value
            }
        }
        return userData
    }

    ipcRenderer.on('params:get', (e, defaults) => {
        defaultData = defaults
        setDefaults(defaultData)
    })

    document.getElementById('clear').onclick = () => {
        for (const key in params) {
            params[key].reset()
        }
    }

    document.getElementById('reset').onclick = () => setDefaults(defaultData)

    document.getElementById('save').onclick = () => {
        var data = getData()
        ipcRenderer.send('params:set', data)
        console.log('Settings saved')
    }

    document.getElementById('submit').onclick = () => {
        console.log('Submit')
    }
})