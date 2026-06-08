import urllib.parse
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class GoogleLoginUrlView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_REDIRECT_URI:
            return Response(
                {"error": "Google OAuth configuration is missing in settings."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Google OAuth authorization URL parameters
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "select_account",
        }
        
        url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
        return Response({"url": url}, status=status.HTTP_200_OK)


class GoogleCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        code = request.GET.get("code")
        if not code:
            return Response(
                {"error": "Authorization code not provided by Google."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET or not settings.GOOGLE_REDIRECT_URI:
            return Response(
                {"error": "Google OAuth configuration is missing in settings."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Exchange authorization code for access and ID tokens
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }

        try:
            token_response = requests.post(token_url, data=data)
            token_response_data = token_response.json()
        except requests.exceptions.RequestException as e:
            return Response(
                {"error": f"Failed to connect to Google token server: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY
            )

        if "error" in token_response_data:
            return Response(
                {"error": token_response_data.get("error_description", token_response_data["error"])},
                status=status.HTTP_400_BAD_REQUEST
            )

        access_token = token_response_data.get("access_token")
        
        # Fetch user info using the access token
        userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        try:
            userinfo_response = requests.get(
                userinfo_url,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            userinfo = userinfo_response.json()
        except requests.exceptions.RequestException as e:
            return Response(
                {"error": f"Failed to retrieve user profile from Google: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY
            )

        if "error" in userinfo:
            return Response(
                {"error": userinfo.get("error_description", userinfo["error"])},
                status=status.HTTP_400_BAD_REQUEST
            )

        email = userinfo.get("email")
        if not email:
            return Response(
                {"error": "Google account does not have an email associated."},
                status=status.HTTP_400_BAD_REQUEST
            )

        first_name = userinfo.get("given_name", "")
        last_name = userinfo.get("family_name", "")

        # Get or create the user
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Generate a unique username
            base_username = email.split("@")[0]
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            # Create User
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                role="EMPLOYEE"  # default role
            )

        # Generate JWT tokens for our app
        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role
            }
        }, status=status.HTTP_200_OK)
