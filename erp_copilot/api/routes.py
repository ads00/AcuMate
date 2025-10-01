# ====== install (if needed) ======
# !pip -q install flask requests openai
 
import os, json, time, uuid, urllib.parse
from flask import Flask, request, jsonify
import requests

# Import our custom classes with updated paths
from erp_copilot.core.copilot_service import ERPCopilotService
from erp_copilot.managers.pending_action_manager import PendingActionManager

# Optional: Import OpenAI client (uncomment if you have OpenAI API access)
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("OpenAI not available. Install with: pip install openai")

# ========= CONFIG =========
# Set these before running the app (env or edit here)
ERP_BASE   = os.getenv("ERP_BASE", "http://localhost/MPTask")      # e.g., http://localhost/MPTask
VERIFY_SSL = os.getenv("ERP_VERIFY", "true").lower() != "false"   # set ERP_VERIFY=false to skip SSL verify (dev only)

# Login credentials
LOGIN_USERNAME = os.getenv("LOGIN_USERNAME", "admin")
LOGIN_PASSWORD = os.getenv("LOGIN_PASSWORD", "123")
LOGIN_COMPANY = os.getenv("LOGIN_COMPANY", "Company")

# Global session variable
SESSION = None

# ========= LOGIN & SESSION MANAGEMENT =========
def login_and_build_session():
    """Login to ERP system and build authenticated session."""
    global SESSION
    
    session = requests.Session()
    login_url = f"{ERP_BASE.rstrip('/')}/entity/auth/login"
    
    login_payload = {
        "name": LOGIN_USERNAME,
        "password": LOGIN_PASSWORD,
        "company": LOGIN_COMPANY
    }

    login_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        print(f"Attempting login to: {login_url}")
        login_response = session.post(login_url, json=login_payload, headers=login_headers, timeout=10, verify=VERIFY_SSL)
        login_response.raise_for_status()
        
        # Check for authentication cookie
        cookies = session.cookies.get_dict()
        if ".ASPXAUTH" in cookies:
            print("Login successful! Authentication cookie received.")
            print(f"Cookies: {list(cookies.keys())}")
            
            # Set additional headers for authenticated requests
            session.headers["Accept"] = "application/json"
            session.headers["User-Agent"] = "erp-poc/0.1"
            
            SESSION = session
            return session
        else:
            print("Login failed - no authentication cookie received.")
            print(f"Response status: {login_response.status_code}")
            print(f"Response text: {login_response.text[:500]}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Login request failed: {e}")
        return None

def get_authenticated_session():
    """Get authenticated session, login if needed."""
    global SESSION
    
    if SESSION is None:
        print("No active session, attempting login...")
        SESSION = login_and_build_session()
    
    return SESSION

# ========= IN-MEMORY STORE =========
STORE = {}  # storage_key -> {action, plan, request, response}

# ========= ERP COPILOT SERVICE =========
copilot_service = ERPCopilotService(STORE)
pending_action_manager = PendingActionManager()

# Initialize OpenAI client if available
if OPENAI_AVAILABLE:
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            openai_client = openai.Client(api_key=openai_api_key)
            # Initialize copilot service (this will be done when first needed)
        else:
            print("OPENAI_API_KEY not found in environment variables")
            openai_client = None
    except Exception as e:
        print(f"Error initializing OpenAI client: {e}")
        openai_client = None
else:
    openai_client = None

def _store_response(record):
    key = f"hist_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    STORE[key] = record
    return key

# ========= PLANNING RULES =========
def plan_historical_get(action: dict):
    """
    Decide which historical GET to call based on the user action.
    Returns a 'plan' dict or None if not applicable.
    """
    a_type = (action or {}).get("type")
    payload = (action or {}).get("payload", {})
    screen = (payload or {}).get("screen", "")
 
    # RULE 1: PurchaseOrder screen -> GET .../PurchaseOrder?=null
    if a_type == "open_screen" and str(screen).lower() == "purchaseorder":
        return {
            "description": "Fetch Purchase Orders (exact curl replication with ?=null).",
            "path": "/entity/Default/20.200.001/PurchaseOrder",
            "params": None,                # no params; odd suffix used instead
            "raw_url_suffix": "?=null"     # (kept to match your curl)
        }
 
    # RULE 2: SalesOrder screen -> GET .../SalesOrder?$expand=Details/Allocations
    if a_type == "open_screen" and str(screen).lower() == "salesorder":
        return {
            "description": "Fetch SalesOrders with expanded Details/Allocations.",
            "path": "/entity/Default/20.200.001/SalesOrder",
            "params": {"$expand": "Details/Allocations"}
        }
 
    # Not mapped in this POC
    return None

