from pipeline_dsl import InitTask
import unittest


class TestInitTaskSimple(unittest.TestCase):
    def test_basic(self):
        task = InitTask({}, "image")

        obj = task.concourse()

        self.assertEqual(obj["task"], "init")
