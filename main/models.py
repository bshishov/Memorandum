from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.conf import settings
from django.urls import reverse


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

    @property
    def home_dir_item(self):
        from .items import UserItemFactory
        from .item_reps import get_representation
        return get_representation(UserItemFactory(self).get_item('/'))

    @property
    def shared_items_with_me(self):
        from .items import SharedItemItemFactory
        from .item_reps import get_representation
        items = []
        for sharing in self.shared_with_me.all():
            items.append(get_representation(SharedItemItemFactory(sharing).get_item('/')))
        return items


# need to store information about directory-sharing
class Sharing (models.Model):
    # owner of shared dir
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="my_sharings")
    # which item is shared
    item = models.CharField(max_length=1024, blank=True, null=False)
    # with who it is shared
    shared_with = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='shared_with_me')
    # bitmask - what owner allows second person to do
    permissions = models.IntegerField()

    def __str__(self):
        return self.owner.username + " shared " + self.item + " with: " + self.shared_with.username


class SharedLink(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="my_shared_links")
    item = models.CharField(max_length=1024, blank=True, null=False)
    link_id = models.CharField(max_length=256, blank=False, null=False, unique=True)
    permissions = models.IntegerField()

    def __str__(self):
        return self.owner.username + " shared " + self.item

    @property
    def url(self):
        return reverse('link_handler', kwargs={'link_id': self.link_id, 'relative_path': ''})