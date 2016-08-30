from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import Context, loader, RequestContext
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.conf import settings
from . import models
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


# sets
def index(request, userName, relativePath):
    try:
        user = User.objects.get(username=userName)
        homeDir = models.HomeDirectories.objects.get(uid=user).homeDir
        # making current item from homedir and url params
        currentItemPath= os.path.join(homeDir, relativePath)
        currentItem = models.Item(currentItemPath)
        # getting the needed editor or searching for default editor
        chosenEditor = request.GET.get('editor', None)
        if chosenEditor is None:
            for editorName in settings.EDITORNAMES:
                possibleEditor = settings.EDITORS[editorName]
                if possibleEditor.isDefaultFor(currentItem):
                    editor = possibleEditor
                    break
        else:
            editor = settings.EDITORS[chosenEditor]
            # check if the editor is suitable for this extension
            # (if not, LookupException will be raised)
            editor.canHandleProbe(currentItem)
        # getting the needed action or 'show' by default
        chosenAction = request.GET.get('action', 'show')
    except KeyError:
        return HttpResponse("No such editor")
    except LookupError:
        return HttpResponse("Wrong editor chosen")
    except FileNotFoundError:
        return HttpResponse("404 not found")
    except Exception:
        return HttpResponse("Unknown exception")
    else:
        action = getattr(editor, chosenAction, editor.notExists)
        return action(currentItem)



