# C/C++ Klasörü

Bu klasör C/C++ için yapılandırma ve proje örnekleri barındırır.

## Hedef

- C/C++ kaynaklarını `src/cpp/src/` altına yerleştirmek
- Yapılandırma başlık dosyalarını `src/cpp/config/` altına almak
- Derleme ve test scriptlerini `src/cpp/build/` klasöründe tutmak

## Örnek Yapı

```
src/cpp/
├── README.md
├── config/
│   └── config.h
├── src/
│   └── main.cpp
└── build/
```

## Başlatma Örneği

```bash
cd src/cpp/src
g++ main.cpp -o app
./app
```
