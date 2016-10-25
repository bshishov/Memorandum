from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.conf import settings


# here will be defined models for home directories,
# info about sharing directories and item-model

class CustomUserManager(BaseUserManager):
    def create_user(self, email, home_dir, password=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            home_dir=home_dir,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, home_dir, password):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            email,
            password=password,
            home_dir=home_dir
        )
        user.is_admin = True
        user.save(using=self._db)
        return user

    def get_by_natural_key(self, username):
        return CustomUser.objects.get(email=username)


class CustomUser(AbstractBaseUser):
    email = models.EmailField(
        verbose_name='Email address',
        max_length=255,
        unique=True,
    )
    home_dir = models.CharField("Home Directory", max_length=90)
    is_active = models.BooleanField("Is active", default=True)
    is_admin = models.BooleanField("Is admin", default=False)
    date_joined = models.DateTimeField("Date joined", auto_now=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['home_dir',]

    def get_username(self):
        return self.email

    @property
    def username(self):
        return self.email

    def get_full_name(self):
        # The user is identified by their email address
        return self.email

    def get_short_name(self):
        # The user is identified by their email address
        return self.email

    def __str__(self):  # __unicode__ on Python 2
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin


# need to store information about directory-sharing
class Sharing (models.Model):
    # owner of shared dir
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="sharings")
    # which item is shared
    item = models.CharField(max_length=512)
    # with who it is shared
    shared_with = models.ForeignKey(settings.AUTH_USER_MODEL)
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
