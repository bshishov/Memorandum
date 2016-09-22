from django.urls import reverse
from . import models
from . import apps


class Representation:
    def __init__(self, item):
        self.name = item.name
        self.item = item
        self.thumbnail = self.default_editor.thumbnail

    @property
    def default_editor(self):
        for possibleEditor in apps.EDITORS:
            if possibleEditor.can_handle(self.item):
                editor = possibleEditor
                break
        return editor

    @property
    def url(self):
        full_url = reverse('item_handler', kwargs={'user_name': self.item.owner.username,
                                                   'relative_path': self.item.rel_path})
        return full_url

    @property
    def breadcrumbs(self):
        item_breadcrumbs = []
        for parent in self.item.parents:
            parent_rep = Representation(parent)
            item_breadcrumbs.append(parent_rep)
        return item_breadcrumbs


class FileRep(Representation):
    def __init__(self, item):
        super(FileRep, self).__init__(item)
        self.mime = apps.MIMES.get(self.item.extension, 'application/x-binary')


class DirRep(Representation):
    def __init__(self, item):
        super(DirRep, self).__init__(item)
        self.children = item.children

    @property
    def content(self):
        dir_content = []
        for child in self.item.children:
            rep = Representation(child)
            dir_content.append(rep)
        return dir_content
