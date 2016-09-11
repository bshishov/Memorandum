import os
from . import models


# abstract item - file or directory
class Item:
    def __init__(self, user, url):
        self.rel_path = url.rstrip("/")
        self.rel_path = self.rel_path.lstrip("/")
        home_dir = models.HomeDirectory.objects.get(uid=user).home_dir
        self.absolute_path = os.path.join(home_dir, self.rel_path)
        if not os.path.exists(self.absolute_path):
            raise FileNotFoundError
        self.owner = user
        self.extension = os.path.splitext(self.absolute_path)[1]
        self.parent_path = os.path.dirname(self.absolute_path)
        self.name = os.path.basename(self.absolute_path)
        if self.name == "":
            self.name = os.path.basename(self.parent_path)
            self.parent_path = os.path.dirname(self.parent_path)
        if os.path.isdir(self.absolute_path):
            self.thumbnail_template = "blocks/thumbnails/dir.html"
            self.is_dir = True
        else:
            self.thumbnail_template = "blocks/thumbnails/file.html"
            self.is_dir = False
        if self.rel_path == "" or self.rel_path == "/":
            self.is_root = True
        else:
            self.is_root = False
        parent_url_length = self.rel_path.rfind('/')
        if parent_url_length != -1:
            self.parent_url = self.rel_path[:parent_url_length]
        else:
            self.parent_url = ""
        pass

    def __str__(self):
        return self.name  # lol

    @property
    def parent(self):
        parent_item = Item(self.owner, self.parent_url)
        return parent_item

    @property
    def children(self):
        child_list = os.listdir(self.absolute_path)
        child_items = []
        for child in child_list:
            child_url = self.rel_path + "/" + child
            child_item = Item(self.owner, child_url)
            child_items.append(child_item)
        return child_items

    @property
    def url(self):
        full_url = self.owner.username + "/" + self.rel_path
        full_url = full_url.rstrip("/")
        return full_url

    @property
    def breadcrumbs(self):
        breadcrumbs = []
        breadcrumb = self
        while not breadcrumb.is_root:
            breadcrumb = breadcrumb.parent
            breadcrumbs.append(breadcrumb)
        breadcrumbs.reverse()
        return breadcrumbs
