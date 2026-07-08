import os


def print_tree(root, prefix="", depth=None, level=3):
    if depth is not None and level >= depth:
        return
    entries = sorted(os.listdir(root))
    for i, name in enumerate(entries):
        path = os.path.join(root, name)
        connector = "└── " if i == len(entries) - 1 else "├── "
        print(prefix + connector + name)
        if os.path.isdir(path):
            extension = "    " if i == len(entries) - 1 else "│   "
            print_tree(path, prefix + extension, depth, level + 1)


print_tree(r"D:\1_pytorch", depth=2)
