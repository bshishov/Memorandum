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
    user = User.objects.get(username="dumb")
    models.HomeDirectories.objects.create(uid=user, homeDir="d:\\python\\memorandum\\testhomedir")
    return HttpResponse("done")


# help function - need to show existing users and home directories
# for ensure that they are created
def show(request):
    user = User.objects.get(username="admin")
    directory = models.HomeDirectories.objects.get(uid=currUser)
    return HttpResponse(directory)


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


# main view function - handles the given item
def index(request, userName, relativePath):
    try:
        request_user = request.user
        if not request_user.is_authenticated:
            return redirect("/login")
        url_user = User.objects.get(username=userName)
        homeDir = models.HomeDirectories.objects.get(uid=url_user).homeDir
        # making current item from homedir and url params
        currentItemPath= os.path.join(homeDir, relativePath)
        currentItem = items.Item(currentItemPath, url_user, request.get_full_path())
        # getting the needed editor or searching for default editor
        editorName = request.GET.get('editor', None)
        if editorName is None:
            for possibleEditor in settings.EDITORS:
                if possibleEditor.canHandle(currentItem):
                    editor = possibleEditor
                    break
        else:
            for possibleEditor in settings.EDITORS:
                if possibleEditor.name == editorName:
                    editor = possibleEditor
                    break
            # check if the editor is suitable for this extension
            # (if not, LookupException will be raised)
            if not editor.canHandle(currentItem):
                raise LookupError
        # getting the needed action or 'show' by default
        chosenAction = request.GET.get('action', 'show')
    except ObjectDoesNotExist:
        return HttpResponse("wrong user or homedir does not exist")
    except KeyError:
        return HttpResponse("No such editor")
    except LookupError:
        return HttpResponse("Wrong editor chosen")
    except FileNotFoundError:
        return HttpResponse("404 not found")
    except Exception:
        return HttpResponse("Unknown exception")
    else:
        action = getattr(editor, chosenAction, editor.notExists())
        return action(currentItem, request)



