import urllib.parse
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponse
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
        
        # Get requested role (default to EMPLOYEE)
        role = request.GET.get("role", "EMPLOYEE").upper()
        if role not in ["ADMIN", "MANAGER", "EMPLOYEE"]:
            return Response(
                {"error": f"Invalid role choice '{role}'. Allowed roles are: ADMIN, MANAGER, EMPLOYEE."},
                status=status.HTTP_400_BAD_REQUEST
            )

        redirect_param = request.GET.get("redirect", "false").lower() == "true"
        state = f"{role}:true" if redirect_param else f"{role}:false"

        # Google OAuth authorization URL parameters
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "select_account",
            "state": state,  # Pass role and redirect flag through state parameter
        }
        
        url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)

        if redirect_param:
            from django.shortcuts import redirect
            return redirect(url)

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

        # Extract the role and redirect flag from the state parameter
        state_param = request.GET.get("state", "EMPLOYEE:false")
        if ":" in state_param:
            state, redirect_flag = state_param.split(":", 1)
            redirect_flag = redirect_flag.lower() == "true"
        else:
            state = state_param
            redirect_flag = False

        state = state.upper()
        assigned_role = state if state in ["ADMIN", "MANAGER", "EMPLOYEE"] else "EMPLOYEE"

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
                role=assigned_role  # assign role chosen from state
            )

        # Generate JWT tokens for our app
        refresh = RefreshToken.for_user(user)

        if redirect_flag:
            from django.shortcuts import redirect
            redirect_url = (
                f"/api/users/test-oauth/?"
                f"access={refresh.access_token}&refresh={refresh}"
                f"&username={urllib.parse.quote(user.username)}"
                f"&email={urllib.parse.quote(user.email)}"
                f"&role={user.role}"
            )
            return redirect(redirect_url)

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