# ========= EXECUTION =========
def exec_get(plan: dict):
    """Execute the GET per the plan; return (request_info, response_info)."""
    session = get_authenticated_session()
    
    if session is None:
        return {
            "method": "GET",
            "url": "N/A",
            "error": "Authentication failed"
        }, {
            "error": "Could not authenticate with ERP system"
        }, {
            "status": None,
            "body_preview": "Authentication failed"
        }
    
    base = ERP_BASE.rstrip("/")
    path = plan["path"]
    params = plan.get("params")
    raw_suffix = plan.get("raw_url_suffix", "")
 
    url = f"{base}{path}{raw_suffix}"
 
    # Build a curl-like preview (sanitized headers)
    req_preview = {
        "method": "GET",
        "url": url,
        "params": params,
        "headers": {"Cookie": "<redacted>", "Accept": "application/json"},
        "verify_ssl": VERIFY_SSL,
    }
 
    try:
        r = session.get(url, params=params, timeout=60, verify=VERIFY_SSL)
        status = r.status_code
        
        # Handle authentication failure
        if status == 401 or status == 403:
            print("Authentication expired, attempting re-login...")
            global SESSION
            SESSION = None
            session = get_authenticated_session()
            if session:
                r = session.get(url, params=params, timeout=60, verify=VERIFY_SSL)
                status = r.status_code
            else:
                resp_payload = {"error": "Re-authentication failed", "status": status}
                body_preview = "Re-authentication failed"
                resp_preview = {"status": status, "body_preview": body_preview}
                return req_preview, resp_payload, resp_preview
        
        # Try JSON, else raw text (trim preview)
        try:
            body_json = r.json()
            body_preview = json.dumps(body_json, indent=2)[:2000]
            resp_payload = {"status": status, "json": body_json}
        except Exception:
            text = r.text or ""
            body_preview = text[:2000]
            resp_payload = {"status": status, "text": text}
            
    except requests.exceptions.SSLError as e:
        # retriable path if you want to force verify=False in dev
        resp_payload = {"error": f"SSL error: {e}"}
        body_preview = str(e)
    except Exception as e:
        resp_payload = {"error": repr(e)}
        body_preview = repr(e)
 
    resp_preview = {
        "status": resp_payload.get("status"),
        "body_preview": body_preview
    }
    return req_preview, resp_payload, resp_preview

# ========= FLASK APP =========
app = Flask(__name__)

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/action")
def handle_action():
    """
    Accepts a user action from the frontend:
    {
      "session_id": "sess_123",
      "action": {"type":"open_screen","payload":{"screen":"PurchaseOrder"}}
    }
    """
    body = request.get_json(force=True, silent=True) or {}
    action = body.get("action") or {}
    session_id = body.get("session_id")
 
    plan = plan_historical_get(action)
    if not plan:
        return jsonify({
            "status": "no_history",
            "message": "No historical GET mapped for this action in the POC.",
            "action_echo": action
        }), 200
 
    req_preview, resp_payload, resp_preview = exec_get(plan)
 
    record = {
        "session_id": session_id,
        "ts": int(time.time()),
        "action": action,
        "plan": plan,
        "request": req_preview,
        "response": resp_payload
    }
    key = _store_response(record)

    # Get AI suggestion based on historical data and current action
    ai_suggestion_result = None
    action_id = None
    
    if openai_client:
        try:
            # Initialize copilot service if not already done
            if not copilot_service.is_initialized:
                copilot_service.initialize(openai_client)
            
            # Get AI suggestion with action recommendation
            suggestion_result = copilot_service.get_suggestion(
                session_id=session_id,
                current_action=action,
                limit=5  # Analyze last 5 actions
            )
            
            if suggestion_result["status"] == "success":
                ai_suggestion_result = suggestion_result
                
                # If LLM suggested a specific action, create pending action
                if suggestion_result.get("suggested_action"):
                    action_id = pending_action_manager.create_pending_action(
                        session_id=session_id,
                        original_action=action,
                        suggested_action=suggestion_result["suggested_action"],
                        llm_suggestion=suggestion_result["business_suggestion"]
                    )
                    print(f"Created pending action: {action_id}")
                
        except Exception as e:
            print(f"Error getting AI suggestion: {e}")
            ai_suggestion_result = {"error": f"AI service error: {str(e)}"}

    response_data = {
        "status": "ok",
        "storage_key": key
    }
    
    # Add AI suggestion if available
    if ai_suggestion_result:
        ai_response = {
            "title": "AI Assistant Recommendation",
            "business_suggestion": ai_suggestion_result.get("business_suggestion")
        }
        
        # Add action details if we have a pending action
        if action_id and ai_suggestion_result.get("suggested_action"):
            suggested_action = ai_suggestion_result.get("suggested_action")
            ai_response["action_id"] = action_id
            ai_response["suggested_action"] = {
                "method": suggested_action.get("method"),
                "endpoint": suggested_action.get("endpoint"),
                "description": f"{suggested_action.get('method', 'ACTION')} request to {suggested_action.get('endpoint', 'ERP system')}"
            }
            
        response_data["ai_suggestion"] = ai_response
    
    return jsonify(response_data)

