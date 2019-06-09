from . import views
from django.contrib import admin
from django.urls import include, path, re_path
from django.conf.urls import include, url
from .views import index, results

appname = 'cctaxes'
urlpatterns = [
    path('', views.index, name='index'),
    path('results/<int:id>/', views.results, name='results'),
    path('tax-impact/', views.tax_impact, name='tax-impact'),
]
