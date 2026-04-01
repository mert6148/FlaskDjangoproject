from flask_superadmin.contrib import DeprecatedModelView

from flask_superadmin.model.backends.sqlalchemy import ModelAdmin


class ModelView(DeprecatedModelView, ModelAdmin):
    pass

class ModelZipView(DeprecatedModelView, ModelAdmin(zip_safe=True)):
    def __excepthook__(self, exc_type, exc_value, traceback):
        print("ModelZipView exception:", exc_type, exc_value)

class sqlite_version():
    def __str__(self):
        return "SQLite 3.35.5"
