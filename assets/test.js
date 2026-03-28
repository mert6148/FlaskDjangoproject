const test = "This is a test file for the assets directory.";
const anotherTest = "This file is used to test the functionality of the assets module.";

export { test, anotherTest };
export default test;

document.addEventListener("DOMContentLoaded", () => {
    console.log("Test file loaded successfully.");
    console.log("Test variable:", test);
    console.log("Another test variable:", anotherTest);
});

document.getElementById("test-button").addEventListener("click", () => {
    alert("Button clicked! Test file is working.");
});

if (typeof module !== "undefined" && module.exports) {
    module.exports = {
        test,
        anotherTest
    };
}
