import argparse
from client import MumuClient

def main():
    parser = argparse.ArgumentParser(description="Trigger Batch Generation")
    parser.add_argument("--count", type=int, default=1, help="Number of chapters to generate")
    
    args = parser.parse_args()
    client = MumuClient()
    
    print(f"Detecting start chapter for project {client.project_id}...")
    try:
        chapters_resp = client.get(f"chapters/project/{client.project_id}", params={"limit": 1000})
        start_num = None
        for ch in chapters_resp.get("items", []):
            if ch.get("word_count", 0) == 0 or ch.get("status") == "draft":
                start_num = ch.get("chapter_number")
                break
                
        if start_num is None:
            print("❌ No empty draft chapters found in this project. You might need to generate or expand outlines first.")
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
