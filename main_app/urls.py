from django.conf.urls import url
from main_app.views import user_image_list, user_image

urlpatterns = [
    url(r'^images', user_image_list),
    url(r'^image/(?P<file_name>[A-Za-z_0-9.]+)$', user_image)
]
