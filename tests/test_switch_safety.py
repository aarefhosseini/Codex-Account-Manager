import datetime as dt
import io
import json
import plistlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from codex_account_manager import cli, desktop, continuation
from codex_account_manager.subscriptions import purchase_date, subscription_info


class SubscriptionTests(unittest.TestCase):
    def test_period_is_30_days_across_month_and_year_boundaries(self):
        info = subscription_info("2026-12-15", today=dt.date(2026, 12, 20))
        self.assertEqual(info["expires_at"], "2027-01-14")
        self.assertEqual(info["days_remaining"], 25)
        self.assertEqual(subscription_info("2024-02-01")["expires_at"], "2024-03-02")

    def test_unknown_date_is_not_inferred_and_expiry_boundary_is_expired(self):
        self.assertEqual(subscription_info(None)["status"], "unknown")
        info = subscription_info("2026-10-15", today=dt.date(2026, 11, 14))
        self.assertEqual(info["status"], "expired")
        self.assertEqual(info["days_remaining"], 0)
        for value in ("2026-02-30", "20261114", "14/11/2026", 1):
            with self.assertRaises(ValueError):
                purchase_date(value)


class DesktopTests(unittest.TestCase):
    def test_process_tree_includes_helpers_and_excludes_manager_and_cli(self):
        app = desktop.DesktopApp("/Applications/ChatGPT.app/Contents/MacOS/ChatGPT", "/Applications/ChatGPT.app")
        rows = [
            {"pid": 101, "ppid": 1, "executable": app.executable},
            {"pid": 102, "ppid": 101, "executable": app.bundle + "/Contents/Frameworks/Helper"},
            {"pid": 103, "ppid": 102, "executable": "/opt/codex/app-server"},
            {"pid": 104, "ppid": 1, "executable": "/opt/codex/cli"},
            {"pid": 105, "ppid": 1, "executable": "/Applications/Codex Account Manager.app/Contents/MacOS/Codex Account Manager"},
        ]
        self.assertEqual([r["pid"] for r in desktop.desktop_processes(rows, [app], "darwin")], [101, 102, 103])

    def test_renamed_macos_app_is_discovered_by_bundle_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            bundle = Path(temp) / "ChatGPT.app"
            (bundle / "Contents/MacOS").mkdir(parents=True)
            (bundle / "Contents/MacOS/ChatGPT").touch()
            info = {"CFBundleIdentifier": "com.openai.codex", "CFBundleExecutable": "ChatGPT"}
            (bundle / "Contents/Info.plist").write_bytes(plistlib.dumps(info))
            self.assertIn(desktop.DesktopApp(str(bundle / "Contents/MacOS/ChatGPT"), str(bundle)), desktop.discover_macos_apps(bundle))

    def test_process_inspection_failure_is_not_reported_as_closed(self):
        with self.assertRaises(RuntimeError):
            desktop.process_snapshot(mock.Mock(return_value=mock.Mock(returncode=1)), "darwin")

    @mock.patch("codex_account_manager.desktop.time.sleep")
    @mock.patch("codex_account_manager.desktop.os.kill")
    def test_orphaned_children_must_exit_before_stop_returns(self, kill, _sleep):
        app = desktop.DesktopApp("/tmp/Codex")
        parent = {"pid": 101, "ppid": 1, "executable": app.executable}
        child = {"pid": 102, "ppid": 101, "executable": "/tmp/helper"}
        orphan = {**child, "ppid": 1}
        with mock.patch.object(desktop, "process_snapshot", side_effect=[[parent, child], *[[orphan]] * 31, []]):
            desktop.stop_apps([app], platform="linux")
        self.assertIn(mock.call(102, desktop.signal.SIGKILL), kill.call_args_list)

    @mock.patch("codex_account_manager.desktop.time.sleep")
    @mock.patch("codex_account_manager.desktop.os.kill")
    def test_stop_fails_when_process_survives(self, _kill, _sleep):
        app = desktop.DesktopApp("/tmp/Codex")
        with mock.patch.object(desktop, "process_snapshot", return_value=[{"pid": 101, "ppid": 1, "executable": app.executable}]):
            with self.assertRaisesRegex(RuntimeError, "still running"):
                desktop.stop_apps([app], platform="linux")

    def test_resume_uses_current_owner_and_ignores_other_accounts_and_invalid_ids(self):
        first = "01a1dba5-094f-7de0-aebf-226e9316d8da"
        second = "01a1db8c-093d-7dc0-a965-001c66fa0f07"
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            state = {"electron-renderer-content-owner": "current",
                     "electron-owner-atoms:current": {"thread-user-activity-times-v1": {f"local:{first}": 123, "cloud:other": 999}},
                     "electron-owner-atoms:other": {"thread-user-activity-times-v1": {second: 999}}}
            (home / ".codex-global-state.json").write_text(json.dumps(state))
            self.assertEqual(desktop.last_thread_url(home), f"codex://threads/{first}")
            self.assertEqual(json.loads((home / ".codex-global-state.json").read_text()), state)

    def test_current_desktop_json_identity_selects_only_local_chats(self):
        thread = "01a1dba5-094f-7de0-aebf-226e9316d8da"
        other = "01a1db8c-093d-7dc0-a965-001c66fa0f07"
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            state = {"electron-renderer-content-owner": "current", "electron-owner-atoms:current": {
                "thread-user-activity-times-v1": {json.dumps(["local", thread]): 123, json.dumps(["ssh:remote", other]): 999}
            }}
            (home / ".codex-global-state.json").write_text(json.dumps(state))
            self.assertEqual(desktop.last_thread_url(home), f"codex://threads/{thread}")


