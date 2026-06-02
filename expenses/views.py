from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Expense
from .serializers import ExpenseSerializer
from .permissions import IsEmployee

class ExpenseCreateView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = ExpenseSerializer(
            data=request.data
        )

        if serializer.is_valid():

            serializer.save(user=request.user)

            return Response(serializer.data,status.HTTP_201_CREATED)

        return Response(serializer.errors,status.HTTP_400_BAD_REQUEST)