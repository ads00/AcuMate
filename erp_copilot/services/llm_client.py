import json
from ..config.llm_config import LLMConfig
from ..managers.endpoint_manager import EndpointManager

class LLMClient:
    """Handles communication with the LLM service."""
    
    def __init__(self, client, vector_store_id, learning_vector_store_id=None):
        self.client = client
        self.vector_store_id = vector_store_id
        self.learning_vector_store_id = learning_vector_store_id
        self.endpoint_manager = EndpointManager()
    
    def _read_output_text(self, resp):
        """Extract text output from LLM response."""
        # Try the convenience property; else stitch output_text items
        txt = getattr(resp, "output_text", None)
        if txt:
            return txt
        parts = []
        for it in getattr(resp, "output", []):
            if getattr(it, "type", None) == "output_text":
                parts.append(it.text)
        return "\n".join(parts).strip()
    
    def ask_with_databed(self, prompt: str, temperature: float = 0.2):
        """Ask the LLM with knowledge base context."""
        tools = []
        
        # Your knowledge base (required: vector_store_ids)
        vector_store_ids = []
        if self.vector_store_id:
            vector_store_ids.append(self.vector_store_id)
        if self.learning_vector_store_id:
            vector_store_ids.append(self.learning_vector_store_id)
        
        if vector_store_ids:
            tools.append({"type": "file_search", "vector_store_ids": vector_store_ids})
        
        # Optional web browsing (only include if your account has it enabled)
        try:
            tools.append({"type": "web_search"})
        except:
            pass  # Web search might not be available
        
        req = {
            "model": LLMConfig.MODEL,
            "instructions": LLMConfig.INSTRUCTIONS,
            "tools": tools,
            "input": [{"role": "user", "content": prompt}]
        }
        
        try:
            # Print a readable request preview
            preview = dict(req)
            preview["instructions"] = (LLMConfig.INSTRUCTIONS[:300] + "...") if len(LLMConfig.INSTRUCTIONS) > 300 else LLMConfig.INSTRUCTIONS
            print("=== LLM REQUEST (preview) ===")
            print(json.dumps(preview, indent=2))
            
            resp = self.client.responses.create(**req)
            
            print("\n=== LLM RAW (keys) ===", list(resp.__dict__.keys()))
            answer = self._read_output_text(resp)
            print("\n=== LLM ANSWER ===")
            print(answer or "(no text output)")
            
            return {
                "success": True,
                "answer": answer,
                "raw_response": resp
            }
            
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return {
                "success": False,
                "error": str(e),
                "answer": None
            }
    
    def generate_suggestion(self, user_actions_data, learning_guidance=None):
        """Generate a suggestion based on user actions and learning guidance."""
        # Get the current action to find matching endpoints
        current_action = None
        user_actions = user_actions_data.get("user_actions", [])
        if user_actions and len(user_actions) > 0:
            current_action = user_actions[0].get("action")
        
        # Get suggested endpoint from endpoint manager
        suggested_endpoint = None
        if current_action:
            endpoint_suggestion = self.endpoint_manager.get_suggested_endpoint_for_action(current_action)
            if endpoint_suggestion:
                suggested_endpoint = endpoint_suggestion
        
        # Format user actions as JSON string
        user_actions_json = json.dumps(user_actions_data, indent=2)
        
        # Build learning guidance section
        learning_guidance_text = ""
        if learning_guidance:
            learning_guidance_text = f"""
LEARNING GUIDANCE FROM USER FEEDBACK:
- Historical Success Rate: {learning_guidance.get('historical_success_rate', 0):.1%}
- Confidence Score: {learning_guidance.get('confidence_score', 0.5):.1f}
- Should Suggest: {learning_guidance.get('should_suggest', True)}
- Recommended Approach: {learning_guidance.get('suggested_approach', 'standard')}

PATTERNS TO AVOID (frequently rejected):
{chr(10).join(['- ' + pattern for pattern in learning_guidance.get('avoid_patterns', [])])}

PREFERRED PATTERNS (frequently accepted):
{chr(10).join(['- ' + pattern for pattern in learning_guidance.get('preferred_patterns', [])])}

SIMILAR PAST CONTEXTS:
{chr(10).join([f"- {ctx.get('action')} (similarity: {ctx.get('similarity_score', 0):.1f}) - {ctx.get('business_suggestion', '')[:100]}" 
              for ctx in learning_guidance.get('similar_contexts', [])[:3]])}
"""
        
        # Enhanced prompt that includes learning guidance
        enhanced_prompt = f"""
{LLMConfig.get_prompt_template().format(user_actions=user_actions_json)}

{learning_guidance_text}

AVAILABLE ENDPOINTS:
{self.endpoint_manager.format_endpoints_for_llm()}

IMPORTANT: Your response must include:
1. A business suggestion (1-2 sentences for ERP users, no technical terms)
2. If you recommend an action, provide the EXACT API call details using the endpoints above:

SUGGESTED_ACTION:
{{
  "method": "PUT|POST|GET",
  "endpoint": "/entity/Default/20.200.001/EntityName", 
  "body": {{
    // Use the EXACT body structure from the available endpoints above
    // Adjust only the values, not the structure
  }}
}}

LEARNING RULES:
- Consider the learning guidance above when making suggestions
- If historical success rate is low (<30%), be more conservative
- Avoid patterns that have been frequently rejected
- Prefer patterns that have been frequently accepted
- If confidence is low, focus on informational suggestions rather than actions
- ONLY use endpoints that are listed in the AVAILABLE ENDPOINTS section above
- Use the EXACT body structure from those endpoints
- Only modify the values within the body, never change the structure
- If no specific action is needed, set SUGGESTED_ACTION to null
- Focus on business value in your suggestion, not technical details
"""
        
        return self.ask_with_databed(enhanced_prompt)
    
    def parse_suggestion_response(self, llm_response):
        """Parse LLM response to extract suggestion and action."""
        if not llm_response.get("success") or not llm_response.get("answer"):
            return {
                "business_suggestion": "Unable to generate suggestion",
                "suggested_action": None,
                "raw_response": llm_response
            }
        
        answer = llm_response["answer"]
        
        # Try to extract SUGGESTED_ACTION from response
        suggested_action = None
        business_suggestion = answer
        
        if "SUGGESTED_ACTION:" in answer:
            parts = answer.split("SUGGESTED_ACTION:")
            business_suggestion = parts[0].strip()
            
            if len(parts) > 1:
                action_text = parts[1].strip()
                # Try to parse JSON from the action part
                try:
                    # Find JSON block
                    start = action_text.find('{')
                    if start != -1:
                        # Find matching closing brace
                        brace_count = 0
                        end = start
                        for i, char in enumerate(action_text[start:], start):
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    end = i + 1
                                    break
                        
                        json_str = action_text[start:end]
                        suggested_action = json.loads(json_str)
                        
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"Failed to parse suggested action JSON: {e}")
                    suggested_action = None
        
        return {
            "business_suggestion": business_suggestion,
            "suggested_action": suggested_action,
            "raw_response": llm_response
        }
