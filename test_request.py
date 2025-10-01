import requests

# --- Step 1: Start a session ---
session = requests.Session()

# --- Step 2: Login ---
login_url = "http://localhost/MPTask/entity/auth/login"
login_payload = {
    "name": "admin",
    "password": "123",
    "company": "Company"
}

login_headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"  # sometimes needed by ASP.NET
}

try:
    login_response = session.post(login_url, json=login_payload, headers=login_headers, timeout=10)
    login_response.raise_for_status()  # will raise an error if login failed
except requests.exceptions.RequestException as e:
    print("Login request failed:", e)
    exit()

# Check cookies
cookies = session.cookies.get_dict()
if ".ASPXAUTH" in cookies:
    print("Login successful! Cookies:", cookies)
else:
    print("Login failed or cookie not received.")
    exit()

# --- Step 3: Fetch SalesOrder ---
salesorder_url = "http://localhost/MPTask/entity/Default/20.200.001/SalesOrder?$filter=OrderNbr eq '000468'&$expand=Details/Allocations"
params = {
    "$expand": "Details/Allocations"
}

get_headers = {
    "Accept": "application/json"  # ensure server returns JSON
}

try:
    response = session.get(salesorder_url, params=params, headers=get_headers)
    response.raise_for_status()
except requests.exceptions.Timeout:
    print("GET request timed out.")
    exit()
except requests.exceptions.RequestException as e:
    print("GET request failed:", e)
    exit()

# --- Step 4: Print or parse the result ---
try:
    data = response.json()  # parse JSON if server returns it
    print("SalesOrder Data:", data)
except ValueError:
    print("Response is not JSON. Raw text:", response.text)
