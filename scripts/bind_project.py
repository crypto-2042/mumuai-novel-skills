import json
import argparse
import sys
from client import MumuClient

def wait_for_sse(resp, step_name):
    print(f"--- Running: {step_name} ---")
    final_result = None
    try:
        for line in resp.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith("data: "):
                    try:
                        payload = json.loads(decoded[6:])
                        ptype = payload.get("type")
                        if ptype in ["parsing", "saving", "heartbeat"]:
                            pass  # keep console clean
                        elif ptype == "generating":
                            pass
                        elif ptype == "error":
                            print(f"❌ Error during {step_name}: {payload.get('content')}")
                            sys.exit(1)
                        elif ptype == "result":
                            final_result = payload.get("data")
                        elif ptype == "done":
                            print(f"✅ Finished: {step_name}")
                    except json.JSONDecodeError:
                        pass
    finally:
        resp.close()
    return final_result

def main():
    parser = argparse.ArgumentParser(description="Bind or Create a Novel Project")
    parser.add_argument("--action", required=True, choices=["create", "list", "bind", "list-styles", "bind-style"], help="Action: manage projects or bind writing styles")
    parser.add_argument("--title", type=str, help="Title of the new novel (for create)")
    parser.add_argument("--description", type=str, help="Description/Synopsis of the novel (for create)")
    parser.add_argument("--theme", type=str, help="Theme of the novel (for create) e.g. 奋斗、复仇")
    parser.add_argument("--genre", type=str, help="Genre of the novel (for create) e.g. 科幻、修仙")
    parser.add_argument("--project_id", type=str, help="The project ID to bind (for bind)")
    parser.add_argument("--style_id", type=str, help="The writing style ID to bind (for bind-style)")
    
    args = parser.parse_args()
    client = MumuClient(project_id=getattr(args, 'project_id', None), style_id=getattr(args, 'style_id', None))
    
    if args.action == "create":
        if not args.title or not args.theme or not args.genre or not args.description:
            print("Error: --title, --description, --theme, and --genre are all required for create action.")
            return
        print(f"Creating a new project: {args.title} and running AI initialization wizard...")
        try:
            # 1. World Building
            data = {
                "title": args.title, 
                "description": args.description,
                "theme": args.theme,
                "genre": args.genre,
                "narrative_perspective": "第三人称",
                "target_words": 1000000,
                "chapter_count": 5,
                "character_count": 5,
                "outline_mode": "one-to-many"
            }
            resp = client.post("wizard-stream/world-building", json_data=data, stream=True)
            res1 = wait_for_sse(resp, "World Building")
            new_id = res1.get("project_id") if res1 else None
            if not new_id:
                print("Failed to get project_id from World Building!")
                return
            
            print(f"Project created with ID: {new_id}")
            
            # 2. Career System
            resp2 = client.post("wizard-stream/career-system", json_data={"project_id": new_id}, stream=True)
            wait_for_sse(resp2, "Career System")
            
            # 3. Characters
            resp3 = client.post("wizard-stream/characters", json_data={
                "project_id": new_id, 
                "count": 5,
                "theme": args.theme,
                "genre": args.genre
            }, stream=True)
            wait_for_sse(resp3, "Characters")
            
            # 4. Outline
            resp4 = client.post("wizard-stream/outline", json_data={
                "project_id": new_id,
                "chapter_count": 5,
                "narrative_perspective": "第三人称",
                "target_words": 1000000
            }, stream=True)
            wait_for_sse(resp4, "Outline")

            # 自动持久化并提示该 Agent 未来使用此 ID
            client.set_project_id(new_id)
            print("Successfully bound this Agent to the new novel project.")
        except Exception as e:
            print(f"Failed to create project: {e}")
            
    elif args.action == "list":
        print("Fetching your existing novel projects...")
        try:
            resp = client.get("projects", params={"limit": 20})
            print("=== Existing Projects ===")
            for item in resp.get("items", []):
                print(f"- ID: {item['id']} | Title: {item['title']} | Words: {item.get('current_words', 0)}")
            print("=========================")
            print("Use `--action bind --project_id <ID>` to pick one.")
        except Exception as e:
            print(f"Failed to list projects: {e}")

    elif args.action == "bind":
        if not args.project_id:
            print("Error: --project_id is required for bind action.")
            return
        client.set_project_id(args.project_id)
        print(f"Successfully bound this Agent to project {args.project_id}.")

    elif args.action == "list-styles":
        print("Fetching all available writing styles...")
        try:
            resp = client.get("writing-styles/presets/list")
            print("=== Available Styles ===")
            for item in resp:
                print(f"- ID: {item.get('id')} | Name: {item.get('name')} | Desc: {item.get('description', '')[:50]}")
            print("========================")
            print("Use `--action bind-style --style_id <ID>` to pick one.")
        except Exception as e:
            print(f"Failed to list styles: {e}")

    elif args.action == "bind-style":
        if not hasattr(args, 'style_id') or not args.style_id:
            print("Error: --style_id is required for bind-style action.")
            return
        client.set_style_id(args.style_id)
        print(f"Successfully bound writing style {args.style_id} to this Agent.")

if __name__ == "__main__":
    main()