class OAuthTestFrontView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Expense Management Tester</title>
</head>
<body style="font-family: sans-serif; max-width: 800px; margin: 20px auto; padding: 0 10px;">
    <h1>Expense Management Tester Dashboard</h1>
    
    <div id="auth-section">
        <h2>Not Logged In</h2>
        <p>Select a role to log in with Google OAuth:</p>
        <ul>
            <li><a href="/api/users/google/login/?role=ADMIN&redirect=true">Login as ADMIN</a></li>
            <li><a href="/api/users/google/login/?role=MANAGER&redirect=true">Login as MANAGER</a></li>
            <li><a href="/api/users/google/login/?role=EMPLOYEE&redirect=true">Login as EMPLOYEE</a></li>
        </ul>
    </div>
    
    <div id="app-section" style="display:none;">
        <h2>User Profile</h2>
        <p><strong>Username:</strong> <span id="user-username"></span></p>
        <p><strong>Email:</strong> <span id="user-email"></span></p>
        <p><strong>Role:</strong> <span id="user-role"></span></p>
        <button onclick="logout()">Logout</button>

        <hr>

        <div id="employee-panel" style="display:none;">
            <h3>Create Expense (Employee Action)</h3>
            <form id="expense-form" onsubmit="createExpense(event)">
                <p>Title: <input type="text" id="exp-title" required></p>
                <p>Description: <textarea id="exp-desc" required></textarea></p>
                <p>City: <input type="text" id="exp-city" placeholder="e.g. Bangalore"></p>
                <p>Amount: <input type="number" step="0.01" id="exp-amount" required></p>
                <p>Currency: <input type="text" id="exp-currency" value="USD" required></p>
                <button type="submit">Submit Expense</button>
            </form>
            <div id="expense-result"></div>
        </div>

        <div id="manager-panel" style="display:none;">
            <h3>Approve/Reject Expenses (Manager Action)</h3>
            <button onclick="loadManagerExpenses()">Refresh Pending Expenses</button>
            <table border="1" cellpadding="5" id="pending-table" style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                <thead>
                    <tr style="background: #eee;">
                        <th>ID</th>
                        <th>Title</th>
                        <th>City</th>
                        <th>Amount</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="pending-tbody"></tbody>
            </table>
        </div>

        <hr>

        <h3>Expense List</h3>
        <button onclick="loadExpenses()">Refresh Expense List</button>
        <table border="1" cellpadding="5" id="expenses-table" style="width: 100%; border-collapse: collapse; margin-top: 10px;">
            <thead>
                <tr style="background: #eee;">
                    <th>ID</th>
                    <th>Title</th>
                    <th>City</th>
                    <th>Amount (Original)</th>
                    <th>Amount (INR)</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody id="expenses-tbody"></tbody>
        </table>
    </div>

    <script>
        // Parse URL params
        const urlParams = new URLSearchParams(window.location.search);
        const access = urlParams.get('access');
        const refresh = urlParams.get('refresh');
        const username = urlParams.get('username');
        const email = urlParams.get('email');
        const role = urlParams.get('role');

        if (access && refresh) {
            localStorage.setItem('access_token', access);
            localStorage.setItem('refresh_token', refresh);
            localStorage.setItem('user_username', username || '');
            localStorage.setItem('user_email', email || '');
            localStorage.setItem('user_role', role || '');
            // Redirect to clean URL
            window.location.href = window.location.pathname;
        }

        const token = localStorage.getItem('access_token');
        const userRole = localStorage.getItem('user_role');

        if (token) {
            document.getElementById('auth-section').style.display = 'none';
            document.getElementById('app-section').style.display = 'block';
            document.getElementById('user-username').innerText = localStorage.getItem('user_username');
            document.getElementById('user-email').innerText = localStorage.getItem('user_email');
            document.getElementById('user-role').innerText = userRole;

            // Show panels based on role
            if (userRole === 'EMPLOYEE' || userRole === 'ADMIN') {
                document.getElementById('employee-panel').style.display = 'block';
            }
            if (userRole === 'MANAGER') {
                document.getElementById('manager-panel').style.display = 'block';
                loadManagerExpenses();
            }
            loadExpenses();
        }

        function logout() {
            localStorage.clear();
            window.location.href = window.location.pathname;
        }

        async function createExpense(event) {
            event.preventDefault();
            const title = document.getElementById('exp-title').value;
            const description = document.getElementById('exp-desc').value;
            const city = document.getElementById('exp-city').value;
            const original_amount = document.getElementById('exp-amount').value;
            const original_currency = document.getElementById('exp-currency').value;

            const res = await fetch('/api/expenses/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + token
                },
                body: JSON.stringify({ title, description, city, original_amount, original_currency })
            });
            const data = await res.json();
            const resultDiv = document.getElementById('expense-result');
            if (res.ok) {
                resultDiv.innerHTML = '<p style="color:green;">Expense created successfully! ID: ' + data.id + '</p>';
                document.getElementById('expense-form').reset();
                loadExpenses();
            } else {
                resultDiv.innerHTML = '<p style="color:red;">Error: ' + JSON.stringify(data) + '</p>';
            }
        }

        async function loadExpenses() {
            const res = await fetch('/api/expenses/', {
                headers: { 'Authorization': 'Bearer ' + token }
            });
            if (res.ok) {
                const data = await res.json();
                const tbody = document.getElementById('expenses-tbody');
                tbody.innerHTML = '';
                data.forEach(exp => {
                    tbody.innerHTML += `
                        <tr>
                            <td>${exp.id}</td>
                            <td>${exp.title}</td>
                            <td>${exp.city || 'N/A'}</td>
                            <td>${exp.original_amount} ${exp.original_currency}</td>
                            <td>${exp.converted_amount_inr}</td>
                            <td>${exp.status}</td>
                        </tr>
                    `;
                });
            }
        }

        async function loadManagerExpenses() {
            const res = await fetch('/api/expenses/team/', {
                headers: { 'Authorization': 'Bearer ' + token }
            });
            if (res.ok) {
                const data = await res.json();
                const tbody = document.getElementById('pending-tbody');
                tbody.innerHTML = '';
                data.filter(exp => exp.status === 'PENDING').forEach(exp => {
                    tbody.innerHTML += `
                        <tr>
                            <td>${exp.id}</td>
                            <td>${exp.title}</td>
                            <td>${exp.city || 'N/A'}</td>
                            <td>${exp.original_amount} ${exp.original_currency}</td>
                            <td>${exp.status}</td>
                            <td>
                                <button onclick="actionExpense(${exp.id}, 'approve')">Approve</button>
                                <button onclick="actionExpense(${exp.id}, 'reject')">Reject</button>
                            </td>
                        </tr>
                    `;
                });
            }
        }

        async function actionExpense(id, action) {
            const res = await fetch(`/api/expenses/${id}/${action}/`, {
                method: 'PATCH',
                headers: { 'Authorization': 'Bearer ' + token }
            });
            if (res.ok) {
                alert('Expense ' + action + 'd successfully!');
                loadManagerExpenses();
                loadExpenses();
            } else {
                const data = await res.json();
                alert('Error: ' + JSON.stringify(data));
            }
        }
    </script>
</body>
</html>"""
        return HttpResponse(html_content, content_type="text/html")
