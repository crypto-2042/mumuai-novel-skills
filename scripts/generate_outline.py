import json
import argparse
from client import MumuClient

def main():
    parser = argparse.ArgumentParser(description="Trigger AI Outline Generation")
    parser.add_argument("--count", type=int, default=5, help="Number of chapters to outline")
    parser.add_argument("--mode", type=str, default="auto", choices=["auto", "new", "continue"])
    
    args = parser.parse_args()
    client = MumuClient()
    
    print(f"Triggering outline generation ({args.mode}) for {args.count} chapters on project {client.project_id}...")
    try:
        data = {
            "project_id": client.project_id,
            "chapter_count": args.count,
            "mode": args.mode
        }
        resp = client.post("outlines/generate-stream", json_data=data, stream=True)
        print("Waiting for outline generation to complete (this may take a few minutes)...")
        
        final_result = None
        for line in resp.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith("data: "):
                    try:
                        payload = json.loads(decoded[6:])
                        if payload.get("type") == "parsing":
                            print(f"[Agent Status] {payload.get('content')}")
                        elif payload.get("type") == "saving":
                            print(f"[Agent Status] {payload.get('content')}")
                        elif payload.get("type") == "error":
                            print(f"❌ Error: {payload.get('content')}")
                            return
                        elif payload.get("type") == "result":
                            final_result = payload.get("data")
                    except:
                        pass
                        
        print("\n=== OUTLINE GENERATION REPORT ===")
        if final_result:
            print(f"Total new chapters outlined: {final_result.get('new_chapters', 0)}")
            print(f"Message: {final_result.get('message', '')}")
            print("Successfully expanded the novel's creative runway.")
            print("Use trigger_batch.py next to write the actual text!")
        else:
            print("Completed, but no final result payload was captured. Please check the MuMu console.")
            
    except Exception as e:
        print(f"Failed to generate outline: {e}")

if __name__ == "__main__":
    main()
