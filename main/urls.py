from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^access_denied$', views.access_denied, name='access_denied'),
    url(r'^login/?$', views.login_view, name='login_view'),
    url(r'^logout/?$', views.logout_view, name='logout_view'),
    url(r'^$', views.home, name='home'),
    url(r'^(?P<user_id>\d+)/(?P<relative_path>[^?]*)', views.item_handler, name="item_handler"),
    url(r'^(?P<link_id>[a-zA-Z0-9]+)/(?P<relative_path>[^?]*)', views.link_handler, name="link_handler"),
]
