import io
import pathlib
import sys
import unittest
from contextlib import redirect_stdout
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

import bind_project
import analyze_chapter
import check_batch_status
import check_foreshadows
import fetch_unaudited
import generate_outline
import manage_memory
import materialize_outlines
import trigger_batch


class WorkflowSemanticsTests(unittest.TestCase):
    def test_analyze_chapter_extracts_nested_analysis_schema(self):
        payload = {
            "analysis": {
                "overall_quality_score": 88,
                "coherence_score": 84,
                "engagement_score": 90,
                "pacing_score": 82,
                "analysis_report": "章节整体完成度较高。",
                "suggestions": ["压缩一处解释"],
                "hooks": [{"content": "钟声来源"}],
                "foreshadows": [{"content": "木签异样"}],
            }
        }

        report = analyze_chapter.extract_report_fields(payload)

        self.assertEqual(report["overall_quality_score"], 88)
        self.assertEqual(report["coherence_score"], 84)
        self.assertEqual(report["engagement_score"], 90)
        self.assertEqual(report["pacing_score"], 82)
        self.assertEqual(report["analysis_report"], "章节整体完成度较高。")

    def test_analyze_chapter_summary_uses_new_score_fields(self):
        report = {
            "overall_quality_score": 88,
            "coherence_score": 84,
            "engagement_score": 90,
            "pacing_score": 82,
        }

        summary = analyze_chapter.build_score_summary(report)

        self.assertIn("Overall(88)", summary)
        self.assertIn("Coherence(84)", summary)
        self.assertIn("Engagement(90)", summary)
        self.assertIn("Pacing(82)", summary)

    def test_analyze_chapter_falls_back_to_legacy_top_level_schema(self):
        payload = {
            "overall_quality_score": 76,
            "coherence_score": 71,
            "engagement_score": 80,
            "pacing_score": 74,
            "comprehensive_review": "旧接口兼容输出。",
        }

        report = analyze_chapter.extract_report_fields(payload)

        self.assertEqual(report["overall_quality_score"], 76)
        self.assertEqual(report["analysis_report"], "旧接口兼容输出。")

    def test_fetch_unaudited_filters_review_candidates(self):
        items = [
            {"id": "c1", "title": "第1章", "status": "completed", "word_count": 2200},
            {"id": "c2", "title": "第2章", "status": "draft", "word_count": 1800},
            {"id": "c3", "title": "第3章", "status": "pending", "word_count": 0},
        ]

        review_items = fetch_unaudited.select_review_candidates(items)

        self.assertEqual([item["id"] for item in review_items], ["c1", "c2"])

    def test_generate_outline_error_message_uses_detail_when_content_missing(self):
        payload = {"type": "error", "detail": "provider timeout"}

        message = generate_outline.extract_error_message(payload)

        self.assertEqual(message, "provider timeout")

    def test_fetch_unaudited_summary_mentions_scope(self):
        items = [
            {"id": "c1", "title": "第1章", "status": "completed", "word_count": 2200},
            {"id": "c2", "title": "第2章", "status": "draft", "word_count": 1800},
        ]

        summary = fetch_unaudited.build_review_summary(items)

        self.assertIn("review candidates", summary.lower())
        self.assertIn("full chapter list", summary.lower())

    def test_pending_foreshadow_empty_message_explains_query_scope(self):
        message = check_foreshadows.render_empty_pending_message()

        self.assertIn("pending-resolve", message)
        self.assertIn("newly added foreshadows", message.lower())

    def test_batch_blocker_explains_missing_outline_materialization_step(self):
        project = {"wizard_status": "completed", "wizard_step": 4}

        blocker = trigger_batch.get_batch_blocker(project, [])

        self.assertIn("chapter slots", blocker.lower())
        self.assertIn("materialize_outlines.py", blocker)

    def test_materialize_outlines_filters_only_missing_chapter_slots(self):
        outlines = [
            {"id": "o2", "title": "第二卷", "has_chapters": False, "order_index": 2},
            {"id": "o1", "title": "第一卷", "has_chapters": True, "order_index": 1},
            {"id": "o3", "title": "第三卷", "order_index": 3},
        ]

        selected = materialize_outlines.select_outlines_to_materialize(outlines)

        self.assertEqual([item["id"] for item in selected], ["o2", "o3"])

    def test_materialize_outlines_limit_restricts_scope(self):
        outlines = [
            {"id": "o1", "title": "第一卷", "has_chapters": False, "order_index": 1},
            {"id": "o2", "title": "第二卷", "has_chapters": False, "order_index": 2},
            {"id": "o3", "title": "第三卷", "has_chapters": False, "order_index": 3},
        ]

        selected = materialize_outlines.select_outlines_to_materialize(outlines, limit=1)

        self.assertEqual([item["id"] for item in selected], ["o1"])

    def test_materialize_outlines_builds_batch_expand_payload(self):
        payload = materialize_outlines.build_batch_expand_payload(
            project_id="project-1",
            outline_ids=["o1", "o2"],
            chapters_per_outline=3,
            expansion_strategy="balanced",
        )

        self.assertEqual(payload["project_id"], "project-1")
        self.assertEqual(payload["outline_ids"], ["o1", "o2"])
        self.assertEqual(payload["chapters_per_outline"], 3)
        self.assertEqual(payload["expansion_strategy"], "balanced")
        self.assertFalse(payload["auto_create_chapters"])

    def test_batch_status_summary_reports_progress(self):
        payload = {
            "batch_id": "batch-1",
            "status": "running",
            "total": 3,
            "completed": 1,
            "current_chapter_number": 2,
            "current_retry_count": 0,
            "max_retries": 3,
            "failed_chapters": [],
            "error_message": None,
        }

        summary = check_batch_status.build_status_summary(payload)

        self.assertIn("running", summary.lower())
        self.assertIn("1/3", summary)
        self.assertIn("chapter 2", summary.lower())

    def test_trigger_batch_terminal_status_detection(self):
        self.assertFalse(trigger_batch.is_terminal_batch_status({"status": "running"}))
        self.assertTrue(trigger_batch.is_terminal_batch_status({"status": "completed"}))
        self.assertTrue(trigger_batch.is_terminal_batch_status({"status": "failed"}))

    def test_trigger_batch_wait_summary_mentions_progress(self):
        payload = {
            "batch_id": "batch-1",
            "status": "running",
            "total": 2,
            "completed": 1,
            "current_chapter_number": 2,
        }

        summary = trigger_batch.build_batch_wait_summary(payload)

        self.assertIn("running", summary.lower())
        self.assertIn("1/2", summary)
        self.assertIn("chapter 2", summary.lower())

    def test_trigger_batch_timeout_message_guides_status_check(self):
        message = trigger_batch.build_wait_timeout_message("batch-1", 180)

        self.assertIn("180", message)
        self.assertIn("check_batch_status.py", message)
        self.assertIn("batch-1", message)

    def test_manage_memory_success_message_mentions_pending_resolve_gap(self):
        message = manage_memory.build_add_foreshadow_success_message()

        self.assertIn("pending-resolve", message)
        self.assertIn("not appear immediately", message.lower())

    def test_status_payload_includes_runtime_snapshot_when_present(self):
        project = {
            "id": "project-1",
            "title": "Test",
            "wizard_status": "incomplete",
            "wizard_step": 2,
        }
        runtime_snapshot = {
            "status": "running",
            "phase": "characters",
            "subphase": "generating",
            "last_message": "角色信息补全中...",
            "last_progress": 65,
        }

        payload = bind_project.build_status_payload(project, runtime_snapshot)

        self.assertEqual(payload["runtime_status"], "running")
        self.assertEqual(payload["runtime_subphase"], "generating")
        self.assertEqual(payload["runtime_message"], "角色信息补全中...")
        self.assertEqual(payload["recommended_command"], "advance")

    def test_wait_timeout_uses_advance_style_output_when_runtime_exists(self):
        project = {
            "id": "project-1",
            "title": "Test",
            "wizard_status": "incomplete",
            "wizard_step": 2,
        }
        runtime_snapshot = {
            "status": "running",
            "phase": "characters",
            "subphase": "generating",
            "last_message": "角色信息补全中...",
            "last_progress": 65,
        }

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            fake_client = object()
            with mock.patch.object(bind_project, "fetch_project", return_value=project):
                with mock.patch.object(bind_project, "load_runtime_snapshot", return_value=runtime_snapshot):
                    with mock.patch.object(bind_project, "MumuClient", return_value=fake_client):
                        with mock.patch.object(bind_project.time, "monotonic", side_effect=[0, 1]):
                            args = [
                                "bind_project.py",
                                "--action",
                                "wait",
                                "--project_id",
                                "project-1",
                                "--timeout",
                                "0",
                                "--interval",
                                "0",
                                "--json",
                            ]
                            with mock.patch.object(sys, "argv", args):
                                bind_project.main()

        output = stdout.getvalue()
        self.assertIn('"subphase": "generating"', output)
        self.assertIn('"message": "角色信息补全中..."', output)


if __name__ == "__main__":
    unittest.main()
