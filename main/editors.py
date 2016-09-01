#from django.shortcuts import render
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
    def canHandle(self, item):
        if item.extension in self.extensions:
            return True
        else:
            return False

    # returns if needed action was not found
    def notExists(self):
        return HttpResponse("No such action")

    @staticmethod
    def show(item, request):
        return HttpResponse("Sup, i handled " + item.name)


# universal editor - can handle all items
class UniversalEditor(Editor):
    def __init__(self):
        super(UniversalEditor, self).__init__()
        self.name = "universal"

    # never raise exception
    def canHandle(self, item):
        return True

    @staticmethod
    def show(item, request):
        return HttpResponse("item " + item.name + " with extension " + item.extension + " handled whith universal editor")


# test editor, that only shows text file content
class TextEditor(Editor):
    def __init__(self):
        super(TextEditor, self).__init__()
        self.name = "text"
        self.extensions = [".txt", ".hex", ".bin", ".ini"]

    @staticmethod
    def show(item, request):
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
    def show(item, request):
        childList = os.listdir(item.absolutePath)
        childItems = []
        for child in childList:
            absolutePath = os.path.join(item.absolutePath, child)
            urlPath = item.urlPath + "/" + child
            childItems.append(items.Item(absolutePath, item.owner, urlPath))
        host = request.get_host()
        template = loader.get_template("directory.html")
        context = Context({'childItems': childItems, 'host': host})
        return HttpResponse(template.render(context))
