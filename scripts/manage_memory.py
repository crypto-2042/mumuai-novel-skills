import argparse
from client import MumuClient

def main():
    parser = argparse.ArgumentParser(description="Manage RAG Memory and Foreshadows")
    parser.add_argument("--action", required=True, choices=["add_foreshadow", "add_memory"], help="Action to perform")
    parser.add_argument("--content", required=True, help="Content of the memory or foreshadow")
    
    args = parser.parse_args()
    client = MumuClient()
    
    print(f"Executing {args.action} on bound project {client.project_id}...")
    
    try:
        if args.action == "add_foreshadow":
            data = {"content": args.content, "status": "pending"}
            resp = client.post("foreshadows", json_data=data)
            print("Foreshadow added successfully.")
            
        elif args.action == "add_memory":
            data = {"content": args.content, "type": "lore"}
            resp = client.post(f"memories", json_data=data)
            print("Memory injected successfully.")
            
    except Exception as e:
        print(f"Memory management failed: {e}")

if __name__ == "__main__":
    main()
