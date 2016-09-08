import os


# abstract item - file or directory
class Item:
    def __init__(self, path, user, url):
        if not os.path.exists(path):
            raise FileNotFoundError
        self.extension = os.path.splitext(path)[1]
        self.absolute_path = path
        self.parent_path = os.path.dirname(path)
        self.name = os.path.basename(path)
        if self.name == "":
            self.name = os.path.basename(self.parent_path)
            self.parent_path = os.path.dirname(self.parent_path)
        if os.path.isdir(self.absolute_path):
            self.thumbnail_template = "blocks/thumbnails/dir.html"
            self.is_dir = True
        else:
            self.thumbnail_template = "blocks/thumbnails/file.html"
            self.is_dir = False
        self.owner = user
        self.url_path = url.rstrip('/')
        if self.url_path.lstrip('/') == user.username:
            self.is_root = True
        else:
            self.is_root = False
        parent_url_length = self.url_path.rfind('/')
        self.parent_url = self.url_path[:parent_url_length]
        pass

    def __str__(self):
        return self.name  # lol

    def get_parent(self):
        parent_item = Item(self.parent_path, self.owner, self.parent_url)
        return parent_item
