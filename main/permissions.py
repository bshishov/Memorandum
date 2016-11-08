from .models import Sharing, SharedLink
from . import items

READ = 0
WRITE = 1
ADMIN = 2

__ITEM_KEY = 'item'
__CHILD_KEY = 'child'

PERMISSION_LEVELS = {
    READ: {
        __ITEM_KEY: ('show', 'raw', 'download', 'preview'),
        __CHILD_KEY: ('show', 'raw', 'download', 'preview'),
    },
    WRITE: {
        __ITEM_KEY: ('show', 'raw', 'download', 'preview', 'upload', 'create_new'),
        __CHILD_KEY: ('show', 'raw', 'download', 'preview', 'upload', 'create_new', 'rename', 'delete'),
    },
    ADMIN: {
        __ITEM_KEY: ('show', 'raw', 'download', 'preview', 'upload', 'create_new', 'share', 'unshare'),
        __CHILD_KEY: ('show', 'raw', 'download', 'preview', 'upload', 'create_new', 'rename', 'delete', 'share', 'unshare'),
    },
}

ALL_PERMISSIONS = PERMISSION_LEVELS.keys()


def has_permission(user, item, action):
    if not user or not user.is_authenticated:
        return guest_has_permission(item, action)

    if user == item.owner:
        return True

    sharing = get_nearest_sharing(user, item)

    if not sharing:
        return False

    return __is_permitted(item.rel_path, sharing.permissions, action)


def get_nearest_sharing(user, item):
    sharings = Sharing.objects.filter(owner=item.owner, shared_with=user)

    if len(sharings) == 0:
        return None

    sorted_sharings = sorted(sharings, key=lambda sh: -len(sh.item))
    for sharing in sorted_sharings:
        shared_item_rel_path = sharing.item

        if sharing.item == "":
            return sharing

        if item.rel_path.startswith(shared_item_rel_path):
            return sharing

    return None


def guest_has_permission(item, action):
    # guest can access only by shared link
    if not isinstance(item.factory, items.SharedLinkItemFactory):
        return False

    return __is_permitted(item.rel_path, item.factory.link.permissions, action)


def __is_permitted(relative_path, permission, action):
    if permission not in ALL_PERMISSIONS:
        raise RuntimeError('Unknown permission')

    permission_level = PERMISSION_LEVELS[permission]

    if relative_path not in ('', '/'):
        if action in permission_level[__CHILD_KEY]:
            return True
    else:
        if action in permission_level[__ITEM_KEY]:
            return True

    return False
