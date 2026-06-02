from django.urls import path
from .views import ExpenseCreateView, ApproveExpenseView, TeamExpenseListView

urlpatterns = [
    path('', ExpenseCreateView.as_view()),
    path(
        '<int:pk>/approve/',
        ApproveExpenseView.as_view()
    ),
    path('team/', TeamExpenseListView.as_view()),
]