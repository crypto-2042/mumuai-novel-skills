import argparse
import os
from client import MumuClient

def main():
    parser = argparse.ArgumentParser(description="Audit/Approve/Rewrite a generated chapter")
    parser.add_argument("--action", choices=["approve", "rewrite"], required=True, help="Action to perform")
    parser.add_argument("--chapter_id", type=str, required=True, help="The Chapter ID to act upon")
    parser.add_argument("--file", type=str, help="Path to a text file containing the rewritten content (for rewrite action)")
    
    args = parser.parse_args()
    client = MumuClient()
    
    if args.action == "approve":
        print(f"Approving chapter {args.chapter_id}...")
        try:
            client.put(f"chapters/{args.chapter_id}", json_data={"status": "published"})
            print("✅ Chapter is now PUBLISHED and will be hidden from the unaudited inbox.")
        except Exception as e:
            print(f"Failed to approve chapter: {e}")
            
    elif args.action == "rewrite":
        if not args.file or not os.path.exists(args.file):
            print("❌ Error: --file must point to a valid text file containing the new chapter text.")
            return
            
        with open(args.file, "r", encoding="utf-8") as f:
            new_text = f.read()
            
        print(f"Submitting heavily edited rewrite for chapter {args.chapter_id} (Words: {len(new_text)})...")
        try:
            client.put(f"chapters/{args.chapter_id}", json_data={"content": new_text, "status": "published"})
            print("✅ Chapter successfully overwritten and PUBLISHED!")
        except Exception as e:
            print(f"Failed to rewrite chapter: {e}")

if __name__ == "__main__":
    main()
