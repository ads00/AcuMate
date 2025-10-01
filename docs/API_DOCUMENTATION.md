# ERP Copilot API Documentation

## Overview
The ERP Copilot system provides AI-powered suggestions for ERP actions with a confirmation workflow.

## Workflow
1. User action comes to `/action` endpoint
2. System gets historical data and sends to LLM
3. LLM returns suggestion + specific action endpoint
4. System creates pending action and returns suggestion to frontend
5. Frontend shows suggestion with confirm/reject buttons
6. User confirms via `/action/confirm` or rejects via `/action/reject`
7. If confirmed, system executes the suggested action

## API Endpoints

### 1. Core Action Endpoint

#### POST `/action`
Processes user actions and generates AI suggestions.

**Request:**
```json
{
  "session_id": "user_session_123",
  "action": {
    "type": "open_screen",
    "payload": {
      "screen": "SalesOrder"
    }
  }
}
```

**Response:**
```json
{
  "status": "ok",
  "storage_key": "hist_1728000000_abc123",
  "plan": {
    "description": "Fetch SalesOrders with expanded Details/Allocations",
    "path": "/entity/Default/20.200.001/SalesOrder",
    "params": {"$expand": "Details/Allocations"}
  },
  "request_preview": {
    "method": "GET",
    "url": "http://localhost/MPTask/entity/Default/20.200.001/SalesOrder",
    "params": {"$expand": "Details/Allocations"}
  },
  "response_preview": {
    "status": 200,
    "body_preview": "{ \"value\": [...] }"
  },
  "ai_suggestion": {
    "business_suggestion": "Consider adding related items to increase order value",
    "has_suggested_action": true,
    "requires_confirmation": true,
    "action_id": "pending_1728000000_def456",
    "business_context": {
      "screens_accessed": ["SalesOrder"],
      "entities_involved": ["SalesOrder"]
    }
  }
}
```

### 2. Action Confirmation Endpoints

#### POST `/action/confirm`
Confirms and executes a suggested action.

**Request:**
```json
{
  "action_id": "pending_1728000000_def456"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Suggested action executed successfully",
  "action_id": "pending_1728000000_def456",
  "execution_result": {
    "status": 200,
    "response_preview": "{ \"OrderNbr\": { \"value\": \"000472\" } }"
  },
  "storage_key": "hist_1728000100_ghi789"
}
```

#### POST `/action/reject`
Rejects a suggested action.

**Request:**
```json
{
  "action_id": "pending_1728000000_def456",
  "reason": "Not needed right now"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Action rejected successfully",
  "action_id": "pending_1728000000_def456",
  "reason": "Not needed right now"
}
```

### 3. Action Management Endpoints

#### GET `/action/pending`
Get pending actions for a session.

**Query Parameters:**
- `session_id` (optional): Filter by session ID

**Response:**
```json
{
  "session_id": "user_session_123",
  "pending_actions": {
    "pending_1728000000_def456": {
      "action_id": "pending_1728000000_def456",
      "created_at": "2025-10-01T10:00:00",
      "expires_at": "2025-10-01T10:30:00",
      "business_suggestion": "Consider adding related items",
      "has_suggested_action": true,
      "original_action": {
        "type": "open_screen",
        "payload": {"screen": "SalesOrder"}
      }
    }
  },
  "count": 1
}
```

#### GET `/action/details/{action_id}`
Get detailed information about a specific action.

**Response:**
```json
{
  "action_id": "pending_1728000000_def456",
  "status": "pending",
  "created_at": "2025-10-01T10:00:00",
  "expires_at": "2025-10-01T10:30:00",
  "session_id": "user_session_123",
  "business_suggestion": "Consider adding related items to increase order value",
  "original_action": {
    "type": "open_screen",
    "payload": {"screen": "SalesOrder"}
  },
  "suggested_action": {
    "method": "PUT",
    "endpoint": "/entity/Default/20.200.001/SalesOrder",
    "body": {
      "OrderType": {"value": "SO"},
      "Details": [
        {
          "InventoryID": {"value": "ITEM001"},
          "OrderQty": {"value": "1.00"}
        }
      ]
    }
  }
}
```

### 4. System Endpoints

#### GET `/health`
Basic health check.

**Response:**
```json
{
  "ok": true
}
```

#### GET `/copilot/status`
Get AI copilot service status.

**Response:**
```json
{
  "initialized": true,
  "vector_store_id": "vs_abc123",
  "llm_client_ready": true,
  "openai_available": true,
  "openai_client_ready": true,
  "knowledge_base_files": ["rules.md", "api_shapes.md", "examples.md"]
}
```

#### POST `/copilot/initialize`
Manually initialize the copilot service.

**Response:**
```json
{
  "status": "success",
  "message": "Copilot service initialized successfully"
}
```

### 5. Data Storage Endpoints

#### GET `/store`
List all stored action keys.

**Response:**
```json
{
  "keys": ["hist_1728000000_abc123", "hist_1728000100_def456"]
}
```

#### GET `/store/{key}`
Get detailed stored action data.

**Response:**
```json
{
  "session_id": "user_session_123",
  "ts": 1728000000,
  "action": {
    "type": "open_screen",
    "payload": {"screen": "SalesOrder"}
  },
  "plan": {
    "description": "Fetch SalesOrders",
    "path": "/entity/Default/20.200.001/SalesOrder"
  },
  "request": {
    "method": "GET",
    "url": "http://localhost/MPTask/entity/Default/20.200.001/SalesOrder"
  },
  "response": {
    "status": 200,
    "json": {"value": [...]}
  }
}
```

## Environment Variables

```bash
# Required for LLM functionality
OPENAI_API_KEY=

# ERP Connection
ERP_BASE=http://localhost/MPTask
LOGIN_USERNAME=admin
LOGIN_PASSWORD=123
LOGIN_COMPANY=Company

# Optional
ERP_VERIFY=true  # Set to false for dev SSL bypass
```

## Error Responses

All endpoints return standard error format:

```json
{
  "status": "error",
  "message": "Descriptive error message"
}
```

Common HTTP status codes:
- `400`: Bad Request (missing required fields)
- `401`: Authentication failed
- `404`: Resource not found
- `500`: Internal server error

## Frontend Integration

### Basic Workflow Implementation

```javascript
// 1. Send user action
const response = await fetch('/action', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    session_id: 'user_session_123',
    action: {type: 'open_screen', payload: {screen: 'SalesOrder'}}
  })
});

const data = await response.json();

// 2. Check for AI suggestion
if (data.ai_suggestion?.requires_confirmation) {
  const actionId = data.ai_suggestion.action_id;
  const suggestion = data.ai_suggestion.business_suggestion;
  
  // Show confirmation dialog
  const userConfirmed = confirm(`AI Suggestion: ${suggestion}. Execute?`);
  
  if (userConfirmed) {
    // 3. Confirm action
    await fetch('/action/confirm', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({action_id: actionId})
    });
  } else {
    // 3. Reject action
    await fetch('/action/reject', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({action_id: actionId, reason: 'User declined'})
    });
  }
}
```
