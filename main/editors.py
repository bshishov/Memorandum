from django.shortcuts import render, redirect
from django.template import Context, loader, RequestContext
from django.http import HttpResponse
from . import items
from . import views
from . import item_reps
import os
import shutil
import tempfile


# abstract editor
class Editor:
    def __init__(self):
        self.name = "editor"
        # list of extensions that can be handle
        self.extensions = []
        self.thumbnail = "blocks/thumbnails/file.html"

    # raise exception if editor can not handle this item
    def can_handle(self, item):
        if item.extension in self.extensions:
            return True
        else:
            return False

    # returns if needed action was not found
    def not_exists(self):
        return HttpResponse("No such action")

    @classmethod
    def show(cls, item, request, permissions):
        return HttpResponse("Sup, i handled " + item.name)


# universal editor - can handle all items
class UniversalEditor(Editor):
    def __init__(self):
        super(UniversalEditor, self).__init__()
        self.name = "universal"

    # never raise exception
    def can_handle(self, item):
        return True

    @classmethod
    def show(cls, item, request, permissions):
        return HttpResponse("item " + item.name + " with extension "
                            + item.extension + " handled whith universal editor")


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
        item_rep = item_reps.DirRep(item)
        child_list = item.children
        child_files = []
        child_dirs = []
        for child in child_list:
            if child.is_dir:
                child_dirs.append(item_reps.DirRep(child))
            else:
                child_files.append(item_reps.FileRep(child))
        context = Context({'item': item_rep, 'child_dirs': child_dirs, 'child_files': child_files, })
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


# common editor for files
class FileEditor(Editor):
    def __init__(self):
        super(FileEditor, self).__init__()
        self.name = "file"
        self.extensions = [".txt", ".hex", ".bin", ".ini"]
        self.thumbnail = "blocks/thumbnails/file.html"

    def can_handle(self, item):
        if item.extension in self.extensions and not item.is_dir:
            return True
        else:
            return False

    @classmethod
    def raw(cls, item, request, permissions):
        data = item.read_byte()
        return HttpResponse(data)

    @classmethod
    def download(cls, item, request, permissions):
        content = item.read_byte()
        response = HttpResponse(content, content_type='application/force-download')
        response['Content-Disposition'] = 'attachment; filename=' + item.name
        response['X-Sendfile'] = item.name
        return response

    @classmethod
    def rename(cls, item, request, permissions):
        new_name = request.GET.get('name', item.name)
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


class CodeEditor(FileEditor):
    def __init__(self):
        super(CodeEditor, self).__init__()
        self.name = "code"
        self.extensions = [".txt", ".hex", ".bin", ".ini", ""]

    @classmethod
    def show(cls, item, request, permissions):
        item_rep = item_reps.FileRep(item)
        context = Context({'item': item_rep})
        return render(request, "files/code.html", context)


class MarkdownEditor(FileEditor):
    def __init__(self):
        super(MarkdownEditor, self).__init__()
        self.name = "markdown"
        self.extensions = [".markdown", ".md"]

    @classmethod
    def show(cls, item, request, permissions):
        item_rep = item_reps.FileRep(item)
        context = Context({'item': item_rep})
        return render(request, "files/md.html", context)


class ImageEditor(FileEditor):
    def __init__(self):
        super(ImageEditor, self).__init__()
        self.name = "image"
        self.extensions = [".jpg", ".bmp", ".gif", ".png"]
        self.thumbnail = "blocks/thumbnails/image.html"

    @classmethod
    def show(cls, item, request, permissions):
        item_rep = item_reps.FileRep(item)
        context = Context({'item': item_rep})
        return render(request, "files/image.html", context)
