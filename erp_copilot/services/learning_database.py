"""
Learning Database Manager for ERP Copilot
Tracks user feedback on AI suggestions to improve future recommendations.
"""

import json
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from ..config.llm_config import LLMConfig


class LearningEntry:
    """Represents a single learning entry in the database."""
    
    def __init__(self, 
                 suggestion_context: Dict[str, Any],
                 user_action: str,  # "accepted", "rejected", "ignored"
                 feedback_reason: Optional[str] = None,
                 execution_result: Optional[Dict[str, Any]] = None):
        self.id = str(uuid.uuid4())
        self.timestamp = datetime.now()
        self.suggestion_context = suggestion_context
        self.user_action = user_action
        self.feedback_reason = feedback_reason
        self.execution_result = execution_result
        
        # Extract key features for pattern matching
        self.context_hash = self._generate_context_hash()
        self.pattern_features = self._extract_pattern_features()
    
    def _generate_context_hash(self) -> str:
        """Generate a hash of the context for quick similarity matching."""
        context_str = json.dumps({
            "action_type": self.suggestion_context.get("original_action", {}).get("type"),
            "screen": self.suggestion_context.get("original_action", {}).get("payload", {}).get("screen"),
            "business_suggestion": self.suggestion_context.get("business_suggestion", "")[:100]
        }, sort_keys=True)
        return str(hash(context_str))
    
    def _extract_pattern_features(self) -> Dict[str, Any]:
        """Extract key features for pattern matching."""
        original_action = self.suggestion_context.get("original_action", {})
        suggested_action = self.suggestion_context.get("suggested_action", {})
        
        return {
            "action_type": original_action.get("type"),
            "screen": original_action.get("payload", {}).get("screen"),
            "suggested_method": suggested_action.get("method") if suggested_action else None,
            "suggested_endpoint": suggested_action.get("endpoint") if suggested_action else None,
            "business_context": self.suggestion_context.get("business_context", {}),
            "session_pattern": self._analyze_session_pattern()
        }
    
    def _analyze_session_pattern(self) -> Dict[str, Any]:
        """Analyze patterns in the user's session behavior."""
        business_context = self.suggestion_context.get("business_context", {})
        return {
            "session_length": business_context.get("session_length", 0),
            "action_frequency": business_context.get("action_frequency", {}),
            "common_screens": business_context.get("most_common_screens", []),
            "time_of_day": self.timestamp.hour
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "suggestion_context": self.suggestion_context,
            "user_action": self.user_action,
            "feedback_reason": self.feedback_reason,
            "execution_result": self.execution_result,
            "context_hash": self.context_hash,
            "pattern_features": self.pattern_features
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LearningEntry':
        """Create from dictionary."""
        entry = cls(
            suggestion_context=data["suggestion_context"],
            user_action=data["user_action"],
            feedback_reason=data.get("feedback_reason"),
            execution_result=data.get("execution_result")
        )
        entry.id = data["id"]
        entry.timestamp = datetime.fromisoformat(data["timestamp"])
        entry.context_hash = data["context_hash"]
        entry.pattern_features = data["pattern_features"]
        return entry


class LearningDatabase:
    """
    Manages the learning database that tracks user feedback on AI suggestions.
    Stores data both in JSON files and as vector embeddings for semantic search.
    """
    
    def __init__(self, openai_client=None):
        self.data_dir = LLMConfig.ensure_data_dir()
        self.learning_file = self.data_dir / "learning_entries.json"
        self.patterns_file = self.data_dir / "learned_patterns.json"
        self.openai_client = openai_client
        self.vector_store_id = None
        
        # In-memory cache for quick access
        self.entries: List[LearningEntry] = []
        self.patterns: Dict[str, Any] = {}
        
        # Load existing data
        self._load_data()
    
    def _load_data(self):
        """Load existing learning data from files."""
        try:
            if self.learning_file.exists():
                with open(self.learning_file, 'r') as f:
                    data = json.load(f)
                    self.entries = [LearningEntry.from_dict(entry) for entry in data]
                print(f"Loaded {len(self.entries)} learning entries")
            
            if self.patterns_file.exists():
                with open(self.patterns_file, 'r') as f:
                    self.patterns = json.load(f)
                print(f"Loaded {len(self.patterns)} learned patterns")
                
        except Exception as e:
            print(f"Error loading learning data: {e}")
            self.entries = []
            self.patterns = {}
    
    def _save_data(self):
        """Save learning data to files."""
        try:
            # Save entries
            with open(self.learning_file, 'w') as f:
                json.dump([entry.to_dict() for entry in self.entries], f, indent=2)
            
            # Save patterns
            with open(self.patterns_file, 'w') as f:
                json.dump(self.patterns, f, indent=2)
                
        except Exception as e:
            print(f"Error saving learning data: {e}")
    
    def setup_vector_store(self, openai_client) -> Optional[str]:
        """Setup vector store for learning data."""
        try:
            self.openai_client = openai_client
            
            # Create learning-specific vector store
            vs = openai_client.vector_stores.create(name="erp_learning_feedback_v1")
            self.vector_store_id = vs.id
            print(f"Learning vector store created: {self.vector_store_id}")
            
            # Create learning patterns file for vector search
            self._create_learning_knowledge_file()
            
            # Upload learning patterns to vector store
            learning_file = self.data_dir / "learning_patterns.md"
            if learning_file.exists():
                f = openai_client.files.create(
                    file=(learning_file.name, open(learning_file, "rb")), 
                    purpose="assistants"
                )
                openai_client.vector_stores.files.create_and_poll(
                    vector_store_id=vs.id, 
                    file_id=f.id
                )
                print(f"Learning patterns uploaded to vector store")
            
            return self.vector_store_id
            
        except Exception as e:
            print(f"Error setting up learning vector store: {e}")
            return None
    
    def _create_learning_knowledge_file(self):
        """Create a markdown file with learning patterns for vector search."""
        try:
            content = self._generate_learning_patterns_content()
            learning_file = self.data_dir / "learning_patterns.md"
            learning_file.write_text(content)
            print(f"Learning patterns file created: {learning_file}")
            
        except Exception as e:
            print(f"Error creating learning patterns file: {e}")
    
    def _generate_learning_patterns_content(self) -> str:
        """Generate markdown content with learning patterns."""
        content = ["# ERP Copilot Learning Patterns\n"]
        content.append("This file contains learned patterns from user feedback to improve AI suggestions.\n")
        
        # Analyze acceptance patterns
        accepted_patterns = self._analyze_accepted_patterns()
        content.append("## Successful Patterns (User Accepted)")
        for pattern, details in accepted_patterns.items():
            content.append(f"\n### Pattern: {pattern}")
            content.append(f"- **Occurrences**: {details['count']}")
            content.append(f"- **Success Rate**: {details['success_rate']:.1%}")
            content.append(f"- **Context**: {details['context']}")
            content.append(f"- **Recommendation**: {details['recommendation']}")
        
        # Analyze rejection patterns  
        rejected_patterns = self._analyze_rejected_patterns()
        content.append("\n\n## Failed Patterns (User Rejected)")
        for pattern, details in rejected_patterns.items():
            content.append(f"\n### Pattern: {pattern}")
            content.append(f"- **Occurrences**: {details['count']}")
            content.append(f"- **Rejection Rate**: {details['rejection_rate']:.1%}")
            content.append(f"- **Common Reasons**: {', '.join(details['reasons'])}")
            content.append(f"- **Avoid**: {details['avoid_recommendation']}")
        
        # Context-specific recommendations
        content.append("\n\n## Context-Specific Recommendations")
        context_patterns = self._analyze_context_patterns()
        for context, recommendations in context_patterns.items():
            content.append(f"\n### {context}")
            for rec in recommendations:
                content.append(f"- {rec}")
        
        return "\n".join(content)
    
    def record_feedback(self, 
                       action_id: str,
                       suggestion_context: Dict[str, Any],
                       user_action: str,
                       feedback_reason: Optional[str] = None,
                       execution_result: Optional[Dict[str, Any]] = None) -> str:
        """
        Record user feedback on a suggestion.
        
        Args:
            action_id: ID of the suggested action
            suggestion_context: Full context of the suggestion made
            user_action: "accepted", "rejected", or "ignored"
            feedback_reason: Optional reason for rejection
            execution_result: Result of execution if action was accepted
            
        Returns:
            ID of the learning entry
        """
        try:
            # Create learning entry
            entry = LearningEntry(
                suggestion_context=suggestion_context,
                user_action=user_action,
                feedback_reason=feedback_reason,
                execution_result=execution_result
            )
            
            # Add to entries
            self.entries.append(entry)
            
            # Update patterns
            self._update_patterns(entry)
            
            # Save data
            self._save_data()
            
            # Update vector store if available
            if self.openai_client and self.vector_store_id:
                self._update_vector_store()
            
            print(f"Recorded feedback: {user_action} for action {action_id}")
            return entry.id
            
        except Exception as e:
            print(f"Error recording feedback: {e}")
            return None
    
    def _update_patterns(self, entry: LearningEntry):
        """Update learned patterns based on new feedback."""
        pattern_key = f"{entry.pattern_features['action_type']}_{entry.pattern_features['screen']}"
        
        if pattern_key not in self.patterns:
            self.patterns[pattern_key] = {
                "total_suggestions": 0,
                "accepted": 0,
                "rejected": 0,
                "ignored": 0,
                "success_rate": 0.0,
                "common_rejection_reasons": {},
                "successful_suggestions": [],
                "failed_suggestions": [],
                "last_updated": datetime.now().isoformat()
            }
        
        pattern = self.patterns[pattern_key]
        pattern["total_suggestions"] += 1
        pattern[entry.user_action] += 1
        pattern["success_rate"] = pattern["accepted"] / pattern["total_suggestions"]
        pattern["last_updated"] = datetime.now().isoformat()
        
        # Track rejection reasons
        if entry.user_action == "rejected" and entry.feedback_reason:
            reasons = pattern["common_rejection_reasons"]
            reasons[entry.feedback_reason] = reasons.get(entry.feedback_reason, 0) + 1
        
        # Store successful/failed suggestions for pattern analysis
        suggestion_summary = {
            "business_suggestion": entry.suggestion_context.get("business_suggestion", "")[:200],
            "suggested_action": entry.suggestion_context.get("suggested_action"),
            "timestamp": entry.timestamp.isoformat()
        }
        
        if entry.user_action == "accepted":
            pattern["successful_suggestions"].append(suggestion_summary)
            # Keep only last 10 successful suggestions
            pattern["successful_suggestions"] = pattern["successful_suggestions"][-10:]
        elif entry.user_action == "rejected":
            suggestion_summary["reason"] = entry.feedback_reason
            pattern["failed_suggestions"].append(suggestion_summary)
            # Keep only last 10 failed suggestions
            pattern["failed_suggestions"] = pattern["failed_suggestions"][-10:]
    
    def _update_vector_store(self):
        """Update vector store with new learning patterns."""
        try:
            if not self.openai_client or not self.vector_store_id:
                return
            
            # Recreate learning patterns file
            self._create_learning_knowledge_file()
            
            # Note: In a production system, you might want to update existing files
            # rather than recreating them. For this POC, we recreate the file.
            print("Learning vector store updated with new patterns")
            
        except Exception as e:
            print(f"Error updating learning vector store: {e}")
    
    def get_suggestion_guidance(self, 
                              current_action: Dict[str, Any],
                              business_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get guidance for making suggestions based on learned patterns.
        
        Args:
            current_action: The current user action
            business_context: Current business context
            
        Returns:
            Dictionary with guidance for suggestion generation
        """
        try:
            action_type = current_action.get("type")
            screen = current_action.get("payload", {}).get("screen")
            pattern_key = f"{action_type}_{screen}"
            
            guidance = {
                "should_suggest": True,
                "confidence_score": 0.5,  # Default confidence
                "suggested_approach": "standard",
                "avoid_patterns": [],
                "preferred_patterns": [],
                "historical_success_rate": 0.0,
                "similar_contexts": []
            }
            
            # Check if we have specific patterns for this action/screen combination
            if pattern_key in self.patterns:
                pattern = self.patterns[pattern_key]
                guidance["historical_success_rate"] = pattern["success_rate"]
                guidance["confidence_score"] = min(0.9, pattern["success_rate"])
                
                # If success rate is very low, suggest being more cautious
                if pattern["success_rate"] < 0.3:
                    guidance["should_suggest"] = False
                    guidance["suggested_approach"] = "cautious"
                    
                # Add common rejection reasons to avoid
                top_rejections = sorted(
                    pattern["common_rejection_reasons"].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:3]
                guidance["avoid_patterns"] = [reason for reason, _ in top_rejections]
                
                # Add successful patterns to prefer
                guidance["preferred_patterns"] = [
                    s["business_suggestion"] for s in pattern["successful_suggestions"][-3:]
                ]
            
            # Find similar contexts from other patterns
            similar_contexts = self._find_similar_contexts(current_action, business_context)
            guidance["similar_contexts"] = similar_contexts
            
            return guidance
            
        except Exception as e:
            print(f"Error getting suggestion guidance: {e}")
            return {"should_suggest": True, "confidence_score": 0.5}
    
    def _find_similar_contexts(self, 
                             current_action: Dict[str, Any],
                             business_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find similar contexts from historical data."""
        similar = []
        
        current_screen = current_action.get("payload", {}).get("screen", "").lower()
        current_type = current_action.get("type", "")
        
        for entry in self.entries[-50:]:  # Check last 50 entries
            entry_action = entry.suggestion_context.get("original_action", {})
            entry_screen = entry_action.get("payload", {}).get("screen", "").lower()
            entry_type = entry_action.get("type", "")
            
            # Calculate similarity score
            similarity_score = 0
            if entry_screen == current_screen:
                similarity_score += 0.5
            if entry_type == current_type:
                similarity_score += 0.3
            
            # Check business context similarity
            entry_context = entry.suggestion_context.get("business_context", {})
            if self._contexts_similar(business_context, entry_context):
                similarity_score += 0.2
            
            if similarity_score >= 0.5:  # Threshold for similarity
                similar.append({
                    "action": entry.user_action,
                    "similarity_score": similarity_score,
                    "business_suggestion": entry.suggestion_context.get("business_suggestion", "")[:100],
                    "feedback_reason": entry.feedback_reason,
                    "timestamp": entry.timestamp.isoformat()
                })
        
        return sorted(similar, key=lambda x: x["similarity_score"], reverse=True)[:5]
    
    def _contexts_similar(self, context1: Dict[str, Any], context2: Dict[str, Any]) -> bool:
        """Check if two business contexts are similar."""
        # Simple similarity check - can be enhanced with more sophisticated algorithms
        common_screens1 = set(context1.get("most_common_screens", []))
        common_screens2 = set(context2.get("most_common_screens", []))
        
        if common_screens1 and common_screens2:
            overlap = len(common_screens1.intersection(common_screens2))
            union = len(common_screens1.union(common_screens2))
            return (overlap / union) > 0.3 if union > 0 else False
        
        return False
    
    def _analyze_accepted_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Analyze patterns from accepted suggestions."""
        accepted_entries = [e for e in self.entries if e.user_action == "accepted"]
        patterns = {}
        
        for entry in accepted_entries:
            pattern_key = f"{entry.pattern_features['action_type']}_{entry.pattern_features['screen']}"
            if pattern_key not in patterns:
                patterns[pattern_key] = {
                    "count": 0,
                    "success_rate": 0.0,
                    "context": "",
                    "recommendation": ""
                }
            
            patterns[pattern_key]["count"] += 1
        
        # Calculate success rates and add recommendations
        for pattern_key, details in patterns.items():
            if pattern_key in self.patterns:
                total = self.patterns[pattern_key]["total_suggestions"]
                details["success_rate"] = details["count"] / total if total > 0 else 0.0
                details["context"] = f"Screen: {pattern_key.split('_')[1]}, Action: {pattern_key.split('_')[0]}"
                details["recommendation"] = f"Continue suggesting similar actions for this context"
        
        return patterns
    
    def _analyze_rejected_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Analyze patterns from rejected suggestions."""
        rejected_entries = [e for e in self.entries if e.user_action == "rejected"]
        patterns = {}
        
        for entry in rejected_entries:
            pattern_key = f"{entry.pattern_features['action_type']}_{entry.pattern_features['screen']}"
            if pattern_key not in patterns:
                patterns[pattern_key] = {
                    "count": 0,
                    "rejection_rate": 0.0,
                    "reasons": [],
                    "avoid_recommendation": ""
                }
            
            patterns[pattern_key]["count"] += 1
            if entry.feedback_reason:
                patterns[pattern_key]["reasons"].append(entry.feedback_reason)
        
        # Calculate rejection rates and add recommendations
        for pattern_key, details in patterns.items():
            if pattern_key in self.patterns:
                total = self.patterns[pattern_key]["total_suggestions"]
                details["rejection_rate"] = details["count"] / total if total > 0 else 0.0
                details["reasons"] = list(set(details["reasons"]))  # Remove duplicates
                details["avoid_recommendation"] = f"Avoid suggesting similar actions for this context"
        
        return patterns
    
    def _analyze_context_patterns(self) -> Dict[str, List[str]]:
        """Analyze context-specific patterns and recommendations."""
        context_patterns = {}
        
        # Group entries by time of day
        time_patterns = {"morning": [], "afternoon": [], "evening": []}
        for entry in self.entries:
            hour = entry.timestamp.hour
            if 6 <= hour < 12:
                time_patterns["morning"].append(entry)
            elif 12 <= hour < 18:
                time_patterns["afternoon"].append(entry)
            else:
                time_patterns["evening"].append(entry)
        
        # Analyze patterns for each time period
        for time_period, entries in time_patterns.items():
            if entries:
                accepted_rate = len([e for e in entries if e.user_action == "accepted"]) / len(entries)
                if accepted_rate > 0.7:
                    context_patterns[f"Best time for suggestions: {time_period}"] = [
                        f"Users accept {accepted_rate:.1%} of suggestions during {time_period}",
                        f"Continue providing proactive suggestions during {time_period}"
                    ]
                elif accepted_rate < 0.3:
                    context_patterns[f"Avoid suggestions during: {time_period}"] = [
                        f"Users only accept {accepted_rate:.1%} of suggestions during {time_period}",
                        f"Be more conservative with suggestions during {time_period}"
                    ]
        
        return context_patterns
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get comprehensive learning statistics."""
        total_entries = len(self.entries)
        if total_entries == 0:
            return {"message": "No learning data available yet"}
        
        accepted = len([e for e in self.entries if e.user_action == "accepted"])
        rejected = len([e for e in self.entries if e.user_action == "rejected"])
        ignored = len([e for e in self.entries if e.user_action == "ignored"])
        
        # Recent performance (last 30 days)
        recent_date = datetime.now() - timedelta(days=30)
        recent_entries = [e for e in self.entries if e.timestamp >= recent_date]
        recent_accepted = len([e for e in recent_entries if e.user_action == "accepted"])
        
        return {
            "total_suggestions_tracked": total_entries,
            "overall_acceptance_rate": accepted / total_entries if total_entries > 0 else 0,
            "overall_rejection_rate": rejected / total_entries if total_entries > 0 else 0,
            "ignored_rate": ignored / total_entries if total_entries > 0 else 0,
            "recent_performance": {
                "last_30_days_total": len(recent_entries),
                "last_30_days_accepted": recent_accepted,
                "last_30_days_acceptance_rate": recent_accepted / len(recent_entries) if recent_entries else 0
            },
            "top_rejection_reasons": self._get_top_rejection_reasons(),
            "most_successful_patterns": self._get_most_successful_patterns(),
            "learning_trends": self._get_learning_trends()
        }
    
    def _get_top_rejection_reasons(self) -> List[Dict[str, Any]]:
        """Get the most common rejection reasons."""
        reason_counts = {}
        for entry in self.entries:
            if entry.user_action == "rejected" and entry.feedback_reason:
                reason_counts[entry.feedback_reason] = reason_counts.get(entry.feedback_reason, 0) + 1
        
        return [
            {"reason": reason, "count": count}
            for reason, count in sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
    
    def _get_most_successful_patterns(self) -> List[Dict[str, Any]]:
        """Get the most successful suggestion patterns."""
        successful_patterns = []
        for pattern_key, pattern_data in self.patterns.items():
            if pattern_data["total_suggestions"] >= 3:  # Only patterns with enough data
                successful_patterns.append({
                    "pattern": pattern_key,
                    "success_rate": pattern_data["success_rate"],
                    "total_suggestions": pattern_data["total_suggestions"],
                    "accepted": pattern_data["accepted"]
                })
        
        return sorted(successful_patterns, key=lambda x: x["success_rate"], reverse=True)[:5]
    
    def _get_learning_trends(self) -> Dict[str, Any]:
        """Analyze learning trends over time."""
        if len(self.entries) < 10:
            return {"message": "Not enough data for trend analysis"}
        
        # Split entries into early and recent halves
        mid_point = len(self.entries) // 2
        early_entries = self.entries[:mid_point]
        recent_entries = self.entries[mid_point:]
        
        early_acceptance = len([e for e in early_entries if e.user_action == "accepted"]) / len(early_entries)
        recent_acceptance = len([e for e in recent_entries if e.user_action == "accepted"]) / len(recent_entries)
        
        improvement = recent_acceptance - early_acceptance
        
        return {
            "early_acceptance_rate": early_acceptance,
            "recent_acceptance_rate": recent_acceptance,
            "improvement": improvement,
            "trend": "improving" if improvement > 0.1 else "declining" if improvement < -0.1 else "stable"
        }
