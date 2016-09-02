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


# test editor, that only shows text file content
class TextEditor(Editor):
    def __init__(self):
        super(TextEditor, self).__init__()
        self.name = "text"
        self.extensions = [".txt", ".hex", ".bin", ".ini"]

    @staticmethod
    def show(item, request, permissions):
        f = open(item.absolutePath, 'r')
        content = f.read()
        f.close()
        template = loader.get_template("text_file.html")
        context = Context({'content': content})
        return HttpResponse(template.render(context))


# test editor for directories
class DirectoryEditor(Editor):
    def __init__(self):
        super(DirectoryEditor, self).__init__()
        self.name = "directory"
        self.extensions = [""]

    @staticmethod
    def show(item, request, permissions):
        child_list = os.listdir(item.absolutePath)
        child_items = []
        for child in child_list:
            absolute_path = os.path.join(item.absolutePath, child)
            url_path = item.urlPath + "/" + child
            child_items.append(items.Item(absolute_path, item.owner, url_path))
        host = request.get_host()
        template = loader.get_template("directory.html")
        context = Context({'childItems': child_items, 'host': host})
        return HttpResponse(template.render(context))