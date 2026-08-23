from pathlib import Path


class SandboxPathMapper:
    def __init__(self, root):
        self.root = Path(root)

    def resolve(self, virtual_path, must_exist=False):
        target = self.root / virtual_path
        if must_exist and not target.exists():
            raise FileNotFoundError(virtual_path)
        return target
