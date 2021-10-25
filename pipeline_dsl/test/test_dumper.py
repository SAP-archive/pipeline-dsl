from pipeline_dsl import ConcourseResource
from pipeline_dsl.utils.dumper import NoTagDumper

import unittest
import yaml


class TestNoTagDumper(unittest.TestCase):
    def test_basic(self):
        x = ConcourseResource("name", "type", "icon", "source")
        result = yaml.dump(x, Dumper=NoTagDumper)
        self.assertNotIn("!!python/object", result)
