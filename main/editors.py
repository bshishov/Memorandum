from django.http import HttpResponse
import os


# abstract editor
class Editor:
    def __init__(self):
        # list of extensions that can be handle
        self.extensions = []
        # list of extensions that this editor is default for
        self.defaultExtensions = []

    # raise exception if editor can not handle this item
    def canHandleProbe(self, item):
        if item.extension not in self.extensions:
            raise LookupError

    # return true if item extension is in defaultExtensions list
    def isDefaultFor(self, item):
        if item.extension in self.defaultExtensions:
            return True
        else:
            return False

    # returns if needed action was not found
    def notExists(self):
        return HttpResponse("No such action")

    @staticmethod
    def show(item):
        return HttpResponse("Sup, i handled " + item.name)


# universal editor - can handle all items
class UniversalEditor(Editor):
    def __init__(self):
        super(UniversalEditor, self).__init__()

    # never raise exception
    def canHandleProbe(self, item):
        pass

    # return true always
    def isDefaultFor(self, item):
            return True

    @staticmethod
    def show(item):
        return HttpResponse("item " + item.name + " with extension " + item.extension + " handled whith universal editor")


# test editor, that only shows text file content
class TextEditor(Editor):
    def __init__(self):

        self.extensions = ["txt", "hex", "bin", "ini"]
        self.defaultExtensions = ["txt"]

    @staticmethod
    def show(item):
        f = open(item.absolutePath, 'r')
        content = f.read()
        f.close()
        return HttpResponse("TEXT FILES HANDLER<br><br>" + content)


# test editor for directories
class DirectoryEditor(Editor):
    def __init__(self):
        Editor.__init__(self)
        self.extensions = [""]
        self.defaultExtensions = [""]

    @staticmethod
    def show(item):
        childList = os.listdir(item.absolutePath)
        contentString = ""
        for subItem in childList:
            contentString += subItem + "<br>"
        return HttpResponse("DIRECTORY HANDLER<br><br>" + contentString)
