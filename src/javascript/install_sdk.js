const { exec } = require('child_process');
const fs = require('fs');

console.log('SDK Kurulum Programı - JavaScript');
console.log('Vue.js ve Oracle JET frameworklerini kurmak için...');

// Node.js kontrolü
console.log('1. Node.js kontrol ediliyor...');
exec('node --version', (error, stdout, stderr) => {
    if (error) {
        console.error(`Hata: ${error.message}`);
        return;
    }
    console.log(`Node.js versiyonu: ${stdout}`);
});

// npm kontrolü
console.log('2. npm kontrol ediliyor...');
exec('npm --version', (error, stdout, stderr) => {
    if (error) {
        console.error(`Hata: ${error.message}`);
        return;
    }
    console.log(`npm versiyonu: ${stdout}`);
});

// Vue.js kurulum
console.log('3. Vue.js kuruluyor...');
exec('npm install -g @vue/cli', (error, stdout, stderr) => {
    if (error) {
        console.error(`Hata: ${error.message}`);
        return;
    }
    console.log('Vue.js kuruldu.');
});

// Oracle JET kurulum
console.log('4. Oracle JET kuruluyor...');
exec('npm install -g @oracle/oraclejet-cli', (error, stdout, stderr) => {
    if (error) {
        console.error(`Hata: ${error.message}`);
        return;
    }
    console.log('Oracle JET kuruldu.');
});

console.log('Kurulum tamamlandı!');