import unittest

from conpype import *

class TestGitResource(unittest.TestCase):

    def test_basic(self):
        repo = GitRepo("https://example.com/repo.git")
        
        obj = repo.concourse(name="test")
        self.assertDictEqual(obj, {
            "name": "test",
            "type": "git",
            "icon": "git",
            "source": {
                "uri": "https://example.com/repo.git"
            }
        })

if __name__ == '__main__':
    unittest.main()

# run > python -munittest in main conpype dir to execute
