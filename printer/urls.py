from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('p/<slug:slug>/', views.index, name='printout'),
    path('p/<slug:slug>/download/', views.download, name='download'),
    path('api/highlight/', views.highlight_code, name='highlight'),
    path('api/file/', views.file_printout, name='file'),
]
