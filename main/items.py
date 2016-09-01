import os


# abstract item - file or directory
class Item:
    def __init__(self, path, user, url):
        if not os.path.exists(path):
            raise FileNotFoundError
        parts = os.path.split(path)
        self.extension = os.path.splitext(path)[1]
        pathWithoutName = parts[0]
        self.name = parts[1]
        if self.name == "":
            self.name = os.path.split(pathWithoutName)[1]
        self.absolutePath = path
        self.urlPath = url
        self.urlPath = self.urlPath.rstrip('/')
        self.owner = user

    def __str__(self):
        return self.name  # lol
