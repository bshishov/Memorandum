from django.shortcuts import render, redirect
from django.template import Context
from django.http import HttpResponse
from django.conf import settings
from PIL import Image
import importlib
import zlib
import re
import datetime
import mimetypes
import os.path
from . import items
from . import responses
from . import models
from . import item_reps
from .permissions import ALL_PERMISSIONS

mimetypes.init()


def get_editor(name):
    editor = FileEditor
    for possibleEditor in editors:
        if possibleEditor.name == name:
            editor = possibleEditor
            break
    return editor


def get_default_for(item):
    for possibleEditor in editors:
        if possibleEditor.can_handle(item):
            return possibleEditor
    raise LookupError('No suitable editor found for item {}'.format(item))


# abstract editor
class Editor:
    name = 'default_editor'
    thumbnail = 'blocks/thumbnails/file.html'

    def __init__(self):
        pass

    # returns if needed action was not found
    @classmethod
    def default(cls, item, request):
        return HttpResponse("No such action")

    @classmethod
    def show(cls, item, request):
        return HttpResponse("Sup, i handled " + item.name)

    @classmethod
    def rename(cls, item, request):
        new_name = request.POST.get('name', item.name)
        if not item.is_root:
            item.rename(new_name)
        return redirect(item.factory.get_url(item.rel_path))

    @classmethod
    def share(cls, item, request):
        user_email = request.POST.get('target', "")
        permissions = int(request.POST.get('permissions', "-1"))
        rel_path = item.rel_path

        if permissions not in ALL_PERMISSIONS:
            raise RuntimeError('Invalid sharing type')

        share_with = models.CustomUser.objects.get(email=user_email)
        if share_with.id == request.user.id:
            raise RuntimeError('Can not share to yourself')

        sharing_note, create = models.Sharing.objects.get_or_create(owner=item.owner, item=rel_path,
                                                                    shared_with=share_with,
                                                                    permissions=permissions,
                                                                    defaults={'permissions': 0})
        sharing_note.save()

        return redirect(item.factory.get_url(item.rel_path))

    @classmethod
    def unshare(cls, item, request):
        sharing_id = request.GET.get('id', None)

        if not sharing_id:
            raise ValueError('Invalid sharing id')

        sharing = models.Sharing.objects.get(id=sharing_id)

        if sharing.owner != request.user:
            raise PermissionError('Only owner can remove sharings')

        sharing.delete()
        return redirect(item.factory.get_url(item.rel_path))

    @classmethod
    def delete(cls, item, request):
        item.delete()
        return redirect(item.parent.factory.get_url(item.parent.rel_path))


