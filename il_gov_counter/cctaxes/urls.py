from . import views

from django.contrib import admin
from django.urls import include, path
from django.conf.urls import include, url

appname = 'cctaxes'
urlpatterns = [
#    url(r'^search/', search),
    path('', views.index, name='index'),
    path('<int:taxcode_id>/', views.detail, name='detail'),
    path('<int:taxcode_id>/results/', views.results, name='results'),
    path('<int:taxcode_id>/search/', views.search, name='search'),
]
