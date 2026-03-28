import json
import argparse
import sys
import time
from client import MumuClient

WIZARD_STAGES = {
    0: "world_building",
    1: "career_system",
    2: "characters",
    3: "outline",
}


def build_outline_payload(project):
    payload = {
        "project_id": project["id"],
        "narrative_perspective": project.get("narrative_perspective") or "第三人称",
    }
    return payload


def get_wizard_stage_label(project):
    if is_project_ready(project):
        return "completed"
    step = int(project.get("wizard_step") or 0)
    return WIZARD_STAGES.get(step, "unknown")


def is_project_ready(project):
    status = (project.get("wizard_status") or "").lower()
    step = int(project.get("wizard_step") or 0)
    return status == "completed" and step >= 4


def get_next_wizard_action(project):
    if is_project_ready(project):
        return None

    step = int(project.get("wizard_step") or 0)
    if step <= 1:
        return "career-system"
    if step == 2:
        return "characters"
    if step in (2, 3):
        return "outline"
    return None


def emit_project_status(project, json_mode=False):
    payload = {
        "project_id": project.get("id"),
        "title": project.get("title"),
        "wizard_status": project.get("wizard_status"),
        "wizard_step": project.get("wizard_step"),
        "stage": get_wizard_stage_label(project),
        "ready": is_project_ready(project),
        "next_action": get_next_wizard_action(project),
    }
    if json_mode:
        print(json.dumps(payload, ensure_ascii=False))
        return

    print("=== Project Status ===")
    for key, value in payload.items():
        print(f"{key}: {value}")
    print("======================")


def wait_for_sse(resp, step_name):
    print(f"--- Running: {step_name} ---")
    final_result = None
    chunk_count = 0
    try:
        for line in resp.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith("data: "):
                    try:
                        payload = json.loads(decoded[6:])
                        ptype = payload.get("type")
                        if ptype == "progress":
                            message = payload.get("message")
                            progress = payload.get("progress")
                            if message:
                                print(f"[{progress}%] {message}")
                        elif ptype == "chunk":
                            chunk_count += 1
                            if chunk_count % 100 == 0:
                                print(f"[stream] received {chunk_count} content chunks...")
                        elif ptype == "error":
                            print(f"❌ Error during {step_name}: {payload.get('error')}")
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


def fetch_project(client, project_id):
    return client.get(f"projects/{project_id}")


def run_world_building_stage(client, args):
    data = {
        "title": args.title,
        "description": args.description,
        "theme": args.theme,
        "genre": args.genre,
        "narrative_perspective": "第三人称",
        "target_words": 1000000,
        "chapter_count": 5,
        "character_count": 5,
        "outline_mode": "one-to-many",
    }
    resp = client.post("wizard-stream/world-building", json_data=data, stream=True)
    result = wait_for_sse(resp, "World Building")
    new_id = result.get("project_id") if result else None
    if not new_id:
        raise RuntimeError("Failed to get project_id from World Building")
    client.set_project_id(new_id)
    return fetch_project(client, new_id)


def run_next_stage(client, project, theme=None, genre=None):
    project_id = project["id"]
    next_action = get_next_wizard_action(project)
    if not next_action:
        return project

    if next_action == "career-system":
        resp = client.post("wizard-stream/career-system", json_data={"project_id": project_id}, stream=True)
        wait_for_sse(resp, "Career System")
    elif next_action == "characters":
        resp = client.post(
            "wizard-stream/characters",
            json_data={
                "project_id": project_id,
                "count": 5,
                "theme": theme or project.get("theme"),
                "genre": genre or project.get("genre"),
            },
            stream=True,
        )
        wait_for_sse(resp, "Characters")
    elif next_action == "outline":
        resp = client.post(
            "wizard-stream/outline",
            json_data=build_outline_payload(project),
            stream=True,
        )
        wait_for_sse(resp, "Outline")
    else:
        raise RuntimeError(f"Unknown wizard action: {next_action}")

    return fetch_project(client, project_id)

def main():
    parser = argparse.ArgumentParser(description="Bind or Create a Novel Project")
    parser.add_argument("--action", required=True, choices=["create", "status", "wait", "resume", "ready", "list", "bind", "list-styles", "bind-style"], help="Action: manage projects or bind writing styles")
    parser.add_argument("--title", type=str, help="Title of the new novel (for create)")
    parser.add_argument("--description", type=str, help="Description/Synopsis of the novel (for create)")
    parser.add_argument("--theme", type=str, help="Theme of the novel (for create) e.g. 奋斗、复仇")
    parser.add_argument("--genre", type=str, help="Genre of the novel (for create) e.g. 科幻、修仙")
    parser.add_argument("--project_id", type=str, help="The project ID to bind (for bind)")
    parser.add_argument("--style_id", type=str, help="The writing style ID to bind (for bind-style)")
    parser.add_argument("--timeout", type=int, default=300, help="Maximum seconds to wait when using wait")
    parser.add_argument("--interval", type=int, default=5, help="Polling interval in seconds for wait")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON for status-style actions")
    
    args = parser.parse_args()
    client = MumuClient(project_id=getattr(args, 'project_id', None), style_id=getattr(args, 'style_id', None))
    
    if args.action == "create":
        if not args.title or not args.theme or not args.genre or not args.description:
            print("Error: --title, --description, --theme, and --genre are all required for create action.")
            return
        print(f"Creating a new project: {args.title} and starting the first initialization stage...")
        try:
            project = run_world_building_stage(client, args)
            print(f"Project created with ID: {project.get('id')}")
            print("World building finished. Use `--action resume --project_id <ID>` to continue the next stage, or `--action status` to inspect progress.")
            emit_project_status(project, json_mode=args.json)
        except Exception as e:
            print(f"Failed to create project: {e}")

    elif args.action == "status":
        if not args.project_id:
            print("Error: --project_id is required for status action.")
            return
        try:
            emit_project_status(fetch_project(client, args.project_id), json_mode=args.json)
        except Exception as e:
            print(f"Failed to fetch project status: {e}")

    elif args.action == "wait":
        if not args.project_id:
            print("Error: --project_id is required for wait action.")
            return
        deadline = time.monotonic() + args.timeout
        try:
            while True:
                project = fetch_project(client, args.project_id)
                if is_project_ready(project):
                    emit_project_status(project, json_mode=args.json)
                    return
                if time.monotonic() >= deadline:
                    print(f"Initialization is still in progress after {args.timeout} seconds.")
                    emit_project_status(project, json_mode=args.json)
                    return
                time.sleep(args.interval)
        except Exception as e:
            print(f"Failed while waiting for project readiness: {e}")

    elif args.action == "resume":
        if not args.project_id:
            print("Error: --project_id is required for resume action.")
            return
        try:
            project = fetch_project(client, args.project_id)
            if is_project_ready(project):
                print("Project initialization is already complete.")
                emit_project_status(project, json_mode=args.json)
                return
            print(f"Resuming initialization for project {args.project_id} from stage {get_wizard_stage_label(project)}...")
            project = run_next_stage(client, project, theme=args.theme, genre=args.genre)
            emit_project_status(project, json_mode=args.json)
        except Exception as e:
            print(f"Failed to resume initialization: {e}")

    elif args.action == "ready":
        if not args.project_id:
            print("Error: --project_id is required for ready action.")
            return
        try:
            project = fetch_project(client, args.project_id)
            if args.json:
                print(json.dumps({"project_id": args.project_id, "ready": is_project_ready(project)}, ensure_ascii=False))
            else:
                print("READY" if is_project_ready(project) else "NOT_READY")
        except Exception as e:
            print(f"Failed to check project readiness: {e}")
            
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
