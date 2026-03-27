import argparse
from client import MumuClient

def main():
    parser = argparse.ArgumentParser(description="Manage RAG Memory and Foreshadows")
    parser.add_argument("--action", required=True, choices=["add_foreshadow"], help="Action to perform")
    parser.add_argument("--content", required=True, help="Content of the foreshadow")
    
    parser.add_argument("--project_id", type=str, help="The bound Novel Project ID (Required if not in env)")
    parser.add_argument("--style_id", type=str, help="The bound Style ID (Optional, overrides .env)")
    args = parser.parse_args()
    client = MumuClient(project_id=args.project_id, style_id=getattr(args, 'style_id', None))
    if not client.project_id:
        print("Error: --project_id argument is required or must be set in .env")
        return
    
    print(f"Executing {args.action} on bound project {client.project_id}...")
    
    try:
        if args.action == "add_foreshadow":
            data = {"project_id": client.project_id, "content": args.content, "status": "pending"}
            client.post("foreshadows", json_data=data)
            print("Foreshadow added successfully.")
            
    except Exception as e:
        print(f"Memory management failed: {e}")

if __name__ == "__main__":
    main()
