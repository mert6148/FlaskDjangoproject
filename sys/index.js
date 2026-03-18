const system = require('./system.json');

const name = system.name;
const version = system.version;
const AWSTemplateFormatVersion = system.AWSTemplateFormatVersion;
const output = {
    system: {
        name,
        system,
        version,
        AWSTemplateFormatVersion
    }
};

document.addEventListener("DOMContentLoaded", function() {
    const outputElement = document.getElementById("output");
    const nameElement = document.getElementById("name");
    const versionElement = document.getElementById("version");
    const AWSTemplateFormatVersionElement = document.getElementById("AWSTemplateFormatVersion");
});

document.addEventListener("DOMContentLoaded", function() {
    const outputElement = document.getElementById("output");
    if (outputElement) {
        outputElement.textContent = JSON.stringify(output);
    }
});