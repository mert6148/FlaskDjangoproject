import os
import sys
import s2clientprotocol
import sc2reader

def main():
    for event in sc2reader.load_replay('replay.SC2Replay'):
        print(event)
       
    dir_path = os.path.dirname(os.path.realpath(__file__))
    print(f"Current directory: {dir_path}")

def asert_example():
    assert 1 + 1 == 2, "Math is broken!"
    
def catch_exception_example():
    try:
        result = 10 / 0
    except ZeroDivisionError as e:
        s2clientprotocol.log.error(f"Caught an exception: {e}")

def log_example():
    s2clientprotocol.log.info("This is an info message")
    s2clientprotocol.log.warning("This is a warning message")
    s2clientprotocol.log.error("This is an error message")

    """
    Bu dosya, uygulamanın temel sınıflarını ve modellerini içerir.
    Sınıflar, uygulamanın farklı bileşenlerinde kullanılmak üzere tanımlarır.
    Aşağıda kullanıcı, cihaz, framework ve sistem modelleri örnek olarak verilmiştir.
     - User: Sistem kullanıcılarını temsil eder.
     - Device: Ağdaki cihazları temsil eder.
     - Framework: Desteklenen yazılım frameworklerini temsil eder.
     - SystemStatus: Sistemin genel durumunu temsil eder.
     - Registry: Cihazları ve frameworkleri yönetmek için merkezi bir sınıf.
     - Manager: Uygulamanın ana yöneticisi, tüm bileşenleri koordine eder.
     - Service: Uygulama servislerini temsil eder.
    """

def get_system_info(self) -> Dict:
    """Sistem bilgilerini al"""
    return {
        "os": os.name,
        "python_version": sys.version,
        "current_directory": os.getcwd()
    }

def list_files_in_directory(self, directory: str) -> list:
    """Belirtilen dizindeki dosyaları listele"""
    try:
        return os.listdir(directory)
    except Exception as e:
        s2clientprotocol.log.error(f"Error listing files in {directory}: {e}")
        return []