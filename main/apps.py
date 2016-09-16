from django.apps import AppConfig
from . import editors


class MainConfig(AppConfig):
    name = 'main'


# array of editors for different types of items
EDITORS = [editors.CodeEditor(),
           editors.MarkdownEditor(),
           editors.DirectoryEditor(),
           editors.FileEditor(),
           editors.UniversalEditor()]
