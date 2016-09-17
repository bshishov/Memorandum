from django.apps import AppConfig
from . import editors


class MainConfig(AppConfig):
    name = 'main'


# array of editors for different types of items
EDITORS = [editors.CodeEditor(),
<<<<<<< HEAD
=======
           editors.MarkdownEditor(),
>>>>>>> fb3dd5ca6a5bda697dc636d36f2fcd57a9105ede
           editors.DirectoryEditor(),
           editors.FileEditor(),
           editors.UniversalEditor()]
