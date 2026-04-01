"""
fileadmin.py — Dosya Yönetim Arayüzü (Python 3 Uyumlu)
=======================================================
Düzeltmeler (orijinal fileadmin.py):
  - 'import urlparse' → 'from urllib.parse import urljoin' (Py3)
  - 'except Exception, ex:' → 'except Exception as ex:' (Py3)
  - 'from werkzeug import secure_filename' → 'from werkzeug.utils import ...'
  - 'TextField' → 'StringField' (WTForms 3.x)
"""

import os
import os.path as op
import platform
import re
import shutil
from operator import itemgetter
from urllib.parse import urljoin                    # Py2: urlparse.urljoin

from werkzeug.utils import secure_filename          # Py2: from werkzeug import

from flask import flash, url_for, redirect, abort, request

from flask_superadmin.base import BaseView, expose
from flask_superadmin.babel import gettext, lazy_gettext
from flask_superadmin import form
from flask_wtf.file import FileField
from wtforms import StringField, ValidationError    # Py3 WTForms: StringField


class NameForm(form.BaseForm):
    """
    Dosya/dizin adı giriş formu.
    *nix ve Windows için geçerli ad doğrulaması yapar.
    """
    name = StringField()                            # TextField → StringField

    regexp = re.compile(
        r'^(?!^(PRN|AUX|CLOCK\$|NUL|CON|COM\d|LPT\d|\..*)'
        r'(\..+)?$)[^\x00-\x1f\\?*:\";|/]+$'
    )

    def validate_name(self, field):
        if not self.regexp.match(field.data or ""):
            raise ValidationError(gettext('Invalid directory name'))


class UploadForm(form.BaseForm):
    """
    Dosya yükleme formu.
    FileAdmin örneğiyle birlikte çalışarak uzantı doğrulaması yapar.
    """
    upload = FileField(lazy_gettext('File to upload'))

    def __init__(self, admin):
        self.admin = admin
        super().__init__()

    def validate_upload(self, field):
        if not self.upload.has_file():
            raise ValidationError(gettext('File required.'))
        filename = self.upload.data.filename
        if not self.admin.is_file_allowed(filename):
            raise ValidationError(gettext('Invalid file type.'))


