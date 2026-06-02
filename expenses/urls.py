from django.urls import path
from .views import ExpenseCreateView, ExpenseApproveView, TeamExpenseListView

urlpatterns = [
    path('', ExpenseCreateView.as_view()),
    path('<int:pk>/approve/', ExpenseApproveView.as_view()),
    path('team/', TeamExpenseListView.as_view()),
]