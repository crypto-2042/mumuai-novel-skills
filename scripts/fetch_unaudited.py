import argparse
from client import MumuClient

def main():
    parser = argparse.ArgumentParser(description="Fetch Unaudited Chapters")
    parser.add_argument("--project_id", type=str, help="The bound Novel Project ID (Required if not in env)")
    parser.add_argument("--style_id", type=str, help="The bound Style ID (Optional, overrides .env)")
    args = parser.parse_args()
    client = MumuClient(project_id=args.project_id, style_id=getattr(args, 'style_id', None))
    if not client.project_id:
        print("Error: --project_id argument is required or must be set in .env")
        return
    
    print(f"Fetching recently generated (unaudited) chapters for project {client.project_id}...")
    
    try:
        resp = client.get(f"chapters/project/{client.project_id}", params={"limit": 100})
        print("Retrieved chapters needing your review:")
        
        found = False
        for item in resp.get("items", []):
            found = True
            print(f"- Chapter ID: {item['id']} | Title: {item['title']} | Status: {item.get('status')} | Words: {item.get('word_count')}")
            if item.get("word_count", 0) > 0:
                print(  item.get('content', '')[:100] + "...\n")
                
        if not found:
            print("No chapters found in this project.")
            
    except Exception as e:
        print(f"Failed to fetch chapters: {e}")

if __name__ == "__main__":
    main()
