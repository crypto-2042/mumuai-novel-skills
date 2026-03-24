import argparse
from client import MumuClient

def main():
    parser = argparse.ArgumentParser(description="Pulls recent RAG memories and unresolved foreshadowing")
    parser.add_argument("--action", choices=["list-pending", "list-memories"], default="list-pending", help="Action to perform")
    
    args = parser.parse_args()
    client = MumuClient()
    
    if args.action == "list-pending":
        print(f"Fetching unresolved plot hooks and foreshadows for project {client.project_id}...")
        try:
            resp = client.get(f"foreshadows/projects/{client.project_id}/pending-resolve", params={"current_chapter": 1})
            items = resp if isinstance(resp, list) else resp.get("items", [])
            print("\n=== Unresolved Foreshadows ===")
            if not items:
                print("Everything is resolved right now. No pending plot hooks.")
            for f in items:
                print(f"- [ID: {f.get('id')}] Content: {f.get('content')} | Severity: {f.get('importance_score', 0)}")
            print("==============================")
            print("Instruction to Agent: Check this list before outline generation or rewriting.")
        except Exception as e:
            print(f"Failed to fetch pending foreshadows: {e}")
            
    elif args.action == "list-memories":
        print(f"Fetching recent important story memories for project {client.project_id}...")
        try:
            resp = client.get(f"memories/projects/{client.project_id}", params={"limit": 20})
            print("\n=== Recent Story Memories ===")
            for m in resp.get("items", []):
                 print(f"- [{m.get('memory_type')}] {m.get('content')} (Score: {m.get('importance_score', 0)})")
            print("=============================")
        except Exception as e:
            print(f"Failed to fetch memories: {e}")

if __name__ == "__main__":
    main()
