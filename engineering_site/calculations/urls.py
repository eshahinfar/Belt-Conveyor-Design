"""URL declarations for the calculations app."""

from django.urls import path

from . import views

app_name = "calculations"

urlpatterns = [
    path("", views.home, name="home"),
]
