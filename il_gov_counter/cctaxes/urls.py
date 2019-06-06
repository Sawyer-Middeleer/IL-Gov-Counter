from . import views
from django.contrib import admin
from django.urls import include, path
from django.conf.urls import include, url
from .views import index, results

appname = 'cctaxes'
urlpatterns = [
    path('', views.index, name='index'),
    path('results/<int:id>/', views.results, name='results'),
]
