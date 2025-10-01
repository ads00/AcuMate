import json
import time
import uuid
from datetime import datetime, timedelta

class PendingActionManager:
    """Manages pending actions waiting for user confirmation."""
    
    def __init__(self):
        self.pending_actions = {}  # action_id -> pending_action_data
        self.expiry_minutes = 30  # Actions expire after 30 minutes
    
    def create_pending_action(self, session_id, original_action, suggested_action, llm_suggestion):
        """Create a pending action and return action_id."""
        action_id = f"pending_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        pending_data = {
            "action_id": action_id,
            "session_id": session_id,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(minutes=self.expiry_minutes),
            "original_action": original_action,
            "suggested_action": suggested_action,
            "llm_suggestion": llm_suggestion,
            "status": "pending"  # pending, confirmed, rejected, expired, executed
        }
        
        self.pending_actions[action_id] = pending_data
        self._cleanup_expired()
        
        return action_id
    
    def get_pending_action(self, action_id):
        """Get pending action by ID."""
        self._cleanup_expired()
        return self.pending_actions.get(action_id)
    
    def confirm_action(self, action_id):
        """Confirm a pending action."""
        action = self.pending_actions.get(action_id)
        if not action:
            return None
        
        if action["status"] != "pending":
            return None
        
        if datetime.now() > action["expires_at"]:
            action["status"] = "expired"
            return None
        
        action["status"] = "confirmed"
        action["confirmed_at"] = datetime.now()
        return action
    
    def reject_action(self, action_id):
        """Reject a pending action."""
        action = self.pending_actions.get(action_id)
        if action and action["status"] == "pending":
            action["status"] = "rejected"
            action["rejected_at"] = datetime.now()
            return action
        return None
    
    def mark_executed(self, action_id, execution_result):
        """Mark action as executed with result."""
        action = self.pending_actions.get(action_id)
        if action:
            action["status"] = "executed"
            action["executed_at"] = datetime.now()
            action["execution_result"] = execution_result
            return action
        return None
    
    def _cleanup_expired(self):
        """Remove expired actions."""
        now = datetime.now()
        expired_ids = []
        
        for action_id, action in self.pending_actions.items():
            if now > action["expires_at"] and action["status"] == "pending":
                action["status"] = "expired"
                expired_ids.append(action_id)
        
        # Optionally remove expired actions completely after some time
        cutoff = now - timedelta(hours=24)  # Keep for 24 hours for debugging
        to_remove = []
        for action_id, action in self.pending_actions.items():
            if action.get("expires_at", now) < cutoff:
                to_remove.append(action_id)
        
        for action_id in to_remove:
            del self.pending_actions[action_id]
    
    def get_pending_for_session(self, session_id):
        """Get all pending actions for a session."""
        self._cleanup_expired()
        return {
            action_id: action 
            for action_id, action in self.pending_actions.items() 
            if action["session_id"] == session_id and action["status"] == "pending"
        }
    
    def get_status_summary(self):
        """Get summary of pending actions."""
        self._cleanup_expired()
        summary = {
            "total": len(self.pending_actions),
            "by_status": {}
        }
        
        for action in self.pending_actions.values():
            status = action["status"]
            summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
        
        return summary
