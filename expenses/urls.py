from django.urls import path
from .views import ExpenseCreateView

urlpatterns = [
    path('', ExpenseCreateView.as_view()),
]