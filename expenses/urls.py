from django.urls import path
from .views import ExpenseCreateView, ExpenseApproveView

urlpatterns = [
    path('', ExpenseCreateView.as_view()),
    path('<int:pk>/approve/', ExpenseApproveView.as_view()),
]