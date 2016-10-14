from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


# here will be defined models for home directories,
# info about sharing directories and item-model


# need to bind home direcroty with
# a default django user object
class HomeDirectory (models.Model):
    uid = models.OneToOneField(User)
    # relative path to homedir
    home_dir = models.CharField("user's home directory", max_length=90)

    def __str__(self):
        return self.uid.username + ": " + self.home_dir


# need to store information about directory-shareing
class Sharing (models.Model):
    # owner of shared dir
    owner = models.ForeignKey(User, related_name="sharings")
    # wich item is shared
    item = models.CharField(max_length=512)
    # with who it is shared
    shared_with = models.ForeignKey(User)
    # bitmask - what owner allows second person to do
    permissions = models.IntegerField()

    def __str__(self):
        return self.owner.username + " shared " + self.item + " with: " + self.shared_with.username

    # checks if the user is allowed to do smth with directory
    @classmethod
    def get_permission(cls, user, item):
        if user == item.owner:
            return settings.PERMISSIONS.get('Chuck_Norris')
        sharing_notes = Sharing.objects.filter(owner=item.owner)
        permissions = 0
        for sharing_note in sharing_notes:
            beginning = sharing_note.item
            if item.rel_path.startswith(beginning) or sharing_note.item == "/":
                permissions = sharing_note.permissions
                break
        return permissions
