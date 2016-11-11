import os
import time
import shutil
import tempfile
from . import models
import mimetypes
from django.urls import reverse

mimetypes.init()


class AbstractItemFactory(object):
    def absolute_path(self, relative_path):
        raise NotImplementedError

    def get_item(self, relative_path):
        raise NotImplementedError

    def new_file(self, relative_path):
        raise NotImplementedError

    def new_directory(self, relative_path):
        raise NotImplementedError

    def get_or_create_directory(self, relative_path):
        dir_item = self.get_item(relative_path)
        if dir_item is not None:
            return dir_item
        return self.new_directory(relative_path)

    def get_or_create_file(self, relative_path):
        file_item = self.get_item(relative_path)
        if file_item is not None:
            return file_item
        return self.new_file(relative_path)

    def get_url(self, relative_path):
        raise NotImplementedError

    def _get_item(self, user, relative_path):
        relative_path = self._clear_path(relative_path)

        absolute_path = self.absolute_path(relative_path)
        if not os.access(absolute_path, os.F_OK | os.R_OK):
                return None
        elif os.path.isdir(absolute_path):
            return DirectoryItem(self, user, relative_path)
        else:
            return FileItem(self, user, relative_path)

    def _new_file(self, user, relative_path):
        return FileItem(self, user, self._clear_path(relative_path))

    def _new_directory(self, user, relative_path):
        return DirectoryItem(self, user, self._clear_path(relative_path))

    def _clear_path(self, value):
        """
        :type value: str
        """
        return value.strip().strip('/')


class PlainItemFactory(AbstractItemFactory):
    def __init__(self, base_dir):
        """
        :type base_dir: str
        """
        super(PlainItemFactory, self).__init__()
        self.__base_dir = base_dir

    def absolute_path(self, relative_path):
        return os.path.join(self.__base_dir, relative_path)

    def get_item(self, relative_path):
        return AbstractItemFactory._get_item(self, None, relative_path)

    def new_file(self, relative_path):
        return AbstractItemFactory._new_file(self, None, relative_path)

    def new_directory(self, relative_path):
        return AbstractItemFactory._new_directory(self, None, relative_path)

    def get_url(self, relative_path):
        raise PermissionError


class UserItemFactory(AbstractItemFactory):
    def __init__(self, owner):
        """
        :type owner: models.CustomUser
        """
        super(UserItemFactory, self).__init__()
        self.__owner = owner

    def absolute_path(self, relative_path):
        return os.path.join(self.__owner.home_dir, relative_path)

    def get_item(self, relative_path):
        return AbstractItemFactory._get_item(self, self.__owner, relative_path)

    def new_file(self, relative_path):
        return AbstractItemFactory._new_file(self, self.__owner, relative_path)

    def new_directory(self, relative_path):
        return AbstractItemFactory._new_directory(self, self.__owner, relative_path)

    def get_url(self, relative_path):
        return reverse('item_handler', kwargs={'user_id': self.__owner.id,
                                               'relative_path': relative_path})


class SharedLinkItemFactory(AbstractItemFactory):
    def __init__(self, shared_link):
        """
        :type shared_link: models.SharedLink
        """
        super(SharedLinkItemFactory, self).__init__()
        assert(isinstance(shared_link, models.SharedLink))
        self.__link = shared_link

    def absolute_path(self, relative_path):
        return os.path.join(self.__link.owner.home_dir, self.__link.item, relative_path)

    def get_item(self, relative_path):
        return AbstractItemFactory._get_item(self, self.__link.owner, relative_path)

    def new_file(self, relative_path):
        return AbstractItemFactory._new_file(self, self.__link.owner, relative_path)

    def new_directory(self, relative_path):
        return AbstractItemFactory._new_directory(self, self.__link.owner, relative_path)

    def get_url(self, relative_path):
        return reverse('link_handler', kwargs={'link_id': self.__link.link_id,
                                               'relative_path': relative_path})

    @property
    def link(self):
        return self.__link


class SharedItemItemFactory(AbstractItemFactory):
    def __init__(self, sharing):
        """
        :type sharing: models.Sharing
        """
        super(SharedItemItemFactory, self).__init__()
        assert(isinstance(sharing, models.Sharing))
        self.__sharing = sharing

    def absolute_path(self, relative_path):
        return os.path.join(self.__sharing.owner, self.__sharing.item, relative_path)

    def get_item(self, relative_path):
        return AbstractItemFactory._get_item(self, self.__sharing.owner, relative_path)

    def new_file(self, relative_path):
        return AbstractItemFactory._new_file(self, self.__sharing.owner, relative_path)

    def new_directory(self, relative_path):
        return AbstractItemFactory._new_directory(self, self.__sharing.owner, relative_path)

    def get_url(self, relative_path):
        return reverse('item_handler', kwargs={'user_id': self.__sharing.owner.id,
                                               'relative_path': relative_path})


# abstract item - file or directory
class Item:
    def __init__(self, path_factory, owner, relative_path):
        """
        :type path_factory: AbstractItemFactory
        :type owner: CustomUser
        :type relative_path: str
        """
        self.factory = path_factory
        self.rel_path = relative_path
        self.absolute_path = self.factory.absolute_path(relative_path)
        self.owner = owner
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
    def exists(self):
        return os.path.exists(self.absolute_path)

    @property
    def parent(self):
        return self.factory.get_item(self.parent_rel_path)

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
        return self.rel_path == "" or self.rel_path == "/"

    @property
    def created(self):
        return time.ctime(os.path.getctime(self.absolute_path))

    @property
    def modified(self):
        return time.ctime(os.path.getmtime(self.absolute_path))

    @property
    def modified_time(self):
        return os.path.getmtime(self.absolute_path)

    def rename(self, name):
        new_path = os.path.join(self.parent_path, name)
        os.rename(self.absolute_path, new_path)
        self.absolute_path = new_path
        self.rel_path = os.path.join(self.parent.rel_path, name)
        self.name = name

    def delete(self):
        if not self.is_root:
            if self.is_dir:
                shutil.rmtree(self.absolute_path)
            else:
                os.remove(self.absolute_path)
            self.is_deleted = True


class FileItem(Item):
    def __init__(self, factory, user, path):
        super(FileItem, self).__init__(factory, user, path)

    def read_byte(self):
        f = open(self.absolute_path, 'rb')
        content = f.read()
        f.close()
        return content

    def write_chunks(self, chunks):
        f = open(self.absolute_path, 'wb+')
        for chunk in chunks:
            f.write(chunk)
        f.close()

    def write_content(self, content):
        f = open(self.absolute_path, 'w')
        f.write(content)
        f.close()

    def create_empty(self):
        f = open(self.absolute_path, 'w')
        f.close()


class DirectoryItem(Item):
    def __init__(self, factory, user, path):
        super(DirectoryItem, self).__init__(factory, user, path)

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
                    child_item = self.factory.get_item(self.rel_path + "/" + child)
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

    def create_child_file(self, name):
        return self.factory.new_file(self.make_path_to_new_item(name))

    def create_child_directory(self, name):
        return self.factory.new_directory(self.make_path_to_new_item(name))

    def create_empty(self):
        if not os.path.exists(self.absolute_path):
            os.makedirs(self.absolute_path)