class ContinuationTests(unittest.TestCase):
    thread_id = "01a1dba5-094f-7de0-aebf-226e9316d8da"

    def test_queue_targets_exact_chat_with_resume_and_preserves_codex_home(self):
        run = mock.Mock(return_value=mock.Mock(returncode=0, stdout="Queued message 123 for thread " + self.thread_id, stderr=""))
        continuation.continue_thread("/tmp/codex", self.thread_id, Path("/tmp/test-home"), run=run)
        command = run.call_args.args[0]
        self.assertEqual(command[:5], ["/tmp/codex", "queue", "--thread", self.thread_id, "--message"])
        self.assertEqual(command[-1], "--resume")
        self.assertEqual(run.call_args.kwargs["env"]["CODEX_HOME"], "/tmp/test-home")
        run.assert_called_once()

    def test_resume_warning_is_not_success_and_does_not_send_twice(self):
        run = mock.Mock(return_value=mock.Mock(returncode=0, stdout="Queued message", stderr="Warning: message was queued, but could not resume thread"))
        with self.assertRaisesRegex(RuntimeError, "was queued"):
            continuation.continue_thread("codex", self.thread_id, Path("/tmp/test-home"), run=run)
        run.assert_called_once()

    def test_queue_timeout_is_ambiguous_and_never_retried(self):
        import subprocess
        run = mock.Mock(side_effect=subprocess.TimeoutExpired("codex", 15))
        with self.assertRaisesRegex(RuntimeError, "unknown"):
            continuation.continue_thread("codex", self.thread_id, Path("/tmp/test-home"), run=run)
        run.assert_called_once()


class SwitchSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.paths = mock.patch.multiple(cli, CODEX_HOME=root, AUTH_FILE=root / "auth.json", PROFILES_DIR=root / "profiles",
                                        BACKUPS_DIR=root / "backups", PROFILE_HOMES_DIR=root / "homes", CAM_DIR=root / "manager",
                                        CAM_CONFIG_FILE=root / "manager/config.json", CAM_LOG_FILE=root / "manager/ui.log")
        self.paths.start()
        cli.ensure_dirs()
        self.old = {"tokens": {"access_token": "old", "account_id": "old-id"}}
        self.target = {"tokens": {"access_token": "new", "account_id": "new-id"}}
        cli.atomic_write_json(cli.AUTH_FILE, self.old)
        cli.atomic_write_json(cli.PROFILES_DIR / "work/auth.json", self.target)
        cli.atomic_write_json(cli.PROFILES_DIR / "work/meta.json", {"name": "work", "saved_at": "2026-09-01", "purchased_at": "2026-10-25"})
        self.app = desktop.DesktopApp("/tmp/Codex")
        self.stack = mock.patch.object(cli, "_desktop_apps", return_value=[self.app])
        self.stack.start()
        self.snapshots = mock.patch.object(desktop, "process_snapshot", return_value=[])
        self.snapshots.start()
        self.refresh = mock.patch.object(cli, "refresh_and_sync_live_auth_snapshot", return_value=True)
        self.refresh.start()

    def tearDown(self):
        self.refresh.stop()
        self.snapshots.stop()
        self.stack.stop()
        self.paths.stop()
        self.temp.cleanup()

    def test_failed_stop_keeps_old_credentials_and_never_launches(self):
        with mock.patch.object(desktop, "stop_apps", side_effect=RuntimeError("still running")), mock.patch.object(desktop, "start_app") as start:
            self.assertEqual(cli.cmd_switch("work", True), 1)
        self.assertEqual(cli.load_json(cli.AUTH_FILE), self.old)
        start.assert_not_called()

    def test_order_is_stop_then_write_then_start_and_backup_is_private(self):
        def stop(*args, **kwargs):
            self.assertEqual(cli.load_json(cli.AUTH_FILE), self.old)
        def start(*args, **kwargs):
            self.assertEqual(cli.load_json(cli.AUTH_FILE), self.target)
        with mock.patch.object(desktop, "stop_apps", side_effect=stop), mock.patch.object(desktop, "start_app", side_effect=start) as launched:
            self.assertEqual(cli.cmd_switch("work", True), 0)
        launched.assert_called_once()
        backups = list(cli.BACKUPS_DIR.glob("auth-*.json"))
        self.assertEqual(cli.load_json(backups[0]), self.old)
        self.assertEqual(cli.AUTH_FILE.stat().st_mode & 0o777, 0o600)

    def test_restart_failure_reports_account_was_changed(self):
        output = io.StringIO()
        with mock.patch.object(desktop, "stop_apps"), mock.patch.object(desktop, "start_app", side_effect=RuntimeError("launch failed")), mock.patch("sys.stdout", output):
            self.assertEqual(cli.cmd_switch("work", True), 1)
        self.assertIn("Account changed to 'work'", output.getvalue())
        self.assertEqual(cli.load_json(cli.AUTH_FILE), self.target)

    def test_atomic_write_failure_restores_previous_credentials(self):
        original = cli.atomic_write_json
        def write(path, data):
            if path == cli.AUTH_FILE and data == self.target:
                raise PermissionError("locked")
            return original(path, data)
        with mock.patch.object(cli, "atomic_write_json", side_effect=write):
            self.assertEqual(cli.cmd_switch("work", False), 1)
        self.assertEqual(cli.load_json(cli.AUTH_FILE), self.old)

    def test_purchase_date_survives_relogin_and_is_exposed_in_list(self):
        source = Path(self.temp.name) / "relogin.json"
        cli.atomic_write_json(source, self.target)
        cli.write_profile("work", source, "test", overwrite=True)
        meta = cli.load_json(cli.PROFILES_DIR / "work/meta.json")
        self.assertEqual(meta["purchased_at"], "2026-10-25")
        self.assertEqual(meta["saved_at"], "2026-09-01")
        self.assertEqual(cli.collect_list_data()[0]["subscription"]["expires_at"], "2026-11-24")

    def test_invalid_profile_names_cannot_escape_profile_directory(self):
        for name in ("../work", "..", "/tmp/account", "a\\b"):
            self.assertEqual(cli.cmd_switch(name, False), 1)

    def test_missing_previous_chat_aborts_before_closing_or_changing_account(self):
        with mock.patch.object(desktop, "stop_apps") as stop:
            self.assertEqual(cli.cmd_switch("work", True, resume_work=True), 1)
        stop.assert_not_called()
        self.assertEqual(cli.load_json(cli.AUTH_FILE), self.old)

    def test_unexpected_identity_after_refresh_restores_old_account(self):
        def wrong_identity(*args, **kwargs):
            cli.atomic_write_json(cli.AUTH_FILE, {"tokens": {"account_id": "unexpected", "access_token": "unexpected"}})
        with mock.patch.object(cli, "refresh_and_sync_live_auth_snapshot", side_effect=wrong_identity):
            self.assertEqual(cli.cmd_switch("work", False), 1)
        self.assertEqual(cli.load_json(cli.AUTH_FILE), self.old)

    def test_continuation_is_queued_only_after_relaunch(self):
        events = []
        url = "codex://threads/01a1dba5-094f-7de0-aebf-226e9316d8da"
        with mock.patch.object(desktop, "last_thread_url", return_value=url), \
             mock.patch.object(continuation, "find_resume_cli", return_value="/tmp/codex"), \
             mock.patch.object(cli, "resolve_codex_cli", return_value="/tmp/codex"), \
             mock.patch.object(desktop, "stop_apps", side_effect=lambda *a, **kw: events.append("stop")), \
             mock.patch.object(desktop, "start_app", side_effect=lambda *a, **kw: events.append("start")), \
             mock.patch.object(continuation, "continue_thread", side_effect=lambda *a, **kw: events.append("continue")):
            self.assertEqual(cli.cmd_switch("work", True, resume_work=True), 0)
        self.assertEqual(events, ["stop", "start", "continue"])
