from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Expense
from .serializers import ExpenseSerializer
from .permissions import IsEmployee, IsManager
from .services import convert_currency 

class ExpenseCreateView(APIView):

    permission_classes = [IsAuthenticated, IsEmployee]

    def post(self, request):
        serializer = ExpenseSerializer(data=request.data)

        if serializer.is_valid():
            original_amount = request.data['original_amount']
            original_currency = request.data['original_currency']

            converted_amount = convert_currency(
                float(original_amount),
                original_currency
            )

            serializer.save(
                user=request.user,
                converted_amount_inr=converted_amount
            )

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

class ExpenseApproveView(APIView):

    permission_classes = [IsAuthenticated, IsManager]

    def patch(self, request, pk):
        try:
            expense = Expense.objects.get(pk=pk)
        except Expense.DoesNotExist:
            return Response(
                {"detail": "Expense not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Ensure the logged-in manager is the supervisor of the employee who submitted the expense
        if expense.user.manager != request.user and request.user.role != 'ADMIN':
            return Response(
                {"detail": "You are not authorized to approve this expense."},
                status=status.HTTP_403_FORBIDDEN
            )

        expense.status = 'APPROVED'
        expense.approved_by = request.user
        expense.save()

        serializer = ExpenseSerializer(expense)
        return Response(serializer.data, status=status.HTTP_200_OK)

class TeamExpenseListView(APIView):

    permission_classes = [IsAuthenticated, IsManager]

    def get(self, request):
        expenses = Expense.objects.filter(user__manager=request.user)
        serializer = ExpenseSerializer(expenses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)