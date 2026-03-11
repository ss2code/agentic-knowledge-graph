import unittest
import tempfile
import os
import json
from utils.context_scanner import (
    scan_contexts, load_artifact, load_llm_logs,
    get_last_run_time, load_graph_build_log
)

class TestScanContexts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)

    def _make_context(self, name, with_user_data=True):
        ctx_dir = os.path.join(self.tmp, name)
        os.makedirs(ctx_dir)
        if with_user_data:
            os.makedirs(os.path.join(ctx_dir, "user_data"))
        return ctx_dir

    def test_scan_contexts_finds_contexts_with_user_data(self):
        """scan_contexts returns contexts that have user_data/ subdir"""
        self._make_context("alpha")
        self._make_context("beta")
        result = scan_contexts(self.tmp)
        names = [r["name"] for r in result]
        self.assertIn("alpha", names)
        self.assertIn("beta", names)

    def test_scan_contexts_ignores_dirs_without_user_data(self):
        """scan_contexts skips dirs that have no user_data/ subdir"""
        self._make_context("has_data")
        self._make_context("no_data", with_user_data=False)
        result = scan_contexts(self.tmp)
        names = [r["name"] for r in result]
        self.assertIn("has_data", names)
        self.assertNotIn("no_data", names)

    def test_scan_contexts_returns_empty_for_missing_dir(self):
        result = scan_contexts("/nonexistent/path/xyz")
        self.assertEqual(result, [])

    def test_scan_contexts_sorted_by_name(self):
        for name in ["zebra", "apple", "mango"]:
            self._make_context(name)
        result = scan_contexts(self.tmp)
        names = [r["name"] for r in result]
        self.assertEqual(names, sorted(names))

    def test_load_artifact_returns_none_for_missing_file(self):
        ctx = self._make_context("myctx")
        result = load_artifact(ctx, "nonexistent.json")
        self.assertIsNone(result)

    def test_load_artifact_returns_dict(self):
        ctx = self._make_context("myctx")
        data = {"intent": "test", "primary_entities": ["A"]}
        with open(os.path.join(ctx, "user_intent.json"), "w") as f:
            json.dump(data, f)
        result = load_artifact(ctx, "user_intent.json")
        self.assertEqual(result["intent"], "test")

    def test_load_artifact_returns_none_for_bad_json(self):
        ctx = self._make_context("myctx")
        with open(os.path.join(ctx, "bad.json"), "w") as f:
            f.write("not json {{{{")
        result = load_artifact(ctx, "bad.json")
        self.assertIsNone(result)

class TestLlmLogs(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)

    def _write_log(self, filename, content="# Log content"):
        path = os.path.join(self.tmp, filename)
        with open(path, "w") as f:
            f.write(content)

    def test_load_llm_logs_parses_filename(self):
        """load_llm_logs extracts agent name and timestamp from filename"""
        self._write_log("debug_llm_IntentAgent_20260202_085255.md", "# Intent log")
        logs = load_llm_logs(self.tmp)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["agent"], "IntentAgent")
        self.assertEqual(logs[0]["timestamp"], "20260202_085255")

    def test_load_llm_logs_filters_by_prefix(self):
        self._write_log("debug_llm_IntentAgent_20260202_085255.md")
        self._write_log("debug_llm_NERAgent_20260202_090000.md")
        logs = load_llm_logs(self.tmp, agent_prefix="IntentAgent")
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["agent"], "IntentAgent")

    def test_load_llm_logs_sorted_desc(self):
        """Newer logs (higher timestamp) come first"""
        self._write_log("debug_llm_IntentAgent_20260202_085255.md")
        self._write_log("debug_llm_IntentAgent_20260202_090000.md")
        logs = load_llm_logs(self.tmp)
        self.assertEqual(logs[0]["timestamp"], "20260202_090000")

    def test_load_llm_logs_returns_empty_for_missing_dir(self):
        logs = load_llm_logs("/nonexistent/path")
        self.assertEqual(logs, [])

    def test_get_last_run_time_returns_formatted_timestamp(self):
        self._write_log("debug_llm_IntentAgent_20260202_085255.md")
        result = get_last_run_time(self.tmp, "IntentAgent")
        self.assertEqual(result, "2026-02-02 08:52")

    def test_get_last_run_time_returns_none_for_missing(self):
        result = get_last_run_time(self.tmp, "NonExistentAgent")
        self.assertIsNone(result)

    def test_load_graph_build_log_returns_content(self):
        log_path = os.path.join(self.tmp, "graph_build_log.md")
        with open(log_path, "w") as f:
            f.write("# Build Log\n## Step 1\nDone.")
        content = load_graph_build_log(self.tmp)
        self.assertIn("Build Log", content)

    def test_load_graph_build_log_returns_none_when_missing(self):
        result = load_graph_build_log(self.tmp)
        self.assertIsNone(result)
