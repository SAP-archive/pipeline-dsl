from pipeline_dsl import Task
import unittest


class TestJobSimple(unittest.TestCase):

    def test_basic(self):
        def test_task(out):
            return 0
        task = Task(test_task, jobname="jobname", secret_manager=None, image_resource={}, script="")

        obj = task.concourse()

        self.assertEqual(obj["task"], "test-task")

    def test_output(self):
        def test_task(out):
            return 0
        task = Task(test_task, jobname="jobname", secret_manager=None, image_resource={}, script="", outputs=["out"])

        obj = task.concourse()

        self.assertEqual(obj["task"], "test-task")
        self.assertEqual(obj["config"]["outputs"][1], {"name": "out"})