@app.get("/store")
def list_store():
    """List stored keys."""
    return jsonify({"keys": list(STORE.keys())})

@app.get("/store/<key>")
def get_store(key):
    """Fetch the full stored record by key."""
    item = STORE.get(key)
    if not item:
        return jsonify({"error": "not_found"}), 404
    # Do not leak cookies in the response
    safe = dict(item)
    return jsonify(safe)

@app.get("/copilot/status")
def copilot_status():
    """Get the status of the AI copilot service."""
    status = copilot_service.get_status()
    status["openai_available"] = OPENAI_AVAILABLE
    status["openai_client_ready"] = openai_client is not None
    return jsonify(status)

@app.post("/copilot/initialize")
def initialize_copilot():
    """Manually initialize the copilot service."""
    if not openai_client:
        return jsonify({
            "status": "error",
            "message": "OpenAI client not available. Check OPENAI_API_KEY environment variable."
        }), 400
    
    success = copilot_service.initialize(openai_client)
    if success:
        return jsonify({
            "status": "success",
            "message": "Copilot service initialized successfully"
        })
    else:
        return jsonify({
            "status": "error",
            "message": "Failed to initialize copilot service"
        }), 500

@app.post("/copilot/suggest")
def get_copilot_suggestion():
    """Get AI suggestion for a specific session."""
    body = request.get_json(force=True, silent=True) or {}
    session_id = body.get("session_id")
    current_action = body.get("current_action")
    limit = body.get("limit", 5)
    
    if not session_id:
        return jsonify({
            "status": "error",
            "message": "session_id is required"
        }), 400
    
    if not openai_client:
        return jsonify({
            "status": "error",
            "message": "OpenAI client not available"
        }), 400
    
    # Initialize if needed
    if not copilot_service.is_initialized:
        success = copilot_service.initialize(openai_client)
        if not success:
            return jsonify({
                "status": "error",
                "message": "Failed to initialize copilot service"
            }), 500
    
    # Get suggestion
    result = copilot_service.get_suggestion(
        session_id=session_id,
        current_action=current_action,
        limit=limit
    )
    
    return jsonify(result)

