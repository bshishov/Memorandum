from django.urls import re_path
from . import views


urlpatterns = [
    re_path(r'^access_denied$', views.access_denied, name='access_denied'),
    re_path(r'^login/?$', views.login_view, name='login_view'),
    re_path(r'^logout/?$', views.logout_view, name='logout_view'),
    re_path(r'^$', views.home, name='home'),
    re_path(r'^office/(?P<user_id>\d+)/(?P<relative_path>[^?]*)', views.onlyoffice_handler, name="onlyoffice_handler"),
    re_path(r'^(?P<user_id>\d+)/(?P<relative_path>[^?]*)', views.item_handler, name="item_handler"),
    re_path(r'^(?P<link_id>[a-zA-Z0-9]+)/(?P<relative_path>[^?]*)', views.link_handler, name="link_handler"),
]
