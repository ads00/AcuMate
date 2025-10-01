# ERP Endpoints Configuration Guide

## Overview
The ERP Copilot system now uses a configurable endpoint system. You can add your specific ERP API endpoints to the `erp_endpoints.py` file, and the LLM will use these exact configurations to suggest actions.

## How It Works

1. **User Action** → System analyzes the action
2. **Endpoint Matching** → System finds relevant endpoints from your configuration
3. **LLM Processing** → LLM gets your exact endpoint bodies and suggests actions
4. **Response** → System returns suggestion with your exact API structure

## Adding Your Endpoints

### Step 1: Open `erp_endpoints.py`
Edit the `ERP_ENDPOINTS` dictionary to add your endpoint configurations.

### Step 2: Add Endpoint Configuration
```python
ERP_ENDPOINTS = {
    "your_action_name": {
        "description": "What this endpoint does",
        "method": "PUT|POST|GET", 
        "path": "/your/actual/endpoint/path",
        "query_params": "optional_query_params",  # Can be empty string or None
        "body": {
            # YOUR EXACT REQUEST BODY HERE
            # The LLM will use this exact structure
            "YourField": {"value": "sample_value"}
        },
        "triggers": ["open_screen_SalesOrder", "other_trigger"]  # When to suggest this
    }
}
```

### Step 3: Configure Action Mappings
```python
ACTION_MAPPINGS = {
    "open_screen": {
        "SalesOrder": ["create_sales_order"],  # When user opens SalesOrder screen
        "PurchaseOrder": ["create_purchase_order"]  # When user opens PurchaseOrder screen
    },
    "add_item": {
        "any": ["create_sales_order"]  # When user adds item to any screen
    }
}
```

## Example Configuration

```python
ERP_ENDPOINTS = {
    "create_sales_order": {
        "description": "Create a new Sales Order",
        "method": "PUT",
        "path": "/entity/Default/20.200.001/SalesOrder", 
        "query_params": "$expand=Details/Allocations",
        "body": {
            "OrderType": {"value": "SO"},
            "OrderNbr": {"value": "000470"},
            "CustomerID": {"value": "ABCHOLDING"},
            "Details": [
                {
                    "InventoryID": {"value": "ADVERT"},
                    "WarehouseID": {"value": "WHOLESALE"},
                    "OrderQty": {"value": "1.00"},
                    "UnitPrice": {"value": "10.00"}
                }
            ]
        },
        "triggers": ["open_screen_SalesOrder"]
    }
}
```

## Testing Your Configuration

1. **Add your endpoints** to `erp_endpoints.py`
2. **Start the Flask app**: `python flask_app.py`
3. **Reload endpoints**: `POST /endpoints/reload`
4. **Test with action**: Send a user action to `/action`
5. **Check suggestion**: LLM will use your exact endpoint structure

## API Endpoints for Endpoint Management

### Get Current Endpoints
```bash
GET /endpoints
```
Returns summary of loaded endpoints.

### Reload Endpoints
```bash
POST /endpoints/reload
```
Reloads configurations from `erp_endpoints.py` file.

## Important Notes

### ✅ What the LLM Will Do:
- Use your EXACT endpoint paths and methods
- Use your EXACT request body structure
- Only modify VALUES within your structure
- Respect your field names and hierarchy

### ❌ What the LLM Will NOT Do:
- Create new endpoints not in your file
- Change your request body structure
- Add fields you didn't define
- Modify field names or hierarchy

## Workflow Example

1. **User opens SalesOrder screen**
2. **System matches** to `"open_screen": {"SalesOrder": ["create_sales_order"]}`
3. **LLM gets** your `create_sales_order` endpoint configuration
4. **LLM suggests** action using your exact body structure
5. **System holds** the action for user confirmation
6. **User confirms** → System executes with your exact API call

## Dynamic Updates

You can modify `erp_endpoints.py` while the Flask app is running:
1. Edit the file
2. Call `POST /endpoints/reload`
3. New configuration is immediately available

No need to restart the Flask application!

## Troubleshooting

### "No endpoint configurations available"
- Check if `erp_endpoints.py` exists
- Verify the `ERP_ENDPOINTS` dictionary is properly defined
- Call `POST /endpoints/reload` to refresh

### "No matching endpoints for action"
- Check your `ACTION_MAPPINGS` configuration
- Ensure the action type and payload match your mappings
- Add appropriate triggers to your endpoint configurations

### LLM not suggesting actions
- Verify endpoints are loaded: `GET /endpoints`
- Check if action mappings are correct
- Ensure endpoint bodies are valid JSON structures
