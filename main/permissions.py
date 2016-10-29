from .models import Sharing

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
    if not user:
        return guest_has_permission(item, action)

    if user == item.owner:
        return True

    sharing = get_nearest_sharing(user, item)

    if not sharing:
        return False

    if sharing.permissions not in ALL_PERMISSIONS:
        raise RuntimeError('Unknown sharing permission')
        return False

    permission_level = PERMISSION_LEVELS[sharing.permissions]

    if len(sharing.item) < len(item.rel_path):
        if action in permission_level[__CHILD_KEY]:
            return True
    else:
        if action in permission_level[__ITEM_KEY]:
            return True

    return False


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
    return False