@app.post("/action/confirm")
def confirm_suggested_action():
    """Confirm and execute a suggested action."""
    body = request.get_json(force=True, silent=True) or {}
    action_id = body.get("action_id")
    
    if not action_id:
        return jsonify({
            "status": "error",
            "message": "action_id is required"
        }), 400
    
    # Confirm the pending action
    confirmed_action = pending_action_manager.confirm_action(action_id)
    if not confirmed_action:
        return jsonify({
            "status": "error",
            "message": "Action not found, expired, or already processed"
        }), 404
    
    # Execute the suggested action
    try:
        suggested_action = confirmed_action["suggested_action"]
        
        # Get authenticated session
        session = get_authenticated_session()
        if session is None:
            execution_result = {"error": "Authentication failed"}
            pending_action_manager.mark_executed(action_id, execution_result)
            
            # Record learning feedback for authentication failure
            if copilot_service.is_initialized:
                copilot_service.record_user_feedback(
                    action_id=action_id,
                    suggestion_context={
                        "original_action": confirmed_action["original_action"],
                        "business_suggestion": confirmed_action["llm_suggestion"],
                        "suggested_action": confirmed_action["suggested_action"],
                        "business_context": {}
                    },
                    user_action="accepted",
                    execution_result=execution_result
                )
            
            return jsonify({
                "status": "error",
                "message": "Could not authenticate with ERP system"
            }), 401
        
        # Build the URL
        base = ERP_BASE.rstrip("/")
        endpoint = suggested_action.get("endpoint", "")
        method = suggested_action.get("method", "GET").upper()
        body_data = suggested_action.get("body", {})
        
        url = f"{base}{endpoint}"
        
        print(f"Executing suggested action: {method} {url}")
        
        # Execute the request
        if method == "GET":
            r = session.get(url, timeout=60, verify=VERIFY_SSL)
        elif method == "POST":
            r = session.post(url, json=body_data, timeout=60, verify=VERIFY_SSL)
        elif method == "PUT":
            r = session.put(url, json=body_data, timeout=60, verify=VERIFY_SSL)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        status = r.status_code
        
        # Handle authentication failure
        if status == 401 or status == 403:
            print("Authentication expired during action execution, attempting re-login...")
            global SESSION
            SESSION = None
            session = get_authenticated_session()
            if session:
                # Retry the request
                if method == "GET":
                    r = session.get(url, timeout=60, verify=VERIFY_SSL)
                elif method == "POST":
                    r = session.post(url, json=body_data, timeout=60, verify=VERIFY_SSL)
                elif method == "PUT":
                    r = session.put(url, json=body_data, timeout=60, verify=VERIFY_SSL)
                status = r.status_code
        
        # Parse response
        try:
            response_json = r.json()
            execution_result = {"status": status, "json": response_json}
            response_preview = json.dumps(response_json, indent=2)[:1000]
        except Exception:
            text = r.text or ""
            execution_result = {"status": status, "text": text}
            response_preview = text[:1000]
        
        # Mark as executed
        pending_action_manager.mark_executed(action_id, execution_result)
        
        # Record successful execution in learning database
        if copilot_service.is_initialized:
            copilot_service.record_user_feedback(
                action_id=action_id,
                suggestion_context={
                    "original_action": confirmed_action["original_action"],
                    "business_suggestion": confirmed_action["llm_suggestion"],
                    "suggested_action": confirmed_action["suggested_action"],
                    "business_context": {}  # Could be enhanced with more context
                },
                user_action="accepted",
                execution_result=execution_result
            )
        
        # Store the result
        record = {
            "session_id": confirmed_action["session_id"],
            "ts": int(time.time()),
            "action": {"type": "ai_suggested_action", "action_id": action_id},
            "plan": {"description": "AI suggested action execution", "method": method, "endpoint": endpoint},
            "request": {"method": method, "url": url, "body": body_data},
            "response": execution_result
        }
        result_key = _store_response(record)
        
        return jsonify({
            "status": "success",
            "message": "Suggested action executed successfully",
            "action_id": action_id,
            "execution_result": {
                "status": status,
                "response_preview": response_preview
            },
            "storage_key": result_key
        })
        
    except Exception as e:
        error_msg = f"Error executing suggested action: {str(e)}"
        print(error_msg)
        
        execution_result = {"error": error_msg}
        pending_action_manager.mark_executed(action_id, execution_result)
        
        # Record failed execution in learning database
        if copilot_service.is_initialized:
            copilot_service.record_user_feedback(
                action_id=action_id,
                suggestion_context={
                    "original_action": confirmed_action["original_action"],
                    "business_suggestion": confirmed_action["llm_suggestion"],
                    "suggested_action": confirmed_action["suggested_action"],
                    "business_context": {}
                },
                user_action="accepted",
                execution_result=execution_result
            )
        
        return jsonify({
            "status": "error",
            "message": error_msg,
            "action_id": action_id
        }), 500

