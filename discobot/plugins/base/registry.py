class Registry:
    def __init__(self):
        self.registry = []

    def add(self, cls):
        self.registry.append(cls)

    def reload(self):
        import importlib
        import inspect
        modules = [inspect.getmodule(cls) for cls in self.registry]
        self.registry = []
        for module in modules:
            importlib.reload(module)

    def instantiate_all(self, *args, **kwargs):
        return [cls(*args, **kwargs) for cls in self.registry]

registry = Registry()

def register_module(cls):
    registry.add(cls)
