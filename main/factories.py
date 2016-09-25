from . import models
from . import items
from . import item_reps
from . import editors
from memorandum import settings
import os


class ItemFactory:
    @classmethod
    def get_instance(cls, user, relative_path):
        rel_path = relative_path.rstrip("/")
        rel_path = rel_path.lstrip("/")
        home_dir = models.HomeDirectory.objects.get(uid=user).home_dir
        absolute_path = os.path.join(home_dir, rel_path)
        if not os.path.exists(absolute_path):
            raise FileNotFoundError
        elif os.path.isdir(absolute_path):
            return items.DirectoryItem(user, relative_path)
        else:
            return items.FileItem(user, relative_path)


class RepresentationFactory:
    @classmethod
    def get_representation(cls, item):
        if os.path.isdir(item.absolute_path):
            return item_reps.DirectoryRepresentation(item)
        else:
            return item_reps.FileRepresentation(item)


class EditorsFactory:
    @classmethod
    def get_editor(cls, name):
        all_editors = EditorsFactory.get_all_editors()
        for possibleEditor in all_editors:
            if possibleEditor.name == name:
                editor = possibleEditor
                break
        # check if the editor is suitable for this extension
        # (if not, LookupException will be raised)
        if not editor.can_handle(current_item):
            raise LookupError
        else:
            return editor

    @classmethod
    def get_all_editors(cls):
        default_editors = [
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
            editors_list = default_editors
        all_editors = []
        for editor_name in editors_list:
            editor_constructor = getattr(editors, editor_name)
            editor = editor_constructor()
            all_editors.append(editor)
        return all_editors

    @classmethod
    def get_default_for(cls, item):
        all_editors = EditorsFactory.get_all_editors()
        for possibleEditor in all_editors:
            if possibleEditor.can_handle(item):
                default_editor = possibleEditor
                break
        return default_editor