@app.post("/action/reject")
def reject_suggested_action():
    """Reject a suggested action."""
    body = request.get_json(force=True, silent=True) or {}
    action_id = body.get("action_id")
    reason = body.get("reason", "User rejected")
    
    if not action_id:
        return jsonify({
            "status": "error",
            "message": "action_id is required"
        }), 400
    
    # Reject the pending action
    rejected_action = pending_action_manager.reject_action(action_id)
    if not rejected_action:
        return jsonify({
            "status": "error",
            "message": "Action not found or already processed"
        }), 404
    
    # Record rejection in learning database
    if copilot_service.is_initialized:
        copilot_service.record_user_feedback(
            action_id=action_id,
            suggestion_context={
                "original_action": rejected_action["original_action"],
                "business_suggestion": rejected_action["llm_suggestion"],
                "suggested_action": rejected_action["suggested_action"],
                "business_context": {}  # Could be enhanced with more context
            },
            user_action="rejected",
            feedback_reason=reason
        )
    
    return jsonify({
        "status": "success",
        "message": "Action rejected successfully",
        "action_id": action_id,
        "reason": reason
    })

@app.get("/action/pending")
def get_pending_actions():
    """Get all pending actions (optionally filtered by session)."""
    session_id = request.args.get("session_id")
    
    if session_id:
        pending = pending_action_manager.get_pending_for_session(session_id)
    else:
        # Return summary for all sessions
        return jsonify(pending_action_manager.get_status_summary())
    
    # Format the response to include action details for the session
    formatted_pending = {}
    for action_id, action_data in pending.items():
        formatted_pending[action_id] = {
            "action_id": action_id,
            "created_at": action_data["created_at"].isoformat(),
            "expires_at": action_data["expires_at"].isoformat(),
            "business_suggestion": action_data["llm_suggestion"],
            "has_suggested_action": action_data["suggested_action"] is not None,
            "original_action": action_data["original_action"]
        }
    
    return jsonify({
        "session_id": session_id,
        "pending_actions": formatted_pending,
        "count": len(formatted_pending)
    })

@app.get("/action/details/<action_id>")
def get_action_details(action_id):
    """Get detailed information about a specific action."""
    action = pending_action_manager.get_pending_action(action_id)
    if not action:
        return jsonify({
            "status": "error",
            "message": "Action not found or expired"
        }), 404
    
    # Format response with full details
    response = {
        "action_id": action_id,
        "status": action["status"],
        "created_at": action["created_at"].isoformat(),
        "expires_at": action["expires_at"].isoformat(),
        "session_id": action["session_id"],
        "business_suggestion": action["llm_suggestion"],
        "original_action": action["original_action"],
        "suggested_action": action["suggested_action"] if action["status"] == "pending" else None
    }
    
    # Add execution result if available
    if "execution_result" in action:
        response["execution_result"] = action["execution_result"]
    
    # Add timestamps for status changes
    for timestamp_field in ["confirmed_at", "rejected_at", "executed_at"]:
        if timestamp_field in action:
            response[timestamp_field] = action[timestamp_field].isoformat()
    
    return jsonify(response)

@app.get("/endpoints")
def get_endpoints():
    """Get available endpoint configurations."""
    if not copilot_service.is_initialized:
        return jsonify({
            "status": "error", 
            "message": "Copilot service not initialized"
        }), 400
    
    endpoint_manager = copilot_service.knowledge_base_manager.endpoint_manager
    return jsonify(endpoint_manager.get_endpoint_summary())

@app.post("/endpoints/reload")
def reload_endpoints():
    """Reload endpoint configurations from file."""
    if not copilot_service.is_initialized:
        return jsonify({
            "status": "error",
            "message": "Copilot service not initialized"
        }), 400
    
    try:
        # Reload endpoints
        endpoint_manager = copilot_service.knowledge_base_manager.endpoint_manager
        endpoint_manager.reload_endpoints()
        
        # Recreate knowledge base files with updated endpoints
        copilot_service.knowledge_base_manager.create_knowledge_base_files()
        
        return jsonify({
            "status": "success",
            "message": "Endpoints reloaded successfully",
            "summary": endpoint_manager.get_endpoint_summary()
        })
        
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": f"Failed to reload endpoints: {str(e)}"
        }), 500

# ========= LEARNING DATABASE ENDPOINTS =========

@app.get("/learning/statistics")
def get_learning_statistics():
    """Get comprehensive learning statistics and patterns."""
    if not copilot_service.is_initialized:
        return jsonify({
            "status": "error",
            "message": "Copilot service not initialized"
        }), 400
    
    try:
        stats = copilot_service.get_learning_statistics()
        return jsonify({
            "status": "success",
            "statistics": stats
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error retrieving learning statistics: {str(e)}"
        }), 500

