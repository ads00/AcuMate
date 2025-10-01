import json
from ..config.llm_config import LLMConfig
from ..managers.endpoint_manager import EndpointManager

class KnowledgeBaseManager:
    """Manages the knowledge base files and vector store for the LLM."""
    
    def __init__(self):
        self.data_dir = LLMConfig.ensure_data_dir()
        self.vector_store_id = None
        self.endpoint_manager = EndpointManager()
    
    def create_knowledge_base_files(self):
        """Create the knowledge base files in the data directory."""
        try:
            # Create rules.md
            rules_file = self.data_dir / "rules.md"
            rules_file.write_text(LLMConfig.get_rules_content().strip())
            
            # Create api_shapes.md
            api_shapes_file = self.data_dir / "api_shapes.md"
            api_shapes_file.write_text(LLMConfig.get_api_shapes_content().strip())
            
            # Create examples.md
            examples_file = self.data_dir / "examples.md"
            examples_file.write_text(LLMConfig.get_examples_content().strip())
            
            # Create endpoints.md with current endpoint configurations
            endpoints_file = self.data_dir / "endpoints.md"
            endpoints_content = self.endpoint_manager.format_endpoints_for_llm()
            endpoints_file.write_text(endpoints_content)
            
            print(f"Knowledge base files created in: {self.data_dir}")
            print(f"Loaded {len(self.endpoint_manager.endpoints)} endpoint configurations")
            return list(self.data_dir.glob("*.md"))
            
        except Exception as e:
            print(f"Error creating knowledge base files: {e}")
            return []
    
    def setup_vector_store(self, client):
        """Setup vector store with knowledge base files."""
        try:
            # Create vector store
            vs = client.vector_stores.create(name="erp_databed_v1")
            self.vector_store_id = vs.id
            print(f"Vector store created: {self.vector_store_id}")
            
            # Upload files
            uploaded_ids = []
            for p in self.data_dir.glob("*.md"):
                f = client.files.create(file=(p.name, open(p, "rb")), purpose="assistants")
                uploaded_ids.append(f.id)
            
            # Attach files and poll until processed
            for fid in uploaded_ids:
                client.vector_stores.files.create_and_poll(vector_store_id=vs.id, file_id=fid)
            
            print(f"Added files to vector store: {uploaded_ids}")
            return self.vector_store_id
            
        except Exception as e:
            print(f"Error setting up vector store: {e}")
            return None
    
    def get_vector_store_id(self):
        """Get the vector store ID."""
        return self.vector_store_id
