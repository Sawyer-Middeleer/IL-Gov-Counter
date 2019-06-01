from . import views

from django.contrib import admin
from django.urls import include, path
from django.conf.urls import patterns, include, url
from InputPin.views import *

appname = 'cctaxes'
urlpatterns = [
    path('cctaxes/', include('cctaxes.urls')),
    path('admin/', admin.site.urls),
    url(r'^search/', search),
    path('', views.IndexView.as_view(), name='index'),
    path('<int:pk>/', views.DetailView.as_view(), name='detail'),
    path('<int:pk>/results/', views.ResultsView.as_view(), name='results'),
    path('<int:question_id>/vote/', views.vote, name='vote'),
]
