import time
from ..services.knowledge_base import KnowledgeBaseManager
from ..services.llm_client import LLMClient
from ..services.learning_database import LearningDatabase
from ..managers.data_processor import HistoricalDataProcessor

class ERPCopilotService:
    """Main service class that orchestrates the ERP Copilot functionality."""
    
    def __init__(self, store):
        self.store = store
        self.knowledge_base_manager = KnowledgeBaseManager()
        self.data_processor = HistoricalDataProcessor(store)
        self.learning_database = LearningDatabase()
        self.llm_client = None
        self.is_initialized = False
    
    def initialize(self, openai_client):
        """Initialize the copilot service with OpenAI client."""
        try:
            print("Initializing ERP Copilot Service...")
            
            # Create knowledge base files
            files = self.knowledge_base_manager.create_knowledge_base_files()
            if not files:
                print("Warning: No knowledge base files created")
                return False
            
            # Setup vector store
            vector_store_id = self.knowledge_base_manager.setup_vector_store(openai_client)
            if not vector_store_id:
                print("Warning: Vector store setup failed")
                return False
            
            # Setup learning database with vector store
            learning_vector_store_id = self.learning_database.setup_vector_store(openai_client)
            if learning_vector_store_id:
                print(f"Learning database initialized with vector store: {learning_vector_store_id}")
            
            # Initialize LLM client with both vector stores
            self.llm_client = LLMClient(openai_client, vector_store_id, learning_vector_store_id)
            
            self.is_initialized = True
            print("ERP Copilot Service initialized successfully!")
            return True
            
        except Exception as e:
            print(f"Error initializing ERP Copilot Service: {e}")
            return False
    
    def get_suggestion(self, session_id, current_action=None, limit=10):
        """Get AI-powered suggestion based on historical data and current action."""
        if not self.is_initialized:
            return {
                "status": "error",
                "message": "Copilot service not initialized",
                "suggestion": None
            }
        
        try:
            # Format historical data
            formatted_actions = self.data_processor.format_user_actions(
                session_id=session_id, 
                limit=limit
            )
            
            # Add current action if provided
            if current_action:
                current_action_data = {
                    "timestamp": int(time.time()),
                    "action": current_action,
                    "plan": None,
                    "response_summary": None,
                    "is_current": True
                }
                formatted_actions["user_actions"].insert(0, current_action_data)
            
            # Extract business context
            business_context = self.data_processor.extract_business_context(formatted_actions)
            
            # Add business context to the data
            formatted_actions["business_context"] = business_context
            
            # Get learning guidance based on historical feedback
            learning_guidance = None
            if current_action:
                learning_guidance = self.learning_database.get_suggestion_guidance(
                    current_action=current_action,
                    business_context=business_context
                )
            
            # Get LLM suggestion with learning guidance
            llm_response = self.llm_client.generate_suggestion(formatted_actions, learning_guidance)
            
            if llm_response["success"]:
                # Parse the response to extract suggestion and action
                parsed = self.llm_client.parse_suggestion_response(llm_response)
                
                return {
                    "status": "success",
                    "business_suggestion": parsed["business_suggestion"],
                    "suggested_action": parsed["suggested_action"],
                    "business_context": business_context,
                    "learning_guidance": learning_guidance,
                    "data_used": {
                        "session_id": session_id,
                        "records_analyzed": len(formatted_actions["user_actions"]),
                        "time_range": formatted_actions["session_info"]["time_range"]
                    },
                    "raw_llm_response": parsed["raw_response"]
                }
            else:
                return {
                    "status": "error",
                    "message": f"LLM error: {llm_response['error']}",
                    "business_suggestion": None,
                    "suggested_action": None
                }
                
        except Exception as e:
            print(f"Error getting suggestion: {e}")
            return {
                "status": "error",
                "message": f"Service error: {str(e)}",
                "suggestion": None
            }
    
    
    def record_user_feedback(self, action_id, suggestion_context, user_action, feedback_reason=None, execution_result=None):
        """Record user feedback on a suggestion for learning purposes."""
        return self.learning_database.record_feedback(
            action_id=action_id,
            suggestion_context=suggestion_context,
            user_action=user_action,
            feedback_reason=feedback_reason,
            execution_result=execution_result
        )
    
    def get_learning_statistics(self):
        """Get comprehensive learning statistics."""
        return self.learning_database.get_learning_statistics()
    
    def get_status(self):
        """Get the status of the copilot service."""
        status = {
            "initialized": self.is_initialized,
            "vector_store_id": self.knowledge_base_manager.get_vector_store_id() if self.knowledge_base_manager else None,
            "learning_vector_store_id": self.learning_database.vector_store_id if self.learning_database else None,
            "llm_client_ready": self.llm_client is not None,
            "knowledge_base_files": list(self.knowledge_base_manager.data_dir.glob("*.md")) if self.knowledge_base_manager else [],
            "learning_entries_count": len(self.learning_database.entries) if self.learning_database else 0
        }
        return status
