import json
import time

class HistoricalDataProcessor:
    """Processes and formats historical ERP data for LLM consumption."""
    
    def __init__(self, store):
        self.store = store
    
    def format_user_actions(self, session_id=None, limit=10):
        """Format recent user actions from the store for LLM analysis."""
        # Get recent records from store
        recent_records = []
        
        for key, record in self.store.items():
            if session_id and record.get("session_id") != session_id:
                continue
            recent_records.append(record)
        
        # Sort by timestamp (most recent first)
        recent_records.sort(key=lambda x: x.get("ts", 0), reverse=True)
        
        # Limit the number of records
        recent_records = recent_records[:limit]
        
        # Format for LLM
        formatted_actions = {
            "session_info": {
                "session_id": session_id,
                "record_count": len(recent_records),
                "time_range": self._get_time_range(recent_records)
            },
            "user_actions": []
        }
        
        for record in recent_records:
            action_data = {
                "timestamp": record.get("ts"),
                "action": record.get("action"),
                "plan": record.get("plan"),
                "response_summary": self._summarize_response(record.get("response"))
            }
            formatted_actions["user_actions"].append(action_data)
        
        return formatted_actions
    
    def _get_time_range(self, records):
        """Get time range of records."""
        if not records:
            return None
        
        timestamps = [r.get("ts", 0) for r in records if r.get("ts")]
        if not timestamps:
            return None
        
        return {
            "earliest": min(timestamps),
            "latest": max(timestamps),
            "span_seconds": max(timestamps) - min(timestamps)
        }
    
    def _summarize_response(self, response):
        """Summarize response data for LLM context."""
        if not response:
            return None
        
        summary = {
            "status": response.get("status"),
            "has_data": bool(response.get("json") or response.get("text")),
            "error": response.get("error")
        }
        
        # Add data summary if available
        if response.get("json"):
            json_data = response["json"]
            if isinstance(json_data, list):
                summary["data_type"] = "list"
                summary["data_count"] = len(json_data)
            elif isinstance(json_data, dict):
                summary["data_type"] = "object"
                summary["data_keys"] = list(json_data.keys())[:5]  # First 5 keys
        
        return summary
    
    def extract_business_context(self, formatted_actions):
        """Extract business context from formatted actions for better LLM understanding."""
        context = {
            "screens_accessed": [],
            "entities_involved": [],
            "recent_operations": [],
            "data_patterns": []
        }
        
        for action_data in formatted_actions.get("user_actions", []):
            action = action_data.get("action", {})
            plan = action_data.get("plan", {})
            
            # Extract screen information
            if action.get("type") == "open_screen":
                screen = action.get("payload", {}).get("screen")
                if screen and screen not in context["screens_accessed"]:
                    context["screens_accessed"].append(screen)
            
            # Extract entity information from plan
            if plan and plan.get("path"):
                path = plan["path"]
                # Extract entity name from path (e.g., /entity/Default/20.200.001/SalesOrder)
                path_parts = path.split("/")
                if len(path_parts) > 4:
                    entity = path_parts[-1]
                    if entity not in context["entities_involved"]:
                        context["entities_involved"].append(entity)
            
            # Extract operation types
            operation = {
                "type": action.get("type"),
                "timestamp": action_data.get("timestamp"),
                "success": action_data.get("response_summary", {}).get("status") == 200
            }
            context["recent_operations"].append(operation)
        
        return context
