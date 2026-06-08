from rest_framework import serializers
from .models import Expense

class ExpenseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Expense

        fields = [
            'id',
            'title',
            'description',
            'city',
            'original_amount',
            'original_currency',
            'converted_amount_inr',
            'status',
            'created_at',
        ]

        read_only_fields = [
            'converted_amount_inr',
            'status',
            'created_at',
        ]