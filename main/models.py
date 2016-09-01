from django.db import models
from django.contrib.auth.models import User


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
