# Expense Management API

A Django REST Framework backend application designed to streamline employee expense tracking, foreign currency conversion, and manager approval workflows.

---

## API Endpoints & Role Access

### 1. Authentication (All Users)
* **Obtain JWT Tokens (Login)**
  * **URL:** `POST /api/token/`
  * **Payload:** `{"username": "<username>", "password": "<password>"}`
  * **Returns:** `access` and `refresh` tokens.
* **Refresh Access Token**
  * **URL:** `POST /api/token/refresh/`
  * **Payload:** `{"refresh": "<refresh_token>"}`
  * **Returns:** A new `access` token.

---

### 2. Employee Endpoints
* **Create an Expense**
  * **URL:** `POST /api/expenses/`
  * **Headers:** `Authorization: Bearer <employee_access_token>`
  * **Payload:** 
    ```json
    {
        "title": "Client Lunch",
        "description": "Lunch meeting with partner company",
        "original_amount": "50.00",
        "original_currency": "USD"
    }
    ```
* **View Own Expenses**
  * **URL:** `GET /api/expenses/`
  * **Headers:** `Authorization: Bearer <employee_access_token>`

---

### 3. Manager Endpoints
* **View Team Expenses** (Expenses of employees assigned to you)
  * **URL:** `GET /api/expenses/team/`
  * **Headers:** `Authorization: Bearer <manager_access_token>`
* **Approve an Expense**
  * **URL:** `PATCH /api/expenses/<pk>/approve/`
  * **Headers:** `Authorization: Bearer <manager_access_token>`
* **Reject an Expense**
  * **URL:** `PATCH /api/expenses/<pk>/reject/`
  * **Headers:** `Authorization: Bearer <manager_access_token>`

---

### 4. Admin Endpoints
* **View All Expenses** (Admins see all expenses in the system)
  * **URL:** `GET /api/expenses/`
  * **Headers:** `Authorization: Bearer <admin_access_token>`
* **Create an Expense** (Optional)
  * **URL:** `POST /api/expenses/`
  * **Headers:** `Authorization: Bearer <admin_access_token>`

---

## Testing in Postman

1. **Obtain Access Token**:
   * Send a `POST` request to `http://127.0.0.1:8000/api/token/` with a user's JSON credentials.
   * Copy the returned `access` token.

2. **Authenticate Requests**:
   * In Postman, select the **Auth** tab of any request.
   * Set **Type** to **Bearer Token**.
   * Paste the `access` token in the **Token** input field.

3. **Make Requests**:
   * Send requests to the respective endpoints listed above. Ensure your user has the correct role (`ADMIN`, `MANAGER`, or `EMPLOYEE`) for the endpoint you are testing.
