import argparse
from client import MumuClient

def main():
    parser = argparse.ArgumentParser(description="Rewrite a chapter based on feedback")
    parser.add_argument("--chapter_id", required=True, help="Chapter ID")
    parser.add_argument("--feedback", required=True, help="Instructions on what to rewrite")
    
    args = parser.parse_args()
    client = MumuClient()
    
    print(f"Applying feedback to chapter {args.chapter_id} in project {client.project_id}: '{args.feedback}'")
    
    try:
        data = {"feedback": args.feedback, "mode": "full"}
        resp = client.post(f"chapters/{args.chapter_id}/regenerate-stream", json_data=data)
        print("Rewrite triggered successfully:")
        print(resp)
    except Exception as e:
        print(f"Rewrite failed: {e}")

if __name__ == "__main__":
    main()
