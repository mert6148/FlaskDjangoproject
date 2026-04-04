# C/C++ Dökümantasyonu

`src/cpp/` klasörü C/C++ için yapılandırma rehberi ve örnekleri barındırır.

## İçerik

Bu klasörde şu anda kod dosyası yoktur, ancak C/C++ entegrasyonu için temel yapılandırma ve proje düzeni aşağıdaki gibidir.

## Örnek Dizin Yapısı

```
src/cpp/
├── README.md
├── config/
│   └── config.h
├── src/
│   └── main.cpp
└── build/
```

## Örnek `main.cpp`

```cpp
#include <iostream>
#include <string>

int main() {
    std::cout << "Flask-Django C/C++ yapılandırma örneği" << std::endl;
    return 0;
}
```

## Önerilen Kullanım

1. C/C++ kaynaklarınızı `src/cpp/src/` altına ekleyin.
2. Yapılandırma başlık dosyalarını `src/cpp/config/` altına koyun.
3. Derlemek için:

```bash
cd src/cpp/src
g++ main.cpp -o app
./app
```

## Notlar

- `src/cpp/` klasörü, C/C++ entegrasyonu için ayrılmıştır.
- Bu klasörde ileride `CMakeLists.txt`, `Makefile` veya `vcpkg` konfigürasyonları eklenebilir.
