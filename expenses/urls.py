from django.urls import path
from .views import ExpenseListCreateView, ApproveExpenseView, RejectExpenseView, TeamExpenseListView

urlpatterns = [
    path('', ExpenseListCreateView.as_view()),
    path(
        '<int:pk>/approve/',
        ApproveExpenseView.as_view()
    ),
    path(
        '<int:pk>/reject/',
        RejectExpenseView.as_view()
    ),
    path('team/', TeamExpenseListView.as_view()),
]