import unittest
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

import bind_project
import client as mumu_client


class BindProjectWizardStateTests(unittest.TestCase):
    def test_incomplete_project_reports_next_step(self):
        project = {"wizard_status": "incomplete", "wizard_step": 1}

        self.assertFalse(bind_project.is_project_ready(project))
        self.assertEqual(bind_project.get_next_wizard_action(project), "career-system")
        self.assertEqual(bind_project.get_wizard_stage_label(project), "career_system")

    def test_midway_project_resumes_outline(self):
        project = {"wizard_status": "incomplete", "wizard_step": 3}

        self.assertFalse(bind_project.is_project_ready(project))
        self.assertEqual(bind_project.get_next_wizard_action(project), "outline")
        self.assertEqual(bind_project.get_wizard_stage_label(project), "outline")

    def test_outline_resume_uses_backend_init_defaults(self):
        project = {
            "id": "project-1",
            "wizard_status": "incomplete",
            "wizard_step": 3,
            "narrative_perspective": "第三人称",
            "target_words": 1000000,
            "chapter_count": 5,
        }

        payload = bind_project.build_outline_payload(project)

        self.assertEqual(
            payload,
            {
                "project_id": "project-1",
                "narrative_perspective": "第三人称",
            },
        )

    def test_completed_project_is_ready(self):
        project = {"wizard_status": "completed", "wizard_step": 4}

        self.assertTrue(bind_project.is_project_ready(project))
        self.assertIsNone(bind_project.get_next_wizard_action(project))
        self.assertEqual(bind_project.get_wizard_stage_label(project), "completed")

    def test_stream_requests_disable_read_timeout(self):
        timeout = mumu_client.get_request_timeout(stream=True)

        self.assertEqual(timeout, (mumu_client.DEFAULT_TIMEOUT, None))


if __name__ == "__main__":
    unittest.main()
