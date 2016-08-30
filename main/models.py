from django.db import models
from django.contrib.auth.models import User
import os


# here will be defined models for home directories,
# info about sharing directories and item-model


# need to bind home direcroty with
# a default django user object
class HomeDirectories (models.Model):
    uid = models.OneToOneField(User)
    # relative path to homedir
    homeDir = models.CharField(max_length=90)

    def __str__(self):
        return self.uid.username + " " + self.homeDir


# need to store information about directory-shareing
class DirectoryShareing (models.Model):
    # wich dir is shared
    directory = models.OneToOneField(HomeDirectories)
    # with who it is shared
    sharedWith = models.OneToOneField(User)
    # bitmask - what owner allows second person to do
    rgts = models.IntegerField()


# abstract item - file or directory
class Item:
    def __init__(self, path):
        if not os.path.exists(path):
            raise FileNotFoundError
        # getting an extension
        nameParts = path.split(".")
        # checking if extension exists
        if len(nameParts) > 1:
            self.extension = nameParts.pop()
        else:
            self.extension = ""
        # parse given path
        pathParts = path.split("\\")
        self.name = pathParts.pop()
        # if there was only username in url
        # we have to pop once again
        if self.name == "":
            self.name = pathParts.pop()
        # making relative path from parts
        self.relativePath = ""
        for part in pathParts:
            self.relativePath += part + "\\"
        self.absolutePath = path

    def __str__(self):
        return self.name  # lol
