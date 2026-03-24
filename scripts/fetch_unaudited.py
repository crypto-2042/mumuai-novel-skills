import argparse
from client import MumuClient

def main():
    parser = argparse.ArgumentParser(description="Fetch Unaudited Chapters")
    args = parser.parse_args()
    client = MumuClient()
    
    print(f"Fetching recently generated (unaudited) chapters for project {client.project_id}...")
    
    try:
        resp = client.get(f"chapters/project/{client.project_id}", params={"limit": 100})
        print("Retrieved chapters needing your review:")
        
        found = False
        for item in resp.get("items", []):
            if item.get("status") == "draft" and item.get("word_count", 0) > 0:
                found = True
                print(f"- Chapter ID: {item['id']} | Title: {item['title']} | Words: {item.get('word_count')}")
                print(  item.get('content', '')[:300] + "...\n")
                
        if not found:
            print("No new generated chapters waiting for audit.")
            
    except Exception as e:
        print(f"Failed to fetch chapters: {e}")

if __name__ == "__main__":
    main()
