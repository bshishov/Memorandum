from django.shortcuts import render, redirect
from django.template import Context, loader
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from main.models import CustomUser, SharedLink
from . import models
from . import items
from . import editors
from . import permissions


# shows login form
def login_view(request):
    if request.method == 'GET':
        user = request.user
        if user.is_authenticated:
            return redirect(item_handler, user_id=user.id, relative_path="")
        else:
            return render(request, 'login.html')
    elif request.method == 'POST':
        user = request.user
        if not user.is_authenticated:
            email = request.POST.get('email', "")
            password = request.POST.get('password', "")
            user = authenticate(username=email, password=password)
            if user is None:
                return redirect(login_view)
            login(request, user)
        return redirect(item_handler, user_id=user.id, relative_path="")


def home(request):
    """ index page just redirects if logged in """
    if not request.user.is_authenticated:
        return redirect(login_view)
    return redirect(item_handler, user_id=request.user.id, relative_path="")


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
def item_handler(request, user_id, relative_path):
    if not request.user.is_authenticated:
        return redirect(login_view)

    owner = CustomUser.objects.get(id=user_id)
    current_item = items.get_instance(owner, relative_path)

    return __item_handler(request, current_item, request.user)


def link_handler(request, link_id, relative_path):
    link = SharedLink.objects.get(link_id=link_id)
    if not link:
        return redirect(login_view)

    current_item = items.get_instance(link.owner, link.item + '/' + relative_path)
    return __item_handler(request, current_item, request.user)


def __item_handler(request, current_item, request_user):
    try:
        if current_item is None:
            return redirect(access_denied)

        # getting the needed action or 'show' by default
        chosen_action = request.GET.get('action', 'show')

        if not permissions.has_permission(request_user, current_item, chosen_action):
            return redirect(access_denied)

        # getting the needed editor or searching for default editor
        editor_name = request.GET.get('editor', None)
        if editor_name is None:
            editor = editors.get_default_for(current_item)
        else:
            editor = editors.get_editor(editor_name)

        action = getattr(editor, chosen_action, editor.not_exists())
        return action(current_item, request)
    except ObjectDoesNotExist as error:
        context = Context({'error_code': 404,
                           'error_message': "Object doest not exists",
                           'details': str(error)})
        return render(request, "error.html", context)
    except KeyError as error:
        context = Context({'error_code': 404,
                           'error_message': "Editor not found",
                           'details': str(error)})
        return render(request, "error.html", context)
    except LookupError as error:
        context = Context({'error_code': 404,
                           'error_message': "Wrong editor",
                           'details': str(error)})
        return render(request, "error.html", context)
    except FileNotFoundError as error:
        context = Context({'error_code': 404,
                           'error_message': "Not found",
                           'details': str(error)})
        return render(request, "error.html", context)
    except PermissionError as error:
        context = Context({'error_code': 403,
                           'error_message': "OS Permission error",
                           'details': str(error)})
        return render(request, "error.html", context)
    except Exception as error:
        context = Context({'error_code': 500,
                           'error_message': type(error).__name__,
                           'details': error})
        return render(request, "error.html", context)