# 🤖 Acumate - Acumatica ERP Copilot Framework

An AI-powered assistant system for ERP applications with intelligent action suggestions and automated workflow execution.

## 🏗️ Project Structure

```
erp_copilot/
├── erp_copilot/                    # Main framework package
│   ├── __init__.py                 # Package initialization
│   ├── api/                        # Flask API routes and endpoints
│   │   ├── __init__.py
│   │   └── routes.py               # All API endpoints
│   ├── config/                     # Configuration files
│   │   ├── __init__.py
│   │   ├── llm_config.py          # LLM settings and prompts
│   │   └── erp_endpoints.py       # YOUR ERP endpoint configurations
│   ├── core/                       # Core orchestration services
│   │   ├── __init__.py
│   │   └── copilot_service.py     # Main copilot orchestrator
│   ├── managers/                   # Business logic managers
│   │   ├── __init__.py
│   │   ├── endpoint_manager.py    # Endpoint configuration management
│   │   ├── pending_action_manager.py  # Action confirmation workflow
│   │   └── data_processor.py      # Historical data processing
│   └── services/                   # External service integrations
│       ├── __init__.py
│       ├── llm_client.py          # OpenAI/LLM integration
│       └── knowledge_base.py      # Vector store management
├── tests/                          # Test files
│   └── test_flask_app.py          # Comprehensive test suite
├── docs/                           # Documentation
│   ├── API_DOCUMENTATION.md       # Complete API reference
│   └── ENDPOINTS_GUIDE.md         # How to configure endpoints
├── app.py                          # Main application entry point
└── requirements.txt                # Python dependencies
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
```bash
# Required for AI functionality
export OPENAI_API_KEY=""

# ERP Connection Settings
export ERP_BASE="http://localhost/MPTask"
export LOGIN_USERNAME="admin"
export LOGIN_PASSWORD="123"
export LOGIN_COMPANY="Company"

# Optional
export ERP_VERIFY="false"  # Set to false for dev SSL bypass
```

### 3. Configure Your ERP Endpoints
Edit `erp_copilot/config/erp_endpoints.py` to add your specific ERP API configurations:

```python
ERP_ENDPOINTS = {
    "create_sales_order": {
        "description": "Create a new Sales Order",
        "method": "PUT",
        "path": "/entity/Default/20.200.001/SalesOrder",
        "query_params": "$expand=Details/Allocations",
        "body": {
            # YOUR EXACT REQUEST BODY HERE
        },
        "triggers": ["open_screen_SalesOrder"]
    }
}
```

### 4. Start the Application
```bash
python app.py
```

The server will start at `http://localhost:8000` 🎉

### 5. Run Tests
```bash
python tests/test_flask_app.py
```

## 📋 How It Works

### 🔄 Workflow Overview
1. **User Action** → Frontend sends action to `/action` endpoint
2. **Historical Analysis** → System analyzes user's session history
3. **AI Processing** → LLM analyzes data with your endpoint configurations
4. **Suggestion Generation** → AI suggests next best action with exact API call
5. **User Confirmation** → Frontend shows suggestion with confirm/reject buttons
6. **Action Execution** → On confirmation, system executes your exact API call

### 🎯 Key Features
- **Smart Suggestions**: AI analyzes usage patterns to suggest relevant actions
- **Exact API Matching**: Uses your exact endpoint configurations
- **Confirmation Workflow**: Users confirm before any action is executed
- **Session Management**: Automatic ERP authentication and session handling  
- **Action History**: Complete audit trail of all actions and suggestions
- **Dynamic Configuration**: Reload endpoint configs without restarting

## 📡 API Endpoints

### Core Endpoints
- `POST /action` - Process user actions and get AI suggestions
- `POST /action/confirm` - Confirm and execute suggested actions
- `POST /action/reject` - Reject suggested actions
- `GET /health` - System health check

### Management Endpoints
- `GET /endpoints` - View loaded endpoint configurations
- `POST /endpoints/reload` - Reload endpoint configurations
- `GET /copilot/status` - AI service status
- `GET /action/pending` - View pending actions

### Data Endpoints
- `GET /store` - View stored action history
- `GET /store/{key}` - Get specific action details

## 🔧 Configuration

### ERP Endpoints (`erp_copilot/config/erp_endpoints.py`)
Configure your specific ERP API endpoints here. The AI will use these exact configurations:

```python
ERP_ENDPOINTS = {
    "your_action": {
        "description": "What this does",
        "method": "PUT|POST|GET",
        "path": "/your/api/path", 
        "query_params": "optional_params",
        "body": {
            # Your exact request body structure
        },
        "triggers": ["when_to_suggest_this"]
    }
}
```

### Action Mappings
Map user actions to endpoint suggestions:

```python
ACTION_MAPPINGS = {
    "open_screen": {
        "SalesOrder": ["create_sales_order"],
        "PurchaseOrder": ["create_purchase_order"]
    }
}
```

## 🧪 Testing

Run the comprehensive test suite:
```bash
python tests/test_flask_app.py
```

Tests include:
- ✅ Health checks
- ✅ AI service status
- ✅ Action processing
- ✅ Endpoint management
- ✅ Confirmation workflow
- ✅ Data storage

## 📚 Documentation

- **[API Documentation](docs/API_DOCUMENTATION.md)** - Complete API reference
- **[Endpoints Guide](docs/ENDPOINTS_GUIDE.md)** - How to configure your ERP endpoints

## 🔒 Security Features

- **Authentication**: Automatic ERP session management
- **Action Confirmation**: All suggested actions require user confirmation
- **Session Isolation**: Actions are scoped to user sessions
- **Token Security**: No sensitive tokens exposed in responses
- **Action Expiry**: Pending actions expire after 30 minutes

## 🎛️ Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for LLM functionality | Required |
| `ERP_BASE` | Base URL for your ERP system | `http://localhost/MPTask` |
| `LOGIN_USERNAME` | ERP login username | `admin` |
| `LOGIN_PASSWORD` | ERP login password | `123` |
| `LOGIN_COMPANY` | ERP company identifier | `Company` |
| `ERP_VERIFY` | SSL certificate verification | `true` |

## 🚨 Troubleshooting

### Common Issues

**"No endpoint configurations available"**
- Check `erp_copilot/config/erp_endpoints.py` exists
- Verify `ERP_ENDPOINTS` dictionary is properly defined
- Call `POST /endpoints/reload` to refresh

**"Authentication failed"**
- Check ERP_BASE, LOGIN_USERNAME, LOGIN_PASSWORD environment variables
- Verify ERP system is accessible
- Check SSL settings if using HTTPS

**"LLM not responding"**
- Verify OPENAI_API_KEY is set correctly
- Check OpenAI API status
- Call `GET /copilot/status` to check AI service

## 🎉 Ready to Use!

1. **Configure your endpoints** in `erp_copilot/config/erp_endpoints.py`
2. **Set environment variables** for your ERP system
3. **Start the app** with `python app.py`
4. **Send user actions** to `/action` endpoint
5. **Get intelligent suggestions** with exact API calls! 

The AI will learn from user patterns and suggest the most relevant next actions using your exact ERP API configurations! 🚀

