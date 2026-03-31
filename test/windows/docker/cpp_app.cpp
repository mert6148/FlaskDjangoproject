#include <iostream>
#include <fstream>
#include <windows.h>

int main() {
    std::cout << "C++ Windows hardening Docker testi basladi" << std::endl;

    auto check_service = [&](const std::wstring& serviceName) {
        SERVICE_STATUS_PROCESS ssStatus;
        DWORD bytesNeeded;
        SC_HANDLE hSCM = OpenSCManager(NULL, NULL, SC_MANAGER_CONNECT);
        if (!hSCM) return false;
        SC_HANDLE hService = OpenService(hSCM, serviceName.c_str(), SERVICE_QUERY_STATUS);
        if (!hService) {
            CloseServiceHandle(hSCM);
            return false;
        }
        bool ok = QueryServiceStatusEx(hService, SC_STATUS_PROCESS_INFO, reinterpret_cast<LPBYTE>(&ssStatus), sizeof(ssStatus), &bytesNeeded);
        CloseServiceHandle(hService);
        CloseServiceHandle(hSCM);
        return ok && ssStatus.dwCurrentState == SERVICE_RUNNING;
    };

    bool defender = check_service(L"WinDefend");
    std::cout << "Windows Defender service running: " << (defender ? "Yes" : "No") << std::endl;

    bool firewall = check_service(L"MpsSvc");
    std::cout << "Windows Firewall service running: " << (firewall ? "Yes" : "No") << std::endl;

    std::ofstream report("/workspace/test/windows/docker/cpp_hardening_report.txt");
    report << "Defender=" << (defender ? "1" : "0") << "\n";
    report << "Firewall=" << (firewall ? "1" : "0") << "\n";
    report.close();

    return (defender && firewall) ? 0 : 1;
}
