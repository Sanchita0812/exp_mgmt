from django.db import models
from users.models import User

class Expense(models.Model):

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    title = models.CharField(max_length=255)

    description = models.TextField()

    original_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    original_currency = models.CharField(max_length=10)

    converted_amount_inr = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    
    city = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )
    
    approved_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        related_name='approved_expenses',
        on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]