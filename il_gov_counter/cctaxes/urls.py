from . import views
from django.contrib import admin
from django.urls import include, path
from django.conf.urls import include, url

appname = 'cctaxes'
urlpatterns = [
    path('', views.index, name='index'),
    path('cctaxes/results/', views.results, name='results'),
]
