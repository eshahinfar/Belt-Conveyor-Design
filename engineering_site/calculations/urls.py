"""URL declarations for the calculations app."""

from django.urls import path

from . import views

app_name = "calculations"

urlpatterns = [
    path("", views.home, name="home"),
    path("signup/", views.signup, name="signup"),
    path("saved-results/", views.SavedResultsView.as_view(), name="saved_results"),
    path("calculator/<slug:slug>/", views.calculator, name="calculator"),
]
