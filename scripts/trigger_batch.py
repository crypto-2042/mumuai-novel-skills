import argparse
from client import MumuClient

def main():
    parser = argparse.ArgumentParser(description="Trigger Batch Generation")
    parser.add_argument("--count", type=int, default=1, help="Number of chapters to generate")
    
    parser.add_argument("--project_id", type=str, help="The bound Novel Project ID (Required if not in env)")
    parser.add_argument("--style_id", type=str, help="The bound Style ID (Optional, overrides .env)")
    args = parser.parse_args()
    client = MumuClient(project_id=args.project_id, style_id=getattr(args, 'style_id', None))
    if not client.project_id:
        print("Error: --project_id argument is required or must be set in .env")
        return
    
    print(f"Detecting start chapter for project {client.project_id}...")
    try:
        chapters_resp = client.get(f"chapters/project/{client.project_id}", params={"limit": 1000})
        items = chapters_resp.get("items", [])
        start_num = None
        if not items:
            print("No existing chapters. Starting from Chapter 1.")
            start_num = 1
        else:
            for ch in items:
                print(f"Checking Chapter {ch.get('chapter_number')}: Words={ch.get('word_count')}, Status={ch.get('status')}")
                if ch.get("word_count", 0) == 0 or ch.get("status") == "draft":
                    start_num = ch.get("chapter_number")
                    break
                
        if start_num is None:
            print("❌ No empty draft chapters found in this project. All existing chapters seem to be completed.")
            return
            
        print(f"✅ Found empty draft at Chapter {start_num}. Starting batch generation for {args.count} chapters...")
        
        data = {
            "start_chapter_number": start_num,
            "count": args.count,
            "enable_analysis": True
        }
        if getattr(client, "style_id", None):
            data["style_id"] = client.style_id
            
        resp = client.post(f"chapters/project/{client.project_id}/batch-generate", json_data=data)
        print("Batch generation started successfully:")
        print(resp)
    except Exception as e:
        print(f"Failed to trigger batch generation: {e}")

if __name__ == "__main__":
    main()
