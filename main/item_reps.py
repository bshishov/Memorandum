from django.urls import reverse
from . import editors
from . import items
from .models import Sharing, SharedLink
import os


def get_representation(item):
    if os.path.isdir(item.absolute_path):
        return DirectoryRepresentation(item)
    else:
        return FileRepresentation(item)


class Representation:
    def __init__(self, item, editor=None):
        """
        :type item: items.Item
        :type editor: editors.Editor
        """
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
        return self.item.factory.get_url(self.item.rel_path)

    @property
    def breadcrumbs(self):
        item_breadcrumbs = []
        for parent in self.item.parents:
            parent_rep = Representation(parent)
            item_breadcrumbs.append(parent_rep)
        return item_breadcrumbs

    @property
    def sharings(self):
        item_sharings = Sharing.objects.filter(owner=self.item.owner, item=self.item.rel_path)
        return item_sharings

    @property
    def shared_links(self):
        links = SharedLink.objects.filter(owner=self.item.owner, item=self.item.rel_path)
        return links


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
