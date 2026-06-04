from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Expense
from .serializers import ExpenseSerializer
from .permissions import IsEmployee, IsManager, IsAdmin
from .services import convert_currency
from notifications.tasks import (
    send_submission_email_task,
    send_approval_email_task,
    send_rejection_email_task,
) 

class ExpenseListCreateView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role == 'ADMIN':
            expenses = Expense.objects.all()
        else:
            expenses = Expense.objects.filter(user=request.user)

        serializer = ExpenseSerializer(expenses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if request.user.role != 'EMPLOYEE' and request.user.role != 'ADMIN':
            return Response(
                {"detail": "Only employees can create expenses."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ExpenseSerializer(data=request.data)

        if serializer.is_valid():
            original_amount = request.data['original_amount']
            original_currency = request.data['original_currency']

            converted_amount = convert_currency(
                float(original_amount),
                original_currency
            )

            expense = serializer.save(
                user=request.user,
                converted_amount_inr=converted_amount
            )

            # Queue celery task to send submission email notification
            send_submission_email_task.delay(expense.id)

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class ApproveExpenseView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsManager
    ]

    def patch(self, request, pk):
        expense = get_object_or_404(
            Expense,
            pk=pk
        )

        expense.status = 'APPROVED'
        expense.approved_by = request.user
        expense.save()

        # Queue celery task to send approval email notification
        send_approval_email_task.delay(expense.id)

        return Response({
            "message": "Expense approved"
        })


class RejectExpenseView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsManager
    ]

    def patch(self, request, pk):
        expense = get_object_or_404(
            Expense,
            pk=pk
        )

        expense.status = 'REJECTED'
        expense.approved_by = request.user
        expense.save()

        # Queue celery task to send rejection email notification
        send_rejection_email_task.delay(expense.id)

        return Response({
            "message": "Expense rejected"
        })


class TeamExpenseListView(APIView):

    permission_classes = [IsAuthenticated, IsManager]

    def get(self, request):
        expenses = Expense.objects.filter(user__manager=request.user)
        serializer = ExpenseSerializer(expenses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)