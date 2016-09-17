from django.shortcuts import render, redirect
from django.template import Context, loader, RequestContext
from django.http import HttpResponse
from . import items
import os
import shutil
import tempfile


# abstract editor
class Editor:
    def __init__(self):
        self.name = "editor"
        # list of extensions that can be handle
        self.extensions = []

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
        return HttpResponse("item " + item.name + " with extension " + item.extension + " handled whith universal editor")


# editor for directories
class DirectoryEditor(Editor):
    def __init__(self):
        super(DirectoryEditor, self).__init__()
        self.name = "directory"
        self.extensions = [""]

    def can_handle(self, item):
        if item.is_dir:
            return True
        else:
            return False

    @classmethod
    def show(cls, item, request, permissions):
        child_list = item.children
        child_files = []
        child_dirs = []
        for child in child_list:
            if child.is_dir:
                child_dirs.append(child)
            else:
                child_files.append(child)
        context = Context({'item': item, 'child_dirs': child_dirs, 'child_files': child_files, })
        return render(request, "dir.html", context)

    @classmethod
    def download(cls, item, request, permissions):
        temp_dir = tempfile.mkdtemp()
        archive = os.path.join(temp_dir, item.name)
        root_dir = item.absolute_path
        data = open(shutil.make_archive(archive, 'zip', root_dir), 'rb').read()
        shutil.rmtree(temp_dir)
        response = HttpResponse(data, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="%s"' % (item.name + '.zip')
        return response

    @classmethod
    def upload(cls, item, request, permissions):
        return HttpResponse("lol")


# common editor for files
class FileEditor(Editor):
    def __init__(self):
        super(FileEditor, self).__init__()
        self.name = "file"
        self.extensions = [".txt", ".hex", ".bin", ".ini"]

    def can_handle(self, item):
        if item.extension in self.extensions and not item.is_dir:
            return True
        else:
            return False

    @classmethod
    def raw(cls, item, request, permissions):
        f = open(item.absolute_path, 'r')
        content = f.read()
        f.close()
        return HttpResponse(content)

    @classmethod
    def download(cls, item, request, permissions):
        f = open(item.absolute_path, 'r')
        content = f.read()
        f.close()
        response = HttpResponse(content, content_type='application/force-download')
        response['Content-Disposition'] = 'attachment; filename=' + item.name
        response['X-Sendfile'] = item.name
        return response

    @classmethod
    def rename(cls, item, request, permissions):
        new_name = request.GET.get('name', item.name)
        new_path = os.path.join(item.parent_path, new_name)
        os.rename(item.absolute_path, new_path)
        return redirect("item_handler", user_name=item.parent.owner.username, relative_path=item.parent.rel_path)

    @classmethod
    def remove(cls, item, request, permissions):
        os.remove(item.absolute_path)
        return redirect("item_handler", user_name=item.parent.owner.username, relative_path=item.parent.rel_path)


# test editor, that only shows text file content
class CodeEditor(FileEditor):
    def __init__(self):
        super(CodeEditor, self).__init__()
        self.name = "code"
        self.extensions = [".txt", ".hex", ".bin", ".ini", ""]

    @classmethod
    def show(cls, item, request, permissions):
        context = Context({'item': item})
        return render(request, "files/code.html", context)


class MarkdownEditor(FileEditor):
    def __init__(self):
        super(MarkdownEditor, self).__init__()
        self.name = "code"
        self.extensions = [".markdown", ".md"]

    @classmethod
    def show(cls, item, request, permissions):
        context = Context({'item': item})
        return render(request, "files/md.html", context)