class FileAdmin(BaseView):
    """
    Basit dosya yönetim arayüzü.

    Zorunlu parametreler:

    ``base_path``
        Yönetilecek dizinin tam yolu.
    ``base_url``
        Dizin için temel URL. Statik dosya bağlantıları üretmek için kullanılır.

    Örnek kullanım::

        admin = Admin()
        path  = op.join(op.dirname(__file__), 'static')
        admin.add_view(
            FileAdmin(path, '/static/', name='Statik Dosyalar')
        )
        admin.setup_app(app)

    Özelleştirilebilir sınıf değişkenleri:

    .. code-block:: python

        class OzelFileAdmin(FileAdmin):
            can_upload       = True    # Yüklemeye izin ver
            can_delete       = True    # Silmeye izin ver
            can_delete_dirs  = True    # Dizin silmeye izin ver
            can_mkdir        = True    # Dizin oluşturmaya izin ver
            can_rename       = True    # Yeniden adlandırmaya izin ver
            allowed_extensions = ('jpg', 'png', 'pdf')  # İzin verilen uzantılar
    """

    # ── Özelleştirilebilir değişkenler ────────────────────────────────────────
    can_upload      = True
    can_delete      = True
    can_delete_dirs = True
    can_mkdir       = True
    can_rename      = True
    allowed_extensions = None   # None = tümüne izin ver

    list_template   = 'admin/file/list.html'
    upload_template = 'admin/file/form.html'
    mkdir_template  = 'admin/file/form.html'
    rename_template = 'admin/file/rename.html'

    def __init__(self, base_path, base_url,
                 name=None, category=None, endpoint=None, url=None):
        """
        :param base_path: Temel dosya depolama dizini (tam yol).
        :param base_url:  Dosyalar için temel URL.
        :param name:      Görünüm adı (varsayılan: sınıf adı).
        :param category:  Görünüm kategorisi.
        :param endpoint:  Endpoint adı.
        :param url:       Görünüm URL'si.
        """
        self.base_path   = base_path
        self.base_url    = base_url
        self._on_windows = platform.system() == 'Windows'

        if self.allowed_extensions and not isinstance(self.allowed_extensions, set):
            self.allowed_extensions = set(self.allowed_extensions)

        super().__init__(name, category, endpoint, url)

    # ── Güvenlik yardımcıları ─────────────────────────────────────────────────

    def is_accessible_path(self, path: str) -> bool:
        """
        Yolun mevcut kullanıcı için erişilebilir olup olmadığını doğrular.
        Özelleştirmek için override edin.

        :param path: Kök dizine göre bağıl yol.
        :returns: Erişim izni varsa True.
        """
        return True

    def get_base_path(self) -> str:
        """Temel yolu döndürür. Kullanıcı bazlı dizinler için override edin."""
        return op.normpath(self.base_path)

    def get_base_url(self) -> str:
        """Temel URL'yi döndürür. Override ile özelleştirilebilir."""
        return self.base_url

    def is_file_allowed(self, filename: str) -> bool:
        """
        Dosyanın yüklenebilir olup olmadığını kontrol eder.

        :param filename: Kaynak dosya adı.
        :returns: Yüklemeye izin varsa True.
        """
        ext = op.splitext(filename)[1].lower().lstrip('.')
        if self.allowed_extensions and ext not in self.allowed_extensions:
            return False
        return True

    def is_in_folder(self, base_path: str, directory: str) -> bool:
        """
        ``directory``'nin ``base_path`` içinde olup olmadığını doğrular.

        :param base_path: Temel dizin yolu.
        :param directory: Kontrol edilecek dizin.
        :returns: directory, base_path içindeyse True.
        """
        return op.normpath(directory).startswith(base_path)

    def save_file(self, path: str, file_data) -> None:
        """
        Yüklenen dosyayı diske kaydeder.

        :param path:      Kaydedilecek hedef yol.
        :param file_data: Werkzeug ``FileStorage`` nesnesi.
        """
        file_data.save(path)

    # ── URL üretici yardımcılar ───────────────────────────────────────────────

    def _get_dir_url(self, endpoint: str, path: str, **kwargs) -> str:
        """
        Dizin URL'sini oluşturur.

        :param endpoint: Endpoint adı.
        :param path:     Dizin yolu.
        :returns: Flask ``url_for`` çıktısı.
        """
        if not path:
            return url_for(endpoint)
        if self._on_windows:
            path = path.replace('\\', '/')
        return url_for(endpoint, path=path, **kwargs)

    def _get_file_url(self, path: str) -> str:
        """
        Statik dosya URL'sini döndürür.

        :param path: Statik dosya yolu.
        :returns: Tam dosya URL'si.
        """
        return urljoin(self.get_base_url(), path)  # Py3: urljoin

    def _normalize_path(self, path) -> tuple[str, str, str]:
        """
        Yolu doğrular ve normalleştirir.

        Yol temel dizine göre bağıl değilse veya mevcut değilse 404 fırlatır.

        :returns: (base_path, directory, path) üçlüsü.
        """
        base_path = self.get_base_path()
        if path is None:
            return base_path, base_path, ''
        path      = op.normpath(path)
        directory = op.normpath(op.join(base_path, path))
        if not self.is_in_folder(base_path, directory):
            abort(404)
        if not op.exists(directory):
            abort(404)
        return base_path, directory, path

    # ── Görünüm rotaları ──────────────────────────────────────────────────────

    @expose('/')
    @expose('/b/<path:path>')
    def index(self, path=None):
        """
        Dizin listeleme görünümü.

        :param path: İsteğe bağlı alt dizin yolu.
                     Verilmezse temel dizin kullanılır.
        """
        base_path, directory, path = self._normalize_path(path)
        items = []

        if directory != base_path:
            parent_path = op.normpath(op.join(path, '..'))
            items.append(('..', None if parent_path == '.' else parent_path, True, 0))

        for f in os.listdir(directory):
            fp = op.join(directory, f)
            items.append((f, op.join(path, f), op.isdir(fp), op.getsize(fp)))

        items.sort(key=itemgetter(2), reverse=True)

        breadcrumbs, acc = [], []
        for part in path.split(os.sep):
            if part:
                acc.append(part)
                breadcrumbs.append((part, op.join(*acc)))

        return self.render(
            self.list_template,
            dir_path=path,
            breadcrumbs=breadcrumbs,
            get_dir_url=self._get_dir_url,
            get_file_url=self._get_file_url,
            items=items,
            base_path=base_path,
        )

    @expose('/upload/', methods=('GET', 'POST'))
    @expose('/upload/<path:path>', methods=('GET', 'POST'))
    def upload(self, path=None):
        """
        Dosya yükleme görünümü.

        :param path: Yükleme dizini. Verilmezse temel dizin kullanılır.
        """
        base_path, directory, path = self._normalize_path(path)

        if not self.can_upload:
            flash(gettext('File uploading is disabled.'), 'error')
            return redirect(self._get_dir_url('.index', path))

        upload_form = UploadForm(self)
        if upload_form.validate_on_submit():
            filename = op.join(
                directory,
                secure_filename(upload_form.upload.data.filename)
            )
            if op.exists(filename):
                flash(gettext('File "%(name)s" already exists.',
                              name=upload_form.upload.data.filename), 'error')
            else:
                try:
                    self.save_file(filename, upload_form.upload.data)
                    return redirect(self._get_dir_url('.index', path))
                except Exception as ex:                      # Py3: 'as ex'
                    flash(gettext('Failed to save file: %(error)s', error=ex))

        return self.render(
            self.upload_template,
            form=upload_form,
            base_path=base_path,
            path=path,
            msg=gettext(u'Upload a file'),
        )

    @expose('/mkdir/', methods=('GET', 'POST'))
    @expose('/mkdir/<path:path>', methods=('GET', 'POST'))
    def mkdir(self, path=None):
        """
        Dizin oluşturma görünümü.

        :param path: Üst dizin yolu.
        """
        base_path, directory, path = self._normalize_path(path)
        dir_url = self._get_dir_url('.index', path)

        if not self.can_mkdir:
            flash(gettext('Directory creation is disabled.'), 'error')
            return redirect(dir_url)

        mkdir_form = NameForm(request.form)
        if mkdir_form.validate_on_submit():
            try:
                os.mkdir(op.join(directory, mkdir_form.name.data))
                return redirect(dir_url)
            except Exception as ex:                          # Py3: 'as ex'
                flash(gettext('Failed to create directory: %(error)s',
                              error=ex), 'error')

        return self.render(
            self.mkdir_template,
            form=mkdir_form,
            dir_url=dir_url,
            base_path=base_path,
            path=path,
            msg=gettext(u'Create a new directory'),
        )

    @expose('/delete/', methods=('POST',))
    def delete(self):
        """Dosya veya dizin silme görünümü."""
        path = request.form.get('path')
        if not path:
            return redirect(url_for('.index'))

        base_path, full_path, path = self._normalize_path(path)
        return_url = self._get_dir_url('.index', op.dirname(path))

        if not self.can_delete:
            flash(gettext('Deletion is disabled.'))
            return redirect(return_url)

        if op.isdir(full_path):
            if not self.can_delete_dirs:
                flash(gettext('Directory deletion is disabled.'))
                return redirect(return_url)
            try:
                shutil.rmtree(full_path)
                flash(gettext('Directory "%(name)s" was successfully deleted.',
                              name=path))
            except Exception as ex:                          # Py3: 'as ex'
                flash(gettext('Failed to delete directory: %(error)s',
                              error=ex), 'error')
        else:
            try:
                os.remove(full_path)
                flash(gettext('File "%(name)s" was successfully deleted.',
                              name=path))
            except Exception as ex:                          # Py3: 'as ex'
                flash(gettext('Failed to delete file: %(name)s',
                              name=ex), 'error')

        return redirect(return_url)

    @expose('/rename/', methods=('GET', 'POST'))
    def rename(self):
        """Dosya veya dizin yeniden adlandırma görünümü."""
        path = request.args.get('path')
        if not path:
            return redirect(url_for('.index'))

        base_path, full_path, path = self._normalize_path(path)
        return_url = self._get_dir_url('.index', op.dirname(path))

        if not self.can_rename:
            flash(gettext('Renaming is disabled.'))
            return redirect(return_url)

        if not op.exists(full_path):
            flash(gettext('Path does not exist.'))
            return redirect(return_url)

        rename_form = NameForm(request.form, name=op.basename(path))
        if rename_form.validate_on_submit():
            try:
                dir_base = op.dirname(full_path)
                filename = secure_filename(rename_form.name.data)
                os.rename(full_path, op.join(dir_base, filename))
                flash(gettext(
                    'Successfully renamed "%(src)s" to "%(dst)s"',
                    src=op.basename(path), dst=filename
                ))
            except Exception as ex:                          # Py3: 'as ex'
                flash(gettext('Failed to rename: %(error)s', error=ex), 'error')

            return redirect(return_url)

        return self.render(
            self.rename_template,
            form=rename_form,
            path=op.dirname(path),
            name=op.basename(path),
            dir_url=return_url,
            base_path=base_path,
        )