import json
import importlib.util
import os
from typing import Dict, List, Optional, Any

class EndpointManager:
    """Manages ERP endpoint configurations and matches them to user actions."""
    
    def __init__(self, endpoints_file_path: str = "erp_endpoints.py"):
        # Update the path to point to the config folder
        if not os.path.isabs(endpoints_file_path):
            # Get the config directory path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_dir = os.path.join(os.path.dirname(current_dir), 'config')
            self.endpoints_file_path = os.path.join(config_dir, endpoints_file_path)
        else:
            self.endpoints_file_path = endpoints_file_path
        self.endpoints = {}
        self.action_mappings = {}
        self.load_endpoints()
    
    def load_endpoints(self):
        """Load endpoint configurations from the Python file."""
        try:
            if not os.path.exists(self.endpoints_file_path):
                print(f"Endpoints file not found: {self.endpoints_file_path}")
                return
            
            # Load the module dynamically
            spec = importlib.util.spec_from_file_location("erp_endpoints", self.endpoints_file_path)
            endpoints_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(endpoints_module)
            
            # Get the configurations
            self.endpoints = getattr(endpoints_module, 'ERP_ENDPOINTS', {})
            self.action_mappings = getattr(endpoints_module, 'ACTION_MAPPINGS', {})
            
            print(f"Loaded {len(self.endpoints)} endpoint configurations")
            
        except Exception as e:
            print(f"Error loading endpoints: {e}")
            self.endpoints = {}
            self.action_mappings = {}
    
    def reload_endpoints(self):
        """Reload endpoint configurations (useful for dynamic updates)."""
        self.load_endpoints()
    
    def get_endpoint_config(self, endpoint_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific endpoint."""
        return self.endpoints.get(endpoint_name)
    
    def get_matching_endpoints(self, user_action: Dict[str, Any]) -> List[str]:
        """Get endpoint names that match the user action."""
        action_type = user_action.get("type", "")
        payload = user_action.get("payload", {})
        
        matching_endpoints = []
        
        # Check action mappings
        if action_type in self.action_mappings:
            type_mappings = self.action_mappings[action_type]
            
            # Check for specific screen/entity mappings
            if action_type == "open_screen":
                screen = payload.get("screen", "")
                if screen in type_mappings:
                    matching_endpoints.extend(type_mappings[screen])
            
            # Check for general mappings
            if "any" in type_mappings:
                matching_endpoints.extend(type_mappings["any"])
        
        return list(set(matching_endpoints))  # Remove duplicates
    
    def get_suggested_endpoint_for_action(self, user_action: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get the best endpoint suggestion for a user action."""
        matching_endpoints = self.get_matching_endpoints(user_action)
        
        if not matching_endpoints:
            return None
        
        # For now, return the first matching endpoint
        # You can add more sophisticated logic here later
        endpoint_name = matching_endpoints[0]
        endpoint_config = self.get_endpoint_config(endpoint_name)
        
        if endpoint_config:
            return {
                "endpoint_name": endpoint_name,
                "config": endpoint_config
            }
        
        return None
    
    def format_endpoints_for_llm(self) -> str:
        """Format all endpoints in a way that's useful for the LLM."""
        if not self.endpoints:
            return "No endpoint configurations available."
        
        formatted = "# Available ERP API Endpoints\n\n"
        
        for endpoint_name, config in self.endpoints.items():
            formatted += f"## {endpoint_name}\n"
            formatted += f"**Description**: {config.get('description', 'No description')}\n"
            formatted += f"**Method**: {config.get('method', 'GET')}\n"
            formatted += f"**Path**: {config.get('path', 'No path specified')}\n"
            
            if config.get('query_params'):
                formatted += f"**Query Parameters**: {config['query_params']}\n"
            
            formatted += "**Request Body**:\n"
            formatted += "```json\n"
            formatted += json.dumps(config.get('body', {}), indent=2)
            formatted += "\n```\n"
            
            if config.get('triggers'):
                formatted += f"**Triggered by**: {', '.join(config['triggers'])}\n"
            
            formatted += "\n---\n\n"
        
        return formatted
    
    def get_endpoint_summary(self) -> Dict[str, Any]:
        """Get a summary of available endpoints."""
        return {
            "total_endpoints": len(self.endpoints),
            "endpoint_names": list(self.endpoints.keys()),
            "action_mappings": self.action_mappings,
            "file_path": self.endpoints_file_path
        }
