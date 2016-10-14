from django.shortcuts import render, redirect
from django.template import Context
from django.http import HttpResponse
from django.conf import settings
import importlib
import zlib
import re
import datetime
import mimetypes
from . import items
from . import views
from . import models
from . import item_reps

mimetypes.init()

def get_editor(name):
    all_editors = get_all_editors()
    editor = UniversalFileEditor
    for possibleEditor in all_editors:
        if possibleEditor.name == name:
            editor = possibleEditor
            break
    return editor


def get_all_editors():
    default_editors = [
        'CodeEditor',
        'MarkdownEditor',
        'DirectoryEditor',
        'ImageEditor',
        'AudioEditor',
        'VideoEditor',
        'OnlyOfficeEditor',
        'PdfEditor',
        'UniversalFileEditor'
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


def get_default_for(item):
    all_editors = get_all_editors()
    for possibleEditor in all_editors:
        if possibleEditor.can_handle(item):
            default_editor = possibleEditor
            break
    return default_editor


# abstract editor
class Editor:
    def __init__(self):
        self.name = "editor"
        # list of extensions that can be handle
        self.extensions = []
        self.thumbnail = "blocks/thumbnails/file.html"

    # returns if needed action was not found
    def not_exists(self):
        return HttpResponse("No such action")

    @classmethod
    def show(cls, item, request, permissions):
        return HttpResponse("Sup, i handled " + item.name)

    @classmethod
    def share(cls, item, request, permissions):
        user_name = request.POST.get('target')
        rel_path = '/' + item.rel_path
        try:
            share_with = models.User.objects.get(username=user_name)
        except models.User.DoesNotExist:
            pass
        else:
            sharing_note = models.Sharing.objects.get_or_create(owner=item.owner, item=rel_path, shared_with=share_with)
            sharing_note.permissions = 1
            sharing_note.save()
        finally:
            redirect_username = item.parent.owner.username
            redirect_rel_path = item.parent.rel_path
            return redirect(views.item_handler, user_name=redirect_username, relative_path=redirect_rel_path)


# editor for directories
class DirectoryEditor(Editor):
    def __init__(self):
        super(DirectoryEditor, self).__init__()
        self.name = "directory"
        self.extensions = [""]
        self.thumbnail = "blocks/thumbnails/dir.html"

    def can_handle(self, item):
        if item.is_dir:
            return True
        else:
            return False

    @classmethod
    def show(cls, item, request, permissions):
        item_rep = item_reps.DirectoryRepresentation(item)
        child_list = item.children
        child_files = []
        child_dirs = []
        for child in child_list:
            if child.is_dir:
                child_dirs.append(item_reps.DirectoryRepresentation(child))
            else:
                child_files.append(item_reps.FileRepresentation(child))
        context = Context({'item_rep': item_rep, 'child_dirs': child_dirs, 'child_files': child_files, })
        return render(request, "dir.html", context)

    @classmethod
    def download(cls, item, request, permissions):
        data = item.make_zip()
        response = HttpResponse(data, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="%s"' % (item.name + '.zip')
        return response

    @classmethod
    def upload(cls, item, request, permissions):
        if request.method == 'POST' and 'file' in request.FILES:
            uploaded_file = request.FILES['file']
            new_rel_path = item.rel_path + "/" + uploaded_file.name
            new_item = items.FileItem(item.owner, new_rel_path)
            new_item.write_file(uploaded_file.chunks())
            redirect_username = item.parent.owner.username
            redirect_rel_path = item.parent.rel_path
        return redirect(views.item_handler, user_name=redirect_username, relative_path=redirect_rel_path)

    @classmethod
    def create_new(cls, item, request, permissions):
        if request.POST.get('name', None) is not None:
            new_rel_path = item.rel_path + "/" + uploaded_file.name
            new_item = items.FileItem(item.owner, new_rel_path)
            new_item.init_file()
            redirect_username = item.parent.owner.username
            redirect_rel_path = item.parent.rel_path
        return redirect(views.item_handler, user_name=redirect_username, relative_path=redirect_rel_path)


# common editor for files
class FileEditor(Editor):
    def __init__(self):
        super(FileEditor, self).__init__()
        self.name = "file"
        self.extensions = [".txt", ".hex", ".bin", ".ini"]
        self.thumbnail = "blocks/thumbnails/file.html"

    def can_handle(self, item):
        extension = item.extension.lower()
        if extension in self.extensions and not item.is_dir:
            return True
        else:
            return False

    @classmethod
    def raw(cls, item, request, permissions):
        data = item.read_byte()
        return HttpResponse(data, content_type=item.mime)

    @classmethod
    def download(cls, item, request, permissions):
        content = item.read_byte()
        response = HttpResponse(content, content_type='application/force-download')
        response['Content-Disposition'] = 'attachment; filename=' + item.name
        response['X-Sendfile'] = item.name
        return response

    @classmethod
    def rename(cls, item, request, permissions):
        new_name = request.POST.get('name', item.name)
        item.rename(new_name)
        redirect_username = item.parent.owner.username
        redirect_rel_path = item.parent.rel_path
        return redirect(views.item_handler, user_name=redirect_username, relative_path=redirect_rel_path)

    @classmethod
    def remove(cls, item, request, permissions):
        item.delete()
        redirect_username = item.parent.owner.username
        redirect_rel_path = item.parent.rel_path
        return redirect(views.item_handler, user_name=redirect_username, relative_path=redirect_rel_path)


class UniversalFileEditor(FileEditor):
    def __init__(self):
        super(UniversalFileEditor, self).__init__()
        self.name = "universal"

    def can_handle(self, item):
        if not item.is_dir:
            return True
        else:
            return False

    @classmethod
    def show(cls, item, request, permissions):
        item_rep = item_reps.FileRepresentation(item)
        context = Context({'item_rep': item_rep})
        return render(request, "files/default.html", context)


class CodeEditor(FileEditor):
    def __init__(self):
        super(CodeEditor, self).__init__()
        self.name = "code"
        self.extensions = [".txt", ".hex", ".bin", ".ini", ""]

    @classmethod
    def show(cls, item, request, permissions):
        item_rep = item_reps.FileRepresentation(item)
        context = Context({'item_rep': item_rep})
        return render(request, "files/code.html", context)


class MarkdownEditor(FileEditor):
    def __init__(self):
        super(MarkdownEditor, self).__init__()
        self.name = "markdown"
        self.extensions = [".markdown", ".md"]

    @classmethod
    def show(cls, item, request, permissions):
        item_rep = item_reps.FileRepresentation(item)
        context = Context({'item_rep': item_rep})
        return render(request, "files/md.html", context)


class ImageEditor(FileEditor):
    def __init__(self):
        super(ImageEditor, self).__init__()
        self.name = "image"
        self.extensions = [".jpg", ".bmp", ".gif", ".png"]
        self.thumbnail = "blocks/thumbnails/image.html"

    @classmethod
    def show(cls, item, request, permissions):
        item_rep = item_reps.FileRepresentation(item)
        context = Context({'item_rep': item_rep})
        return render(request, "files/image.html", context)


class AudioEditor(FileEditor):
    def __init__(self):
        super(AudioEditor, self).__init__()
        self.name = "audio"
        self.extensions = [".mp3", ".wav", ".m3u", ".ogg"]
        self.thumbnail = "blocks/thumbnails/file.html"

    @classmethod
    def show(cls, item, request, permissions):
        item_rep = item_reps.FileRepresentation(item)
        context = Context({'item_rep': item_rep})
        return render(request, "files/audio.html", context)


class VideoEditor(FileEditor):
    def __init__(self):
        super(VideoEditor, self).__init__()
        self.name = "video"
        self.extensions = [".mp4", ".avi", ".mov", ".webm"]
        self.thumbnail = "blocks/thumbnails/file.html"

    @classmethod
    def show(cls, item, request, permissions):
        item_rep = item_reps.FileRepresentation(item)
        context = Context({'item_rep': item_rep})
        return render(request, "files/video.html", context)


class OnlyOfficeEditor(FileEditor):
    def __init__(self):
        super(OnlyOfficeEditor, self).__init__()
        self.name = "office"
        self.extensions = OnlyOfficeEditor.get_all_extensions()
        self.thumbnail = "blocks/thumbnails/file.html"

    @classmethod
    def show(cls, item, request, permissions):
        now = datetime.datetime.now()
        curr_date = str(now.day) + "." + str(now.month) + "." + str(now.year)
        api_src = settings.ONLYOFFICE_SERV_API_URL
        item_rep = item_reps.FileRepresentation(item)
        last_breadcrumb = len(item_rep.breadcrumbs) - 1
        item_url = item_rep.url
        parent_url = item_rep.breadcrumbs[last_breadcrumb].url
        client_ip = request.META['REMOTE_ADDR']
        doc_editor_key = OnlyOfficeEditor.get_doc_editor_key(client_ip, item_rep.name)
        doc_type = OnlyOfficeEditor.get_document_type(item)
        ext = item_rep.item.extension.lstrip(".")
        context = Context({'item_rep': item_rep, 'api_src': api_src,
                           'doc_type': doc_type, 'doc_editor_key': doc_editor_key,
                           'client_ip': client_ip, 'parent_url': parent_url,
                           'curr_date': curr_date, 'ext': ext, 'item_url': item_url})
        return render(request, "files/office.html", context)

    @classmethod
    def get_document_type(cls, item):
        ext = "." + item.extension
        if item.extension in settings.EXTS_DOCUMENT:
            return "text"
        elif item.extension in settings.EXTS_SPREADSHEET:
            return "spreadsheet"
        elif item.extension in settings.EXTS_PRESENTATION:
            return "presentation"
        else:
            return ""

    @classmethod
    def get_all_extensions(cls):
        extensions = []
        extensions.extend(settings.EXTS_DOCUMENT)
        extensions.extend(settings.EXTS_SPREADSHEET)
        extensions.extend(settings.EXTS_PRESENTATION)
        return extensions

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


class PdfEditor(FileEditor):
    def __init__(self):
        super(PdfEditor, self).__init__()
        self.name = "pdf"
        self.extensions = [".pdf"]
        self.thumbnail = "blocks/thumbnails/file.html"

    @classmethod
    def show(cls, item, request, permissions):
        item_rep = item_reps.FileRepresentation(item)
        context = Context({'item_rep': item_rep})
        return render(request, "files/pdf.html", context)