import importlib
import json
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[4]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))


def _import_optional(name, default=None):
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError:
        return default


django_urls_mod = _import_optional("fastadmin.api.frameworks.django.app.urls")
fastapi_app_mod = _import_optional("fastadmin.api.frameworks.fastapi.app")
flask_app_mod = _import_optional("fastadmin.api.frameworks.flask.app")

get_django_admin_urls = getattr(django_urls_mod, "get_admin_urls", None)
fastapi_app = getattr(fastapi_app_mod, "app", None)
flask_app = getattr(flask_app_mod, "app", None)


def _make_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def ensure_frontend_skeleton():
    """Frontend klasörleri için çalışma iskeletleri oluşturur."""
    project_root = Path(__file__).resolve().parents[4]
    frontend_folders = [
        project_root / "app",
        project_root / "assets",
        project_root / "src",
    ]

    for folder in frontend_folders:
        (folder / "frontend_readme.md").write_text(
            f"# {folder.name} frontend entegrasyonu\nBu klasör proje için Python + JS + Docker entegrasyonu içerir.\n", encoding="utf-8"
        )
        (folder / "index.html").write_text(
            """<!DOCTYPE html>
<html lang=\"tr\">
<head><meta charset=\"UTF-8\"><title>FastAdmin Frontend</title></head>
<body>
  <h1>FastAdmin Frontend Şablonu</h1>
  <p>Bu dosya, {name} klasörü için otomatik oluşturuldu.</p>
</body>
</html>""".replace("{name}", folder.name),
            encoding="utf-8",
        )
        _make_file(folder / "app.py", "# Python framework starter script for {}\n".format(folder.name))
        _make_file(folder / "docker-compose.yml", "# docker-compose placeholder for {}".format(folder.name))

    return frontend_folders


def create_framework_manifest():
    """Açıkça hangi frameworkler aktif ve kullanılabilir."""
    project_root = Path(__file__).resolve().parents[3]
    manifest = {
        "flask": True,
        "fastapi": True,
        "django": True,
        "api_entrypoints": {
            "flask": "fastadmin.api.frameworks.flask.app.app",
            "fastapi": "fastadmin.api.frameworks.fastapi.app.app",
            "django": "fastadmin.api.frameworks.django.app.urls.get_admin_urls",
        },
    }
    fname = project_root / "frontend_frameworks_manifest.json"
    fname.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return fname


def main():
    created = ensure_frontend_skeleton()
    manifest = create_framework_manifest()
    print("Oluşturulan front-end klasörleri:")
    for path in created:
        print(" -", path)
    print("Manifest kaydedildi:", manifest)
    print("Frameworkler hazır:")
    print(" - flask app:", flask_app)
    print(" - fastapi app:", fastapi_app)
    if callable(get_django_admin_urls):
        print(" - django admin urls:", get_django_admin_urls())
    else:
        print(" - django admin urls: (import edilemedi veya yüklü değil)")


if __name__ == "__main__":
    main()
