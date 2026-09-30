from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("capturar/<slug:area>/", views.capturar, name="capturar"),
]
