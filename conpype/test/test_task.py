from conpype import Task
import unittest


class TestJobSimple(unittest.TestCase):

    def test_basic(self):
        def test_task(out):
            return 0
        task = Task(test_task, "jobname", "timeout", privileged=False, image_resource={}, script="", inputs=[], outputs=[], secrets={}, attempts=4, caches=[], name=None, secret_manager=None, env={})

        obj = task.concourse()

        self.assertEqual(obj["task"], "test-task")

    def test_output(self):
        def test_task(out):
            return 0
        task = Task(test_task, "jobname", "timeout", privileged=False, image_resource={}, script="", inputs=[], outputs=["out"], secrets={}, attempts=4, caches=[], name=None, secret_manager=None, env={})

        obj = task.concourse()

        self.assertEqual(obj["task"], "test-task")
        self.assertEqual(obj["config"]["outputs"][1], {"name": "out"})
