import argparse, os, yaml, json, shutil
from agents.controller import agent
from retrieval.search import mask_pii

def load_cfg(path: str):
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}

class MemoryManager:
    """Manages tenant-scoped memory for buffer and summary modes"""
    
    def __init__(self, tenant_id: str, memory_type: str):
        self.tenant_id = tenant_id
        self.memory_type = memory_type
        self.memory_dir = os.path.join(".state", "memory", tenant_id)
        os.makedirs(self.memory_dir, exist_ok=True)
        
    def load_buffer(self):
        """Load buffer memory from JSONL file"""
        buffer_path = os.path.join(self.memory_dir, "buffer.jsonl")
        if os.path.exists(buffer_path):
            with open(buffer_path, "r", encoding="utf-8") as f:
                return [json.loads(line) for line in f if line.strip()]
        return []
    
    def save_buffer(self, buffer):
        """Save buffer memory to JSONL file"""
        buffer_path = os.path.join(self.memory_dir, "buffer.jsonl")
        with open(buffer_path, "w", encoding="utf-8") as f:
            for turn in buffer:
                f.write(json.dumps(turn, ensure_ascii=False) + "\n")
    
    def load_summary(self):
        """Load summary memory"""
        summary_path = os.path.join(self.memory_dir, "summary.txt")
        if os.path.exists(summary_path):
            with open(summary_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        return ""
    
    def save_summary(self, summary):
        """Save summary memory"""
        summary_path = os.path.join(self.memory_dir, "summary.txt")
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(summary)
    
    def clear_memory(self):
        """Clear all memory for this tenant"""
        if os.path.exists(self.memory_dir):
            shutil.rmtree(self.memory_dir)
            os.makedirs(self.memory_dir, exist_ok=True)

def chat_repl(tenant_id: str, memory_type: str, cfg: dict, base_dir: str):
    """Interactive chat REPL with memory management"""
    memory = MemoryManager(tenant_id, memory_type)
    
    print(f"Chat REPL started for tenant {tenant_id} with {memory_type} memory.")
    print("Commands: /clear, /mode buffer, /mode summary, /exit")
    print("Type your messages below:")
    
    while True:
        try:
            user_input = input(f"\n[{tenant_id}]> ").strip()
            
            if not user_input:
                continue
                
            # Handle commands
            if user_input.startswith("/"):
                if user_input == "/exit":
                    print("Goodbye!")
                    break
                elif user_input == "/clear":
                    memory.clear_memory()
                    print("Memory cleared.")
                    continue
                elif user_input == "/mode buffer":
                    memory_type = "buffer"
                    memory = MemoryManager(tenant_id, memory_type)
                    print("Switched to buffer memory mode.")
                    continue
                elif user_input == "/mode summary":
                    memory_type = "summary"
                    memory = MemoryManager(tenant_id, memory_type)
                    print("Switched to summary memory mode.")
                    continue
                else:
                    print("Unknown command. Use /clear, /mode buffer, /mode summary, or /exit")
                    continue
            
            # Process user query
            response = agent(base_dir, tenant_id, user_input, cfg, memory)
            print(response)
            
            # Update memory based on mode
            if memory_type == "buffer":
                buffer = memory.load_buffer()
                # Mask PII before storing
                masked_user = mask_pii(user_input)
                masked_response = mask_pii(response)
                buffer.append({
                    "user": masked_user,
                    "assistant": masked_response
                })
                memory.save_buffer(buffer)
            elif memory_type == "summary":
                # For summary mode, we would typically use an LLM to update the summary
                # For now, we'll just append to a simple summary
                summary = memory.load_summary()
                if summary:
                    summary += f"\n\nUser: {mask_pii(user_input)}\nAssistant: {mask_pii(response)}"
                else:
                    summary = f"User: {mask_pii(user_input)}\nAssistant: {mask_pii(response)}"
                memory.save_summary(summary)
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

def main():
    p = argparse.ArgumentParser(description="Agentic RAG CLI and Chat REPL")
    p.add_argument("--tenant", required=True, choices=["U1", "U2", "U3", "U4"], help="Tenant ID")
    p.add_argument("--query", help="Single-turn query (not used in chat mode)")
    p.add_argument("--memory", choices=["buffer", "summary", "none"], default="summary", help="Memory mode")
    p.add_argument("--chat", action="store_true", help="Start chat REPL mode")
    p.add_argument("--config", default="config.yaml", help="Configuration file path")
    args = p.parse_args()

    cfg = load_cfg(args.config)
    base_dir = os.path.dirname(os.path.dirname(__file__))

    if args.chat:
        # Chat REPL mode
        chat_repl(args.tenant, args.memory, cfg, base_dir)
    else:
        # Single-turn mode
        if not args.query:
            print("Error: --query is required for single-turn mode")
            return
        
        class _Mem: 
            pass
        mem = _Mem()
        mem.kind = args.memory if args.memory != "none" else None
        
        print(agent(base_dir, args.tenant, args.query, cfg, memory=mem))

if __name__ == "__main__":
    main()
