from conpype import Pipeline, PutStep, GetStep, DoStep, GitRepo, Task
import unittest


class TestJobSimple(unittest.TestCase):

    def test_basic(self):
        with Pipeline("test", script_dirs={"fake": "fake_scripts"}) as pipeline:
            job = pipeline.job("job")

            with job as job:
                @job.task()
                def test_task():
                    return 0

            obj = job.concourse()

            obj["plan"] = obj["plan"][1:]  # remove init task. it is checked test_pipeline.py
            self.assertEqual(obj["plan"][0]["task"], "test-task")

    def test_output(self):
        with Pipeline("test", script_dirs={"fake": "fake_scripts"}) as pipeline:
            job = pipeline.job("job")

            with job as job:
                @job.task(outputs=["out"])
                def test_task(out):
                    return 0

            obj = job.concourse()

            self.assertEqual(obj["plan"][1]["task"], "test-task")
            self.assertEqual(obj["plan"][1]["config"]["outputs"][1], {"name": "out"})

    