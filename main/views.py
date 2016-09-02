from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import Context, loader, RequestContext
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from . import models
from . import items
from . import editors
import os


# help function - need to create users and home directories
def create(request):
    admin = User.objects.get(username="admin")
    dumb = User.objects.get(username="dumb")
    sharing = models.Sharing.objects.get(owner=admin)
    sharing.item = "/subdir"
    sharing.save()
    return HttpResponse("done")


# help function - need to show existing users and home directories
# for ensure that they are created
def show(request):
    admin = User.objects.get(username="admin")
    sharing = models.Sharing.objects.get(owner=admin)
    resp = sharing.shared_with
    return HttpResponse(resp)


# shows login form
def login_view(request):
    user = request.user
    if user.is_authenticated:
        return redirect("/"+user.username)
    else:
        return render(request, 'login_form.html')


# authenticates user
def auth(request):
    user = request.user
    if not user.is_authenticated:
        username = request.POST.get('username', "")
        password = request.POST.get('password', "")
        user = authenticate(username=username, password=password)
        if user is None:
            return redirect("/login")
        login(request, user)
    return redirect("/" + user.username)


def logout_view(request):
    current_user = request.user
    if current_user.is_authenticated:
        logout(request)
    return redirect("/login")


def access_denied(request):
    return HttpResponse("Access denied!!")


# main view function - handles the given item
def index(request, user_name, relative_path):
    try:
        request_user = request.user
        if not request_user.is_authenticated:
            return redirect("/login")
        url_user = User.objects.get(username=user_name)
        home_dir = models.HomeDirectory.objects.get(uid=url_user).home_dir
        current_item_path = os.path.join(home_dir, relative_path)
        # making current item from homedir and url params
        current_item = items.Item(current_item_path, url_user, request.get_full_path())
        # check if request_user can access needed item
        permission = models.Sharing.get_permission(request_user, current_item)
        # getting the needed action or 'show' by default
        chosen_action = request.GET.get('action', 'show')
        if not permission & settings.PERMISSIONS.get(chosen_action):
            return redirect("/access_denied")
        # getting the needed editor or searching for default editor
        editor_name = request.GET.get('editor', None)
        if editor_name is None:
            for possibleEditor in settings.EDITORS:
                if possibleEditor.can_handle(current_item):
                    editor = possibleEditor
                    break
        else:
            for possibleEditor in settings.EDITORS:
                if possibleEditor.name == editor_name:
                    editor = possibleEditor
                    break
            # check if the editor is suitable for this extension
            # (if not, LookupException will be raised)
            if not editor.can_handle(current_item):
                raise LookupError
    except ObjectDoesNotExist:
        return HttpResponse("wrong user or home dir does not exist")
    except KeyError:
        return HttpResponse("No such editor")
    except LookupError:
        return HttpResponse("Wrong editor chosen")
    except FileNotFoundError:
        return HttpResponse("404 not found")
    else:
        action = getattr(editor, chosen_action, editor.not_exists())
        return action(current_item, request, permission)
