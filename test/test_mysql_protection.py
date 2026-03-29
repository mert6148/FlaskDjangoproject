import os
import pytest

from src.mysql_protection import mysql_check


@pytest.fixture(autouse=True)
def unset_mysql_url(monkeypatch):
    monkeypatch.delenv("MYSQL_DATABASE_URL", raising=False)


def test_mysql_check_no_url():
    result = mysql_check()
    assert result["ok"] is False
    assert "ayarlı değil" in result["error"]


def test_mysql_check_bad_url(monkeypatch):
    monkeypatch.setenv("MYSQL_DATABASE_URL", "mysql://badformat")
    result = mysql_check()
    assert result["ok"] is False
    assert "URL formatı hatalı" in result["error"]


@pytest.mark.skip(reason="MySQL sunucusuna erişim gerektirir")
def test_mysql_check_connection_success(monkeypatch):
    monkeypatch.setenv("MYSQL_DATABASE_URL", "mysql+mysqlconnector://user:pass@127.0.0.1:3306/testdb")
    result = mysql_check()
    assert isinstance(result, dict)
