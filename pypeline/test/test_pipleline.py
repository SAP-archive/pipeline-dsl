import unittest

from pypeline import *
import base64
import subprocess
from collections import OrderedDict
from pypeline.utils.docker_daemon import START_SCRIPT, STOP_SCRIPT
from pypeline.concourse.__shared import SCRIPT_DIR, set_concourse_context
from contextlib import contextmanager

@contextmanager
def concourse_ctx():
    set_concourse_context(True)
    try:
        yield
    finally:
        set_concourse_context(False)


TEST_DIR = os.path.abspath(os.path.dirname(__file__))

class TestPipline(unittest.TestCase):

    def test_init_task(self):
        with Pipeline("test",script_dirs={"fake":"fake_scripts"}) as pipeline:
            with pipeline.job("job") as job:
                @job.task()
                def task():
                    pass
            
            self.assertEqual(len(pipeline.jobs),1)
            job = pipeline.jobs[0]
            self.assertEqual(len(job.plan),2)

            init_task = job.plan[0]
            self.assertTrue(isinstance(init_task,InitTask))
            self.assertEqual(init_task.init_dirs,{
                'starter': TEST_DIR,
                'pythonpath/pypeline': os.path.dirname(TEST_DIR),
                'fake': os.path.join(TEST_DIR,'fake_scripts')
            })
            data = init_task.package()
            files = subprocess.check_output(["tar","tjf", "-"], input=base64.b64decode(data)).decode("utf-8").split()
            self.assertIn(f"starter/{os.path.basename(__file__)}",files)
            self.assertIn(START_SCRIPT,files)
            self.assertIn(STOP_SCRIPT,files)
            self.assertIn('fake/test.sh',files)

            self.assertEqual(pipeline.script_dir('fake'),os.path.join(TEST_DIR,'fake_scripts'))

            with concourse_ctx():
                self.assertEqual(pipeline.script_dir('fake'),os.path.abspath('scripts/fake'))


if __name__ == '__main__':
    unittest.main()

# run > python -munittest in main pypeline dir to execute