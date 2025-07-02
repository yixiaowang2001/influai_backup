import os

ALLOWED_EXTENSIONS = {'.py', '.md', '.gitignore'}


def has_allowed_files(path):
    for root, dirs, files in os.walk(path):
        for file in files:
            _, ext = os.path.splitext(file)
            if file in ALLOWED_EXTENSIONS or ext in ALLOWED_EXTENSIONS:
                return True
    return False

def print_tree(startpath, prefix=""):
    items = sorted(os.listdir(startpath))
    items = [item for item in items if not item.startswith('.')]
    display_items = []

    for item in items:
        full_path = os.path.join(startpath, item)
        if os.path.isdir(full_path):
            if has_allowed_files(full_path):
                display_items.append((item, True))
        else:
            _, ext = os.path.splitext(item)
            if item in ALLOWED_EXTENSIONS or ext in ALLOWED_EXTENSIONS:
                display_items.append((item, False))

    for index, (item, is_dir) in enumerate(display_items):
        connector = "└── " if index == len(display_items) - 1 else "├── "
        print(prefix + connector + item)
        full_path = os.path.join(startpath, item)
        if is_dir:
            extension = "    " if index == len(display_items) - 1 else "│   "
            print_tree(full_path, prefix + extension)


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(os.path.basename(current_dir))
    print_tree(current_dir)