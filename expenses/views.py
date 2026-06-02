from django.shortcuts import render, get_object_or_404
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

        return Response({
            "message": "Expense approved"
        })


class TeamExpenseListView(APIView):

    permission_classes = [IsAuthenticated, IsManager]

    def get(self, request):
        expenses = Expense.objects.filter(user__manager=request.user)
        serializer = ExpenseSerializer(expenses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)