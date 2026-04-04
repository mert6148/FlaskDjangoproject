import os
import mysql.connector
from mysql.connector import errorcode


def mysql_check():
    mysql_url = os.environ.get("MYSQL_DATABASE_URL")
    if not mysql_url:
        return {"ok": False, "error": "MYSQL_DATABASE_URL ayarlı değil"}

    # örnek format: mysql+mysqlconnector://user:pass@host:3306/db
    import re
    m = re.match(r"^(?:mysql\+mysqlconnector://)?(?P<user>[^:]+):(?P<pass>[^@]+)@(?P<host>[^:/]+)(?::(?P<port>\d+))?/(?P<db>\w+)", mysql_url)
    if not m:
        return {"ok": False, "error": "URL formatı hatalı"}

    params = m.groupdict()
    try:
        cnx = mysql.connector.connect(
            user=params["user"],
            password=params["pass"],
            host=params["host"],
            port=int(params.get("port") or 3306),
            database=params["db"],
            connection_timeout=5,
        )
        cursor = cnx.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cnx.close()
        return {"ok": bool(result and result[0] == 1), "details": result}
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            return {"ok": False, "error": "Kimlik doğrulama başarısız"}
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            return {"ok": False, "error": "Veritabanı bulunamadı"}
        else:
            return {"ok": False, "error": str(err)}


if __name__ == "__main__":
    print(mysql_check())
