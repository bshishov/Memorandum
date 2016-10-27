from django.urls import reverse
from . import editors
import os


def get_representation(item):
    if os.path.isdir(item.absolute_path):
        return DirectoryRepresentation(item)
    else:
        return FileRepresentation(item)


class Representation:
    def __init__(self, item, editor=None):
        self.name = item.name
        self.item = item
        self.editor = editor

    @property
    def thumbnail(self):
        if self.editor is None:
            return editors.get_default_for(self.item).thumbnail
        else:
            return self.editor.thumbnail

    @property
    def url(self):
        full_url = reverse('item_handler', kwargs={'user_id': self.item.owner.id,
                                                   'relative_path': self.item.rel_path})
        return full_url

    @property
    def breadcrumbs(self):
        item_breadcrumbs = []
        for parent in self.item.parents:
            parent_rep = Representation(parent)
            item_breadcrumbs.append(parent_rep)
        return item_breadcrumbs


class FileRepresentation(Representation):
    def __init__(self, item):
        super(FileRepresentation, self).__init__(item)


class DirectoryRepresentation(Representation):
    def __init__(self, item):
        super(DirectoryRepresentation, self).__init__(item)
        self.children = item.children

    @property
    def content(self):
        dir_content = []
        for child in self.item.children:
            rep = Representation(child)
            dir_content.append(rep)
        return dir_content
