from django.apps import AppConfig
from . import editors
from memorandum import settings


class MainConfig(AppConfig):
    name = 'main'


DEFAULT_EDITORS = [
    'CodeEditor',
    'MarkdownEditor',
    'DirectoryEditor',
    'ImageEditor',
    'FileEditor',
    'UniversalEditor'
]

if hasattr(settings, 'EDITORS') and len(settings.EDITORS) > 0:
    editors_list = settings.EDITORS
else:
    editors_list = DEFAULT_EDITORS
EDITORS = []
for editor_name in editors_list:
    editor_constructor = getattr(editors, editor_name)
    editor = editor_constructor()
    EDITORS.append(editor)
