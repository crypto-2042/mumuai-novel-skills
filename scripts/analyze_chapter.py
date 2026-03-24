import time
import argparse
from client import MumuClient

def main():
    parser = argparse.ArgumentParser(description="Trigger System RAG Analysis for a chapter")
    parser.add_argument("--chapter_id", required=True, help="Chapter ID to analyze")
    
    args = parser.parse_args()
    client = MumuClient()
    
    print(f"Triggering RAG analysis for chapter {args.chapter_id} in project {client.project_id}...")
    
    try:
        # Trigger Analysis
        client.post(f"chapters/{args.chapter_id}/analyze")
        
        # Poll for completion
        print("Waiting for RAG analysis to complete...")
        while True:
            status_resp = client.get(f"chapters/{args.chapter_id}/analysis/status")
            if status_resp.get("status") in ["completed", "failed", "none"]:
                break
            time.sleep(3)
            
        # Fetch the actual report
        report_resp = client.get(f"chapters/{args.chapter_id}/analysis")
        print("\n=== SYSTEM RAG ANALYSIS REPORT ===")
        print(f"Scores: Plot({report_resp.get('plot_consistency_score')}) | Character({report_resp.get('character_consistency_score')}) | Writing({report_resp.get('writing_quality_score')})")
        print(report_resp.get('comprehensive_review', 'No comprehensive review returned.'))
        print("==================================")
        print("Note: If the report shows inconsistencies or missing plot goals, use rewrite_chapter.py")
    except Exception as e:
        print(f"Analysis failed: {e}")

if __name__ == "__main__":
    main()
