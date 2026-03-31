FROM mcr.microsoft.com/windows/servercore:ltsc2022

SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop';"]

RUN Set-ExecutionPolicy Bypass -Scope LocalMachine -Force
RUN choco install -y visualstudio2019buildtools --package-parameters "--add Microsoft.VisualCpp.BuildTools"  

WORKDIR /workspace

COPY cpp_app.cpp ./
RUN cl /EHsc cpp_app.cpp /Fe:cpp_hardening_test.exe

CMD ["cmd", "/c", "cpp_hardening_test.exe"]