# editor for directories
class DirectoryEditor(Editor):
    name = 'directory'
    thumbnail = 'blocks/thumbnails/dir.html'

    def __init__(self):
        super(DirectoryEditor, self).__init__()

    def can_handle(self, item):
        if item.is_dir:
            return True
        else:
            return False

    @classmethod
    def show(cls, item, request):
        item_rep = item_reps.DirectoryRepresentation(item)
        child_list = item.children
        child_files = []
        child_dirs = []
        for child in child_list:
            if child.is_dir:
                child_dirs.append(item_reps.DirectoryRepresentation(child))
            else:
                child_files.append(item_reps.FileRepresentation(child))
        context = Context({'item_rep': item_rep, 'child_dirs': child_dirs, 'child_files': child_files,})
        return render(request, "dir.html", context)

    @classmethod
    def download(cls, item, request):
        data = item.make_zip()
        response = HttpResponse(data, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="%s"' % (item.name + '.zip')
        return response

    @classmethod
    def upload(cls, item, request):
        if request.method == 'POST' and 'file' in request.FILES:
            uploaded_file = request.FILES['file']
            new_rel_path = item.make_path_to_new_item(uploaded_file.name)
            new_item = item.factory.new_file(new_rel_path)
            new_item.write_chunks(uploaded_file.chunks())
        return redirect(item.factory.get_url(item.rel_path))

    @classmethod
    def create_new(cls, item, request):
        name = request.POST.get('name', "")
        item_type = request.POST.get('item_type', "file")

        if item_type == 'directory':
            if not name:
                name = 'New folder'

            new_dir = item.create_child_directory(name)
            new_dir.create_empty()
            if new_dir is not None:
                return redirect(new_dir.factory.get_url(new_dir.rel_path))

        if item_type == 'file':
            if not name:
                name = 'New File'

            new_file = item.create_child_file(name)
            new_file.create_empty()
            if new_file is not None:
                return redirect(new_file.factory.get_url(new_file.rel_path))

        return redirect(item.factory.get_url(item.rel_path))


# common editor for files
class FileEditor(Editor):
    name = 'file'
    extensions = []  # list of extensions that this editor can handle
    thumbnail = "blocks/thumbnails/file.html"

    def __init__(self):
        super(FileEditor, self).__init__()

    def can_handle(self, item):
        if self.extensions:
            return item.extension in self.extensions
        return not item.is_dir

    @classmethod
    def raw(cls, item, request):
        data = item.read_byte()
        return HttpResponse(data, content_type=item.mime)

    @classmethod
    def download(cls, item, request):
        content = item.read_byte()
        response = HttpResponse(content, content_type='application/force-download')
        response['Content-Disposition'] = 'attachment; filename=' + item.name
        response['X-Sendfile'] = item.name
        return response

    @classmethod
    def save(cls, item, request):
        data = request.POST.get('data', None)
        errors = []
        if data is None:
            errors.append('No data received')
            return responses.AjaxResponse(responses.RESULT_ERROR, 'No data received', errors)
        item.write_content(data)
        return responses.AjaxResponse(responses.RESULT_OK, 'File saved successfully')

    @classmethod
    def show(cls, item, request):
        item_rep = item_reps.FileRepresentation(item)
        context = Context({'item_rep': item_rep})
        return render(request, "files/default.html", context)


class CodeEditor(FileEditor):
    name = "code"
    extensions = [".txt", ".hex", ".bin",
                  '.xml', '.json',
                  '.ini', '.cfg',
                  '.c', '.cpp', '.h', '.hpp',
                  '.py', '.cs',
                  '.html', '.htm', '.css', '.js', '.less',
                  ]

    def __init__(self):
        super(CodeEditor, self).__init__()

    @classmethod
    def show(cls, item, request):
        item_rep = item_reps.FileRepresentation(item)
        context = Context({'item_rep': item_rep})
        return render(request, "files/code.html", context)


class MarkdownEditor(FileEditor):
    name = "markdown"
    extensions = [".markdown", ".md"]

    def __init__(self):
        super(MarkdownEditor, self).__init__()

    @classmethod
    def show(cls, item, request):
        item_rep = item_reps.FileRepresentation(item)
        context = Context({'item_rep': item_rep})
        return render(request, "files/md.html", context)


class ImageEditor(FileEditor):
    name = "image"
    extensions = [".jpg", ".bmp", ".gif", ".png"]
    thumbnail = "blocks/thumbnails/image.html"

    THUMBS_FOLDER = 'thumbs'
    THUMB_SIZE = (128, 128)
    THUMB_FORMAT = 'PNG'
    THUMBS_CACHE_SECONDS = 604800

    thumbs_items_factory = items.PlainItemFactory(os.path.join(settings.MEDIA_ROOT, THUMBS_FOLDER))

    def __init__(self):
        super(ImageEditor, self).__init__()

    @classmethod
    def preview(cls, item, request):

        media_dir_rel_path = os.path.join(str(item.owner.id), item.parent.rel_path)
        media_directory_item = ImageEditor.thumbs_items_factory.get_or_create_directory(media_dir_rel_path)

        if not media_directory_item.exists:
            media_directory_item.create_empty()

        preview_item_rel_path = os.path.join(media_dir_rel_path, item.name)
        preview_item = media_directory_item.factory.get_or_create_file(preview_item_rel_path)
        if not preview_item.exists or preview_item.modified_time < item.modified_time:
            image = Image.open(item.absolute_path)
            image.thumbnail(ImageEditor.THUMB_SIZE, Image.ANTIALIAS)
            image.save(preview_item.absolute_path, format=ImageEditor.THUMB_FORMAT)

        response = ImageEditor.raw(preview_item, request)
        response['Cache-Control'] = 'public, max-age={}'.format(ImageEditor.THUMBS_CACHE_SECONDS)
        response['Last-modified'] = '{}'.format(preview_item.modified)
        return response

    @classmethod
    def show(cls, item, request):
        item_rep = item_reps.FileRepresentation(item)
        context = Context({'item_rep': item_rep})
        return render(request, "files/image.html", context)


class AudioEditor(FileEditor):
    name = "audio"
    extensions = [".mp3", ".wav", ".m3u", ".ogg", '.aac']
    thumbnail = "blocks/thumbnails/file.html"

    def __init__(self):
        super(AudioEditor, self).__init__()

    @classmethod
    def show(cls, item, request):
        item_rep = item_reps.FileRepresentation(item)
        context = Context({'item_rep': item_rep})
        return render(request, "files/audio.html", context)


class VideoEditor(FileEditor):
    name = "video"
    extensions = [".mp4", ".avi", ".mov", ".webm"]
    thumbnail = "blocks/thumbnails/file.html"

    def __init__(self):
        super(VideoEditor, self).__init__()

    @classmethod
    def show(cls, item, request):
        item_rep = item_reps.FileRepresentation(item)
        context = Context({'item_rep': item_rep})
        return render(request, "files/video.html", context)


class OnlyOfficeEditor(FileEditor):
    EXTS_DOCUMENT = [".doc", ".docx"]
    EXTS_SPREADSHEET = [".xls", ".xlsx"]
    EXTS_PRESENTATION = [".ppt", ".pptx"]
    EXTENSIONS = EXTS_DOCUMENT + EXTS_SPREADSHEET + EXTS_PRESENTATION

    def __init__(self):
        super(OnlyOfficeEditor, self).__init__()
        self.name = "office"
        self.thumbnail = "blocks/thumbnails/file.html"
        self.extensions = self.EXTENSIONS

    @classmethod
    def show(cls, item, request):
        now = datetime.datetime.now()
        curr_date = str(now.day) + "." + str(now.month) + "." + str(now.year)
        api_src = settings.ONLYOFFICE_SERVER + "/web-apps/apps/api/documents/api.js"
        item_rep = item_reps.FileRepresentation(item)
        last_breadcrumb = len(item_rep.breadcrumbs) - 1
        item_url = item_rep.url
        parent_url = item_rep.breadcrumbs[last_breadcrumb].url
        client_ip = request.META['REMOTE_ADDR']
        doc_editor_key = OnlyOfficeEditor.get_doc_editor_key(client_ip, item_rep.name)
        doc_type = OnlyOfficeEditor.get_document_type(item)
        ext = item_rep.item.extension.lstrip(".")
        context = Context({'item_rep': item_rep,
                           'api_src': api_src,
                           'http_host': request.META['HTTP_HOST'],
                           'doc_type': doc_type, 'doc_editor_key': doc_editor_key,
                           'client_ip': client_ip, 'parent_url': parent_url,
                           'curr_date': curr_date, 'ext': ext, 'item_url': item_url})
        return render(request, "files/office.html", context)

    @classmethod
    def get_document_type(cls, item):
        if item.extension in cls.EXTS_DOCUMENT:
            return "text"
        elif item.extension in cls.EXTS_SPREADSHEET:
            return "spreadsheet"
        elif item.extension in cls.EXTS_PRESENTATION:
            return "presentation"
        else:
            return ""

    @classmethod
    def get_doc_editor_key(cls, ip, name):
        return OnlyOfficeEditor.generate_revision_id(ip + "/" + name)

    @classmethod
    def generate_revision_id(cls, key):
        if len(key) > 20:
            key = zlib.crc32(key.encode('utf-8'))
        key = re.sub("[^0-9-.a-zA-Z_=]", "_", str(key))
        limits = [20, len(key)]
        key = key[:min(limits)]
        return key

    @classmethod
    def track(cls, item, request, permissions):
        pass

    @classmethod
    def save_callback(cls, item, request, permissions):
        print(request.GET)
        pass


class PdfEditor(FileEditor):
    name = "pdf"
    extensions = [".pdf"]
    thumbnail = "blocks/thumbnails/file.html"

    def __init__(self):
        super(PdfEditor, self).__init__()

    @classmethod
    def show(cls, item, request):
        item_rep = item_reps.FileRepresentation(item)
        context = Context({'item_rep': item_rep})
        return render(request, "files/pdf.html", context)


class UrlEditor(FileEditor):
    name = 'url'
    extensions = ['.url']

    def __init__(self):
        super(UrlEditor, self).__init__()

    @classmethod
    def show(cls, item, request):
        item_rep = item_reps.FileRepresentation(item)
        item_rep.target_url = UrlEditor.__get_url(item)
        context = Context({'item_rep': item_rep})
        return render(request, "files/url.html", context)

    @classmethod
    def __get_url(cls, item):
        content = item.read_text()
        match = re.search("url\s*=(.*)", content, flags=re.IGNORECASE)
        if not match:
            raise RuntimeError('Incorrect URL file format')
        if not match.group(1):
            raise RuntimeError('Incorrect URL')
        return match.group(1)


def __init_editors():
    default_editors = [
        'MarkdownEditor',
        'ImageEditor',
        'AudioEditor',
        'VideoEditor',
        'UrlEditor',
        'OnlyOfficeEditor',
        'PdfEditor',
        'CodeEditor',
        'FileEditor',
        'DirectoryEditor',
    ]
    if hasattr(settings, 'EDITORS') and len(settings.EDITORS) > 0:
        editor_names = settings.EDITORS
    else:
        editor_names = default_editors
    initialized_editors = []
    for editor_name in editor_names:
        module_path_parts = editor_name.rsplit(".", 1)
        if len(module_path_parts) > 1:
            module = importlib.import_module(module_path_parts[0])
            editor_name = module_path_parts[1]
            editor_constructor = getattr(module, editor_name)
            initialized_editors.append(editor_constructor())
        else:
            editor = globals()[editor_name]()
            initialized_editors.append(editor)
    return initialized_editors

editors = __init_editors()
