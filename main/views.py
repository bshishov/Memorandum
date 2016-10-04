from django.shortcuts import render, redirect
from django.template import Context, loader
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from . import models
from . import items
from . import editors


# shows login form
def login_view(request):
    user = request.user
    if user.is_authenticated:
        return redirect(item_handler, user_name=user.username, relative_path="")
    else:
        return render(request, 'login.html')


# authenticates user
def auth(request):
    user = request.user
    if not user.is_authenticated:
        username = request.POST.get('username', "")
        password = request.POST.get('password', "")
        user = authenticate(username=username, password=password)
        if user is None:
            return redirect(login_view)
        login(request, user)
    return redirect(item_handler,  user_name=user.username, relative_path="")


def logout_view(request):
    current_user = request.user
    if current_user.is_authenticated:
        logout(request)
    return redirect(login_view)


def access_denied(request):
    context = Context({'error_code': 403,
                       'error_message': "Access denied",
                       'details': "You are not allowed to perform this action"})
    return render(request, "error.html", context)


# main view function - handles the given item
def item_handler(request, user_name, relative_path):
    try:
        request_user = request.user
        if not request_user.is_authenticated:
            return redirect(login_view)
        owner = User.objects.get(username=user_name)
        # making current item from homedir and url params
        current_item = items.get_instance(owner, relative_path)
        if current_item is None:
            return redirect(access_denied)
        # check if request_user can access needed item
        permission = models.Sharing.get_permission(request_user, current_item)
        # getting the needed action or 'show' by default
        chosen_action = request.GET.get('action', 'show')
        if not permission & settings.PERMISSIONS.get(chosen_action):
            return redirect(access_denied)
        # getting the needed editor or searching for default editor
        editor_name = request.GET.get('editor', None)
        if editor_name is None:
            editor = editors.get_default_for(current_item)
        else:
            editor = editors.get_editor(editor_name)
            # check if the editor is suitable for this extension
            # (if not, LookupException will be raised)
            if not editor.can_handle(current_item):
                raise LookupError
    except ObjectDoesNotExist:
        context = Context({'error_code': 404,
                           'error_message': "Not exists",
                           'details': "User or home directory  does not exist"})
        return render(request, "error.html", context)
    except KeyError:
        context = Context({'error_code': 404,
                           'error_message': "Editor not found",
                           'details': "Requested editor does not exist"})
        return render(request, "error.html", context)
    except LookupError:
        context = Context({'error_code': 404,
                           'error_message': "Wrong editor",
                           'details': "Chosen editor can not handle this item"})
        return render(request, "error.html", context)
    except FileNotFoundError:
        context = Context({'error_code': 404,
                           'error_message': "Not found",
                           'details': "Requested file was not found"})
        return render(request, "error.html", context)
    else:
        action = getattr(editor, chosen_action, editor.not_exists())
        return action(current_item, request, permission)
