const electron = require('electron')
const path = require('path')
const fs = require('fs')

class Store {
    constructor(options) {
        const userDataPath = electron.app.getPath('home')

        this.path = path.join(userDataPath, options.configName + '.json')
        this.data = parseDataFile(this.path, options.defaults)
    }

    get() {
        return this.data
    }

    set(data) {
        this.data = data
        fs.writeFileSync(this.path, JSON.stringify(this.data))
    }
}

function parseDataFile(filePath, defaults) {
    try {
        return JSON.parse(fs.readFileSync(filePath))
    } catch (err) {
        return defaults
    }
}

module.exports = Store