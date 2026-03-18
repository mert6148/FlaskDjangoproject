const name = "system";
const version = "1.0.0";
const AWSTemplateFormatVersion = {
    version: "2010-09-09"
};
const system = {
    name,
    version,
    AWSTemplateFormatVersion
};

document.addEventListener("DOMContentLoaded", function() {
    const systemElement = document.getElementById("system");
    if (systemElement) {
        systemElement.textContent = JSON.stringify(system);
    }
});

document.addEventListener("DOMContentLoaded", function() {
    const nameElement = document.getElementById("name");
    if (nameElement) {
        nameElement.textContent = JSON.stringify(name);
    }
});

document.addEventListener("DOMContentLoaded", function() {
    const versionElement = document.getElementById("version");
    if (versionElement) {
        versionElement.textContent = JSON.stringify(version);
    }
});

document.addEventListener("DOMContentLoaded", function() {
    const AWSTemplateFormatVersionElement = document.getElementById("AWSTemplateFormatVersion");
    if (AWSTemplateFormatVersionElement) {
        AWSTemplateFormatVersionElement.textContent = JSON.stringify(AWSTemplateFormatVersion);
    }
});