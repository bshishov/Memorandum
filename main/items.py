import os


# abstract item - file or directory
class Item:
    def __init__(self, path, user, url):
        if not os.path.exists(path):
            raise FileNotFoundError
        parts = os.path.split(path)
        self.extension = os.path.splitext(path)[1]
        path_without_name = parts[0]
        self.name = parts[1]
        if self.name == "":
            self.name = os.path.split(path_without_name)[1]
        self.absolute_path = path
        self.url_path = url.rstrip('/')
        self.owner = user
        self.is_root = False
        self.thumbnail_template = "blocks/thumbnails/dir.html"

    def __str__(self):
        return self.name  # lol

    def is_dir(self):
        return os.path.isdir(self.absolute_path)
