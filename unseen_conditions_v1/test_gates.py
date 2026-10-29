"""Metadata/control-flow checks only. No cell, device or statistical experiment."""
import contextlib
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import config as c
import study as s


class GateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.context = patch.object(c, 'ROOT', self.root)
        self.context.start()

    def tearDown(self):
        self.context.stop()
        self.temp.cleanup()

    def no_simulation(self, function):
        with patch.object(s.subprocess, 'run', side_effect=AssertionError('A simulator must not start')):
            with self.assertRaises(s.GateError):
                function()
        self.assertFalse((self.root/'runs').exists())
        self.assertFalse((self.root/'validation').exists())

    def test_missing_registration_is_closed(self):
        self.no_simulation(s.require_registration)

    def test_validate_cannot_start_without_registration(self):
        self.no_simulation(s.validate)

    def test_design_cannot_start_without_registration(self):
        self.no_simulation(s.design)

    def test_test_cannot_start_without_registration(self):
        self.no_simulation(s.test)

    def test_analysis_cannot_start_without_registration(self):
        self.no_simulation(s.analyze)

    def test_no_held_out_inputs_before_committed_selection(self):
        with patch.object(s, 'require_validation', return_value={}):
            self.no_simulation(s.test)

    def test_missing_build_is_closed(self):
        self.no_simulation(s.check_sources)

    def test_source_change_is_detected(self):
        (self.root/'source.txt').write_text('changed')
        s.write(self.root/'SOURCE_LOCK.json', dict(sources={'source.txt': '0'*64}, binaries={}))
        with self.assertRaises(s.GateError):
            s.check_sources()

    def test_unfilled_example_stays_closed(self):
        s.write(self.root/'registration.json', dict(protocol={}))
        with patch.object(s, 'check_sources', return_value='x'*64):
            with self.assertRaises(s.GateError):
                s.require_registration()

    def test_missing_selection_evidence_is_closed(self):
        with patch.object(s, 'require_validation', return_value={}):
            self.no_simulation(s.require_selection)

    def test_inference_requires_a_complete_test(self):
        with patch.object(s, 'require_selection', return_value={}):
            self.no_simulation(s.analyze)

    def test_build_does_not_replace_a_registered_implementation(self):
        (self.root/'registration.json').write_text('{}')
        self.no_simulation(s.build)

    def test_plan_does_not_run_or_materialize_devices(self):
        import io
        out = io.StringIO()
        with patch.object(s.subprocess, 'run', side_effect=AssertionError('No simulation')):
            with contextlib.redirect_stdout(out):
                s.plan()
        self.assertEqual(json.loads(out.getvalue())['held_out_devices'], 32)
        self.assertEqual(list(self.root.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
