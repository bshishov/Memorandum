from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^access_denied$', views.access_denied, name='access_denied'),
    url(r'^login/?$', views.login_view, name='login_view'),
    url(r'^logout/?$', views.logout_view, name='logout_view'),
    url(r'^$', views.auth, name='home'),
    url(r'^(?P<user_name>\w+)/?(?P<relative_path>[^?]*)', views.item_handler, name="item_handler"),
]
