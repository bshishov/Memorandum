import os
import time
import shutil
import tempfile
from . import models
import mimetypes

mimetypes.init()


def get_instance(user, relative_path):
    rel_path = relative_path.rstrip("/")
    rel_path = rel_path.lstrip("/")
    absolute_path = os.path.join(user.home_dir, rel_path)
    access_ok = os.access(absolute_path, os.F_OK | os.R_OK)
    if not access_ok:
        return None
    elif os.path.isdir(absolute_path):
        return DirectoryItem(user, relative_path)
    else:
        return FileItem(user, relative_path)


def get_instance_by_type(item_type, item_path, user, relative_path):
    access_ok = os.access(item_path, os.F_OK | os.R_OK)
    if not access_ok:
        return None
    elif item_type == "directory":
        return DirectoryItem(user, relative_path)
    else:
        return FileItem(user, relative_path)


# abstract item - file or directory
class Item:
    def __init__(self, user, path):
        self.rel_path = path.rstrip("/")
        self.rel_path = self.rel_path.lstrip("/")
        self.absolute_path = os.path.join(user.home_dir, self.rel_path)
        self.owner = user
        self.extension = os.path.splitext(self.absolute_path)[1]
        self.parent_path = os.path.dirname(self.absolute_path)
        self.name = os.path.basename(self.absolute_path)
        if self.name == "":
            self.name = os.path.basename(self.parent_path)
            self.parent_path = os.path.dirname(self.parent_path)
        parent_rel_path_length = self.rel_path.rfind('/')
        if parent_rel_path_length != -1:
            self.parent_rel_path = self.rel_path[:parent_rel_path_length]
        else:
            self.parent_rel_path = ""
        self.is_deleted = False
        if os.path.exists(self.absolute_path):
            self.time_modified = os.path.getmtime(self.absolute_path)

        mime_type = mimetypes.guess_type(self.name)[0]
        if mime_type is None:
            self.mime = 'application/octet-stream'
        else:
            self.mime = mime_type

    def __str__(self):
        return self.name

    @property
    def parent(self):
        parent_item = get_instance(self.owner, self.parent_rel_path)
        return parent_item

    @property
    def size(self):
        return os.path.getsize(self.absolute_path)

    @property
    def parents(self):
        parent_list = []
        current_item = self
        while not current_item.is_root:
            current_item = current_item.parent
            parent_list.append(current_item)
        parent_list.reverse()
        return parent_list

    @property
    def is_dir(self):
        return os.path.isdir(self.absolute_path)

    @property
    def is_root(self):
        if self.rel_path == "" or self.rel_path == "/":
            return True
        else:
            return False

    @property
    def created(self):
        return time.ctime(os.path.getctime(self.absolute_path))

    @property
    def modified(self):
        return time.ctime(os.path.getmtime(self.absolute_path))

    def rename(self, name):
        new_path = os.path.join(self.parent_path, name)
        os.rename(self.absolute_path, new_path)
        self.name = name

    def delete(self):
        os.remove(self.absolute_path)
        self.is_deleted = True


class FileItem(Item):
    def __init__(self, user, path):
        super(FileItem, self).__init__(user, path)

    def read_byte(self):
        f = open(self.absolute_path, 'rb')
        content = f.read()
        f.close()
        return content

    def write_file(self, chunks):
        f = open(self.absolute_path, 'wb+')
        for chunk in chunks:
            f.write(chunk)
        f.close()

    def create_empty(self):
        f = open(self.absolute_path, 'w')
        f.close()


class DirectoryItem(Item):
    def __init__(self, user, path):
        super(DirectoryItem, self).__init__(user, path)

    @property
    def children(self):
        try:
            child_list = os.listdir(self.absolute_path)
        except PermissionError:
            return []
        else:
            child_items = []
            for child in child_list:
                try:
                    child_url = self.rel_path + "/" + child
                    child_item = get_instance(self.owner, child_url)
                    if child_item is not None:
                        child_items.append(child_item)
                except:
                    pass
            return child_items

    def make_zip(self):
        temp_dir = tempfile.mkdtemp()
        archive = os.path.join(temp_dir, self.name)
        root_dir = self.absolute_path
        data = open(shutil.make_archive(archive, 'zip', root_dir), 'rb').read()
        shutil.rmtree(temp_dir)
        return data

    def has_file(self, name):
        file_path = os.path.join(self.absolute_path, name)
        return os.path.exists(file_path)

    def make_path_to_new_item(self, name):
        file_name = name
        attempts = 1
        ext_beginning = name.rfind(".")
        if ext_beginning == -1:
            ext_beginning = len(file_name)
        while self.has_file(file_name):
            file_name = name[:ext_beginning] + "(" + str(attempts) + ")" + name[ext_beginning:]
            attempts += 1
        path = os.path.join(self.rel_path, file_name)
        return path

    def create_empty(self):
        if not os.path.exists(self.absolute_path):
            os.makedirs(self.absolute_path)
