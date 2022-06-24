/*
 * Functions that are reused across system.
 * 
 * Written by Lukas Vasadi in March 2021
*/

const ipcRenderer = require('electron').ipcRenderer;

// Function to check whether content is loaded
function docReady(fn) {
    // Check if DOM is already available
    if (document.readyState === "complete" || document.readyState === "interactive") {
        // Call on next available tick
        setTimeout(fn, 1);
    } else {
        document.addEventListener("DOMContentLoaded", fn);
    }
}
