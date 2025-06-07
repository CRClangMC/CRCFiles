from django.urls import re_path as url, path
from django.contrib import admin
from django.views.static import serve
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # 定义路由
    url(r'^$', views.index),
    url(r'^login/$', views.login, name='login'),
    url('upload/', views.upload, name='upload'),
    url('index/', views.index, name='index'),
    url('api/files', views.file_list_api, name='file_list_api'),
    url('api/search', views.search_files, name='search_files'),
    url('upload_chunk/', views.upload_chunk, name='upload_chunk'),
    url('merge_chunks/', views.merge_chunks, name='merge_chunks'),
    url('api/batch_download/', views.batch_download, name='batch_download'),
    url('api/delete_files/', views.delete_files_api, name='delete_files_api'),
    # DEBUG = False 时使用
    url(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT}, name='static'),
]
