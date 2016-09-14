from django.shortcuts import render, redirect
from django.template import Context, loader, RequestContext
from django.http import HttpResponse
from . import items
import os


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

    @staticmethod
    def show(item, request, permissions):
        return HttpResponse("Sup, i handled " + item.name)


# universal editor - can handle all items
class UniversalEditor(Editor):
    def __init__(self):
        super(UniversalEditor, self).__init__()
        self.name = "universal"

    # never raise exception
    def can_handle(self, item):
        return True

    @staticmethod
    def show(item, request, permissions):
        return HttpResponse("item " + item.name + " with extension " + item.extension + " handled whith universal editor")


# editor for directories
class DirectoryEditor(Editor):
    def __init__(self):
        super(DirectoryEditor, self).__init__()
        self.name = "directory"
        self.extensions = [""]

    @staticmethod
    def show(item, request, permissions):
        child_list = item.children
        child_files = []
        child_dirs = []
        for child in child_list:
            if child.is_dir:
                child_dirs.append(child)
            else:
                child_files.append(child)
        template = loader.get_template("dir.html")
        context = Context({'item': item, 'child_dirs': child_dirs, 'child_files': child_files, })
        return HttpResponse(template.render(context))

    @staticmethod
    def download(item, request, permissions):
        return HttpResponse("lol")

    @staticmethod
    def upload(item, request, permissions):
        return HttpResponse("lol")


# common editor for files
class FileEditor(Editor):
    def __init__(self):
        super(FileEditor, self).__init__()
        self.name = "file"
        self.extensions = [".txt", ".hex", ".bin", ".ini"]

    @staticmethod
    def raw(item, request, permissions):
        f = open(item.absolute_path, 'r')
        content = f.read()
        f.close()
        template = loader.get_template("text_file.html")
        context = Context({'content': content})
        return HttpResponse(template.render(context))

    @staticmethod
    def download(item, request, permissions):
        f = open(item.absolute_path, 'r')
        content = f.read()
        f.close()
        response = HttpResponse(content, content_type='application/force-download')
        response['Content-Disposition'] = 'attachment; filename=' + item.name
        response['X-Sendfile'] = item.name
        return response

    @staticmethod
    def rename(item, request, permissions):
        new_name = request.GET.get('name', item.name)
        new_path = os.path.join(item.parent_path, new_name)
        os.rename(item.absolute_path, new_path)
        return redirect("/" + item.parent.url)

    @staticmethod
    def remove(item, request, permissions):
        os.remove(item.absolute_path)
        return redirect("/" + item.parent.url)


# test editor, that only shows text file content
class TextEditor(FileEditor):
    def __init__(self):
        super(TextEditor, self).__init__()
        self.name = "text"
        self.extensions = [".txt", ".hex", ".bin", ".ini"]

    @staticmethod
    def show(item, request, permissions):
        f = open(item.absolute_path, 'r')
        content = f.read()
        f.close()
        template = loader.get_template("text_file.html")
        context = Context({'content': content})
        return HttpResponse(template.render(context))
