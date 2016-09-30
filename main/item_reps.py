from django.urls import reverse
from memorandum import settings
from . import editors


def get_representation(item):
    if os.path.isdir(item.absolute_path):
        return item_reps.DirectoryRepresentation(item)
    else:
        return item_reps.FileRepresentation(item)


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
            return editor.thumbnail

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


class FileRepresentation(Representation):
    def __init__(self, item):
        super(FileRepresentation, self).__init__(item)
        self.mime = settings.MIME_TYPES.get(self.item.extension, 'application/x-binary')


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
