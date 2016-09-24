from . import models
from . import items
from . import item_reps
import os


class Factory:
    @classmethod
    def get_instance(cls, user, url):
        rel_path = url.rstrip("/")
        rel_path = rel_path.lstrip("/")
        home_dir = models.HomeDirectory.objects.get(uid=user).home_dir
        absolute_path = os.path.join(home_dir, rel_path)
        if not os.path.exists(absolute_path):
            raise FileNotFoundError
        elif os.path.isdir(absolute_path):
            return items.DirectoryItem(user, url)
        else:
            return items.FileItem(user, url)

    @classmethod
    def get_representation(cls, item):
        if os.path.isdir(item.absolute_path):
            return item_reps.DirRep(item)
        else:
            return item_reps.FileRep(item)


class RepresentationFactory:
    @classmethod
    def get_representation(cls, item):
        if os.path.isdir(item.absolute_path):
            return item_reps.DirRep(item)
        else:
            return item_reps.FileRep(item)