@app.post("/learning/feedback")
def record_manual_feedback():
    """Record manual feedback on past suggestions."""
    body = request.get_json(force=True, silent=True) or {}
    
    required_fields = ["action_id", "user_action"]
    missing_fields = [field for field in required_fields if not body.get(field)]
    
    if missing_fields:
        return jsonify({
            "status": "error",
            "message": f"Missing required fields: {', '.join(missing_fields)}"
        }), 400
    
    if not copilot_service.is_initialized:
        return jsonify({
            "status": "error",
            "message": "Copilot service not initialized"
        }), 400
    
    try:
        # Get the original suggestion context (this would come from your pending actions or historical data)
        suggestion_context = body.get("suggestion_context", {})
        
        feedback_id = copilot_service.record_user_feedback(
            action_id=body["action_id"],
            suggestion_context=suggestion_context,
            user_action=body["user_action"],  # "accepted", "rejected", "ignored"
            feedback_reason=body.get("feedback_reason"),
            execution_result=body.get("execution_result")
        )
        
        return jsonify({
            "status": "success",
            "message": "Feedback recorded successfully",
            "feedback_id": feedback_id
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error recording feedback: {str(e)}"
        }), 500

@app.get("/learning/guidance")
def get_learning_guidance():
    """Get learning guidance for a specific action context."""
    current_action = request.args.get("current_action")
    business_context = request.args.get("business_context")
    
    if not current_action:
        return jsonify({
            "status": "error",
            "message": "current_action parameter is required"
        }), 400
    
    if not copilot_service.is_initialized:
        return jsonify({
            "status": "error",
            "message": "Copilot service not initialized"
        }), 400
    
    try:
        # Parse JSON strings
        try:
            current_action_data = json.loads(current_action)
            business_context_data = json.loads(business_context) if business_context else {}
        except json.JSONDecodeError:
            return jsonify({
                "status": "error",
                "message": "Invalid JSON in parameters"
            }), 400
        
        guidance = copilot_service.learning_database.get_suggestion_guidance(
            current_action=current_action_data,
            business_context=business_context_data
        )
        
        return jsonify({
            "status": "success",
            "guidance": guidance
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error getting learning guidance: {str(e)}"
        }), 500

@app.post("/learning/reset")
def reset_learning_data():
    """Reset all learning data (for development/testing purposes)."""
    body = request.get_json(force=True, silent=True) or {}
    confirm = body.get("confirm", False)
    
    if not confirm:
        return jsonify({
            "status": "error",
            "message": "This action requires confirmation. Set 'confirm': true in request body."
        }), 400
    
    if not copilot_service.is_initialized:
        return jsonify({
            "status": "error",
            "message": "Copilot service not initialized"
        }), 400
    
    try:
        # Clear learning data
        copilot_service.learning_database.entries = []
        copilot_service.learning_database.patterns = {}
        copilot_service.learning_database._save_data()
        
        return jsonify({
            "status": "success",
            "message": "Learning data reset successfully"
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error resetting learning data: {str(e)}"
        }), 500

@app.get("/learning/patterns")
def get_learning_patterns():
    """Get learned patterns and their effectiveness."""
    if not copilot_service.is_initialized:
        return jsonify({
            "status": "error",
            "message": "Copilot service not initialized"
        }), 400
    
    try:
        patterns = copilot_service.learning_database.patterns
        
        # Format patterns for API response
        formatted_patterns = {}
        for pattern_key, pattern_data in patterns.items():
            formatted_patterns[pattern_key] = {
                "success_rate": pattern_data["success_rate"],
                "total_suggestions": pattern_data["total_suggestions"],
                "accepted": pattern_data["accepted"],
                "rejected": pattern_data["rejected"],
                "ignored": pattern_data["ignored"],
                "last_updated": pattern_data["last_updated"],
                "top_rejection_reasons": dict(list(pattern_data["common_rejection_reasons"].items())[:3])
            }
        
        return jsonify({
            "status": "success",
            "patterns": formatted_patterns,
            "total_patterns": len(formatted_patterns)
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error retrieving learning patterns: {str(e)}"
        }), 500

if __name__ == "__main__":
    # In Colab you can run with: app.run(host="0.0.0.0", port=8000)
    app.run(host="0.0.0.0", port=8000, debug=True)
