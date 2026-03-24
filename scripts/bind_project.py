import argparse
from client import MumuClient

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
    client = MumuClient()
    
    if args.action == "create":
        if not args.title or not args.theme or not args.genre or not args.description:
            print("Error: --title, --description, --theme, and --genre are all required for create action.")
            return
        print(f"Creating a new project: {args.title}...")
        try:
            data = {
                "title": args.title, 
                "description": args.description,
                "theme": args.theme,
                "genre": args.genre
            }
            resp = client.post("projects", json_data=data)
            new_id = resp.get("id")
            print(f"Project created with ID: {new_id}")
            # 自动持久化写入 .env
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
