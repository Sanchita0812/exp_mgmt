import requests
import urllib.parse
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from expenses.models import Expense

def get_weather_info(city=None):
    """
    Fetches the current weather for a city from wttr.in.
    Falls back to settings.DEFAULT_WEATHER_CITY if city is not provided.
    """
    if not city:
        city = getattr(settings, 'DEFAULT_WEATHER_CITY', 'Bangalore')
    try:
        url = f"https://wttr.in/{urllib.parse.quote(city)}?format=3"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return f"Weather context ({city}): {response.text.strip()}"
    except Exception as e:
        print(f"Failed to fetch weather for {city}: {str(e)}")
    return None


@shared_task
def send_submission_email_task(expense_id):
    try:
        expense = Expense.objects.select_related('user', 'user__manager').get(id=expense_id)
        employee = expense.user
        manager = employee.manager

        if not manager or not manager.email:
            print(f"Skipping submission email for expense {expense_id}: Manager email not set.")
            return

        weather_info = get_weather_info(expense.city)
        weather_suffix = f"\n\n{weather_info}" if weather_info else ""

        subject = f"New Expense Submitted: {expense.title}"
        message = (
            f"Hello {manager.username},\n\n"
            f"An employee under your management, {employee.username}, has submitted a new expense:\n\n"
            f"Title: {expense.title}\n"
            f"Amount: {expense.original_amount} {expense.original_currency}\n"
            f"Converted Amount: INR {expense.converted_amount_inr}\n"
            f"Description: {expense.description}\n"
            f"City: {expense.city or 'N/A'}\n\n"
            f"Please log into the portal to approve or reject this request.\n\n"
            f"Best regards,\n"
            f"Expense Management System"
            f"{weather_suffix}"
        )
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[manager.email],
            fail_silently=False,
        )
        print(f"Submission email sent successfully for expense {expense_id}")
    except Expense.DoesNotExist:
        print(f"Expense {expense_id} does not exist.")
    except Exception as e:
        print(f"Failed to send submission email: {str(e)}")


@shared_task
def send_approval_email_task(expense_id):
    try:
        expense = Expense.objects.select_related('user', 'approved_by').get(id=expense_id)
        employee = expense.user
        manager = expense.approved_by

        if not employee.email:
            print(f"Skipping approval email for expense {expense_id}: Employee email not set.")
            return

        manager_name = manager.username if manager else "assigned manager"
        weather_info = get_weather_info(expense.city)
        weather_suffix = f"\n\n{weather_info}" if weather_info else ""

        subject = f"Expense Approved: {expense.title}"
        message = (
            f"Hello {employee.username},\n\n"
            f"Your expense request has been approved by {manager_name}.\n\n"
            f"Title: {expense.title}\n"
            f"Amount: {expense.original_amount} {expense.original_currency}\n"
            f"Converted Amount: INR {expense.converted_amount_inr}\n"
            f"City: {expense.city or 'N/A'}\n\n"
            f"Best regards,\n"
            f"Expense Management System"
            f"{weather_suffix}"
        )
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[employee.email],
            fail_silently=False,
        )
        print(f"Approval email sent successfully for expense {expense_id}")
    except Expense.DoesNotExist:
        print(f"Expense {expense_id} does not exist.")
    except Exception as e:
        print(f"Failed to send approval email: {str(e)}")


@shared_task
def send_rejection_email_task(expense_id):
    try:
        expense = Expense.objects.select_related('user', 'approved_by').get(id=expense_id)
        employee = expense.user
        manager = expense.approved_by

        if not employee.email:
            print(f"Skipping rejection email for expense {expense_id}: Employee email not set.")
            return

        manager_name = manager.username if manager else "assigned manager"
        weather_info = get_weather_info(expense.city)
        weather_suffix = f"\n\n{weather_info}" if weather_info else ""

        subject = f"Expense Rejected: {expense.title}"
        message = (
            f"Hello {employee.username},\n\n"
            f"Your expense request has been rejected by {manager_name}.\n\n"
            f"Title: {expense.title}\n"
            f"Amount: {expense.original_amount} {expense.original_currency}\n"
            f"Converted Amount: INR {expense.converted_amount_inr}\n"
            f"City: {expense.city or 'N/A'}\n\n"
            f"Best regards,\n"
            f"Expense Management System"
            f"{weather_suffix}"
        )
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[employee.email],
            fail_silently=False,
        )
        print(f"Rejection email sent successfully for expense {expense_id}")
    except Expense.DoesNotExist:
        print(f"Expense {expense_id} does not exist.")
    except Exception as e:
        print(f"Failed to send rejection email: {str(e)}")
