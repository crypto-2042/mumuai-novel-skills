import os
import json
import requests
from dotenv import load_dotenv, set_key
from pathlib import Path

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

MUMU_API_URL = os.getenv("MUMU_API_URL", "http://localhost:8000").rstrip("/")
MUMU_USERNAME = os.getenv("MUMU_USERNAME", "admin")
MUMU_PASSWORD = os.getenv("MUMU_PASSWORD", "admin123")

SESSION_FILE = Path(__file__).parent.parent / '.mumu_session.json'

class MumuClient:
    def __init__(self):
        self.session = requests.Session()
        
        load_dotenv(dotenv_path=env_path, override=True)
        self.project_id = os.getenv("MUMU_PROJECT_ID")
        self.style_id = os.getenv("MUMU_STYLE_ID")
        
        self._load_cookies()
        if not self._check_auth():
            self.login()
            
    def require_project_id(self):
        if not self.project_id:
            raise Exception("尚未绑定小说项目！请先运行 bind_project.py 进行存量绑定或新建小说。")
        return self.project_id

    def set_project_id(self, project_id: str):
        self.project_id = project_id
        if not env_path.exists():
            env_path.touch()
        set_key(dotenv_path=env_path, key_to_set="MUMU_PROJECT_ID", value_to_set=project_id)
        print(f"[System] MUMU_PROJECT_ID 已成功定格写入 .env -> {project_id}")

    def set_style_id(self, style_id: str):
        self.style_id = style_id
        if not env_path.exists():
            env_path.touch()
        set_key(dotenv_path=env_path, key_to_set="MUMU_STYLE_ID", value_to_set=style_id)
        print(f"[System] MUMU_STYLE_ID 写作风格已成功刻印至 .env -> {style_id}")

    def _load_cookies(self):
        if SESSION_FILE.exists():
            try:
                cookies_dict = json.loads(SESSION_FILE.read_text())
                self.session.cookies.update(cookies_dict)
            except Exception:
                pass

    def _save_cookies(self):
        cookies_dict = self.session.cookies.get_dict()
        SESSION_FILE.write_text(json.dumps(cookies_dict))

    def _check_auth(self):
        resp = self.session.get(f"{MUMU_API_URL}/api/users/me")
        return resp.status_code == 200

    def login(self):
        url = f"{MUMU_API_URL}/api/auth/local/login"
        data = {
            "username": MUMU_USERNAME,
            "password": MUMU_PASSWORD
        }
        resp = requests.post(url, json=data)
        if resp.status_code == 200:
            # 登录响应会在 Header 中包含 Set-Cookie
            self.session.cookies.update(resp.cookies)
            self._save_cookies()
            print("[System] 登录 MuMuAINovel 成功，已获取授权 Session Cookies。")
        else:
            raise Exception(f"登录失败: {resp.status_code} - {resp.text}")

    def get(self, endpoint, **kwargs):
        url = f"{MUMU_API_URL}/api/{endpoint.lstrip('/')}"
        resp = self.session.get(url, **kwargs)
        resp.raise_for_status()
        return resp.json()

    def post(self, endpoint, json_data=None, data=None, **kwargs):
        url = f"{MUMU_API_URL}/api/{endpoint.lstrip('/')}"
        resp = self.session.post(url, json=json_data, data=data, **kwargs)
        if kwargs.get('stream'):
            return resp
        resp.raise_for_status()
        return resp.json()

    def put(self, endpoint, json_data=None, data=None, **kwargs):
        url = f"{MUMU_API_URL}/api/{endpoint.lstrip('/')}"
        resp = self.session.put(url, json=json_data, data=data, **kwargs)
        resp.raise_for_status()
        return resp.json()

if __name__ == "__main__":
    client = MumuClient()
    print("Client Auth Status:", client._check_auth())
