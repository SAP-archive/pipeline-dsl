from pipeline_dsl import Pipeline, PutStep, GetStep, DoStep, GitRepo
import unittest


class TestJobSimple(unittest.TestCase):
    def test_basic(self):
        with Pipeline("test", script_dirs={"fake": "fake_scripts"}) as pipeline:
            job = pipeline.job("job")
            obj = job.concourse()

            obj["plan"] = obj["plan"][1:]  # remove init task. it is checked test_pipeline.py
            self.assertDictEqual(
                obj,
                {
                    "name": "job",
                    "plan": [],
                    "serial": False,
                    "serial_groups": [],
                },
            )

    def test_with_hooks(self):
        with Pipeline("test", script_dirs={"fake": "fake_scripts"}) as pipeline:
            job = pipeline.job("job")

            job.on_success = PutStep("test_res_success", {"param": "success"})
            job.on_failure = PutStep("test_res_fail", {"param": "fail"})
            job.on_abort = PutStep("test_res_abort", {"param": "abort"})
            job.ensure = GetStep("test_res_ensure", False, ["job-1"], {"param": "ensure"}, version="every")

            obj = job.concourse()

            obj["plan"] = obj["plan"][1:]  # remove init task. it is checked test_pipeline.py
            self.assertDictEqual(
                obj,
                {
                    "name": "job",
                    "plan": [],
                    "serial": False,
                    "serial_groups": [],
                    "on_success": {
                        "put": "test_res_success",
                        "params": {"param": "success"},
                    },
                    "on_failure": {
                        "put": "test_res_fail",
                        "params": {"param": "fail"},
                    },
                    "on_abort": {
                        "put": "test_res_abort",
                        "params": {"param": "abort"},
                    },
                    "ensure": {
                        "get": "test_res_ensure",
                        "trigger": False,
                        "passed": ["job-1"],
                        "params": {"param": "ensure"},
                        "version": "every",
                    },
                },
            )

    def test_get_put(self):
        with Pipeline("test", script_dirs={"fake": "fake_scripts"}) as pipeline:
            pipeline.resource("res-1", GitRepo("https://example.com/repo.git"))
            pipeline.resource("res-2", GitRepo("https://example.com/repo.git"))

            job = pipeline.job("job")

            job.get("res-1", False, ["testjob"], params={"test": 1})
            job.get("res-2", True, ["testjob2"], params={"test": 2})

            job.put("res-1", {"test": 3})
            job.put("res-2", {"test": 4})

            obj = job.concourse()

            obj["plan"] = obj["plan"][1:]  # remove init task. it is checked test_pipeline.py
            self.assertDictEqual(
                obj,
                {
                    "name": "job",
                    "plan": [
                        {
                            "get": "res-1",
                            "trigger": False,
                            "passed": ["testjob"],
                            "params": {"test": 1},
                        },
                        {
                            "get": "res-2",
                            "trigger": True,
                            "passed": ["testjob2"],
                            "params": {"test": 2},
                        },
                        {
                            "put": "res-1",
                            "params": {"test": 3},
                        },
                        {
                            "put": "res-2",
                            "params": {"test": 4},
                        },
                    ],
                    "serial": False,
                    "serial_groups": [],
                },
            )

    def test_parallel_try(self):
        with Pipeline("test", script_dirs={"fake": "fake_scripts"}) as pipeline:
            pipeline.resource("res-1", GitRepo("https://example.com/repo.git"))
            pipeline.resource("res-2", GitRepo("https://example.com/repo.git"))

            job = pipeline.job("job")

            with job.in_parallel(fail_fast=True) as parallel:
                parallel.put("res-1", {"test": 3})
                parallel.put("res-2", {"test": 4})

            obj = job.concourse()

            obj["plan"] = obj["plan"][1:]  # remove init task. it is checked test_pipeline.py
            self.assertDictEqual(
                obj,
                {
                    "name": "job",
                    "plan": [
                        {
                            "in_parallel": {
                                "fail_fast": True,
                                "steps": [
                                    {
                                        "put": "res-1",
                                        "params": {"test": 3},
                                    },
                                    {
                                        "put": "res-2",
                                        "params": {"test": 4},
                                    },
                                ],
                            },
                        },
                    ],
                    "serial": False,
                    "serial_groups": [],
                },
            )

    def test_do(self):
        with Pipeline("test", script_dirs={"fake": "fake_scripts"}) as pipeline:
            pipeline.resource("res-1", GitRepo("https://example.com/repo.git"))
            pipeline.resource("res-2", GitRepo("https://example.com/repo.git"))

            job = pipeline.job("job")

            job.get("res-1", False, ["testjob"], params={"test": 1})
            job.get("res-2", True, ["testjob2"], params={"test": 2})

            job.ensure = DoStep([PutStep("res-1", {"test": 3}), PutStep("res-2", {"test": 4})])

            obj = job.concourse()

            obj["plan"] = obj["plan"][1:]  # remove init task. it is checked test_pipeline.py
            self.assertDictEqual(
                obj,
                {
                    "name": "job",
                    "plan": [
                        {
                            "get": "res-1",
                            "trigger": False,
                            "passed": ["testjob"],
                            "params": {"test": 1},
                        },
                        {
                            "get": "res-2",
                            "trigger": True,
                            "passed": ["testjob2"],
                            "params": {"test": 2},
                        },
                    ],
                    "serial": False,
                    "serial_groups": [],
                    "ensure": {
                        "do": [
                            {
                                "put": "res-1",
                                "params": {"test": 3},
                            },
                            {
                                "put": "res-2",
                                "params": {"test": 4},
                            },
                        ]
                    },
                },
            )
