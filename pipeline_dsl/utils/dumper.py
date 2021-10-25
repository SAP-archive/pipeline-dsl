import yaml


class NoTagDumper(yaml.Dumper):
    """
    NoTagDumper same as yaml.Dumper but suppress "!!python/object:" yaml tags for portability
    """

    def represent_object(self, dumper, object):
        return dumper.represent_dict(vars(object))

    def __init__(self, stream, **kwargs):
        yaml.Dumper.__init__(self, stream, **kwargs)
        self.add_multi_representer(object, self.represent_object)
