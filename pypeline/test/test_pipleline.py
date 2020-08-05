import unittest

from pypeline import *
import base64
import subprocess
from collections import OrderedDict
from pypeline.utils.docker_daemon import START_SCRIPT, STOP_SCRIPT
from pypeline.concourse.__shared import SCRIPT_DIR

class TestPipline(unittest.TestCase):

    def test_init_task(self):
        with Pipeline("test") as pipeline:
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
                'starter': os.path.abspath(os.path.dirname(__file__)),
                'pythonpath/pypeline': os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
            })
            data = init_task.package()
            files = subprocess.check_output(["tar","tzf", "-"], input=base64.b64decode(data)).decode("utf-8").split()
            self.assertIn(f"starter/{os.path.basename(__file__)}",files)
            self.assertIn(START_SCRIPT,files)
            self.assertIn(STOP_SCRIPT,files)

if __name__ == '__main__':
    unittest.main()

# run > python -munittest in main pypeline dir to execute
