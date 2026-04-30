import os
from pathlib import Path

def print_directory_tree(root_dir: str, indent: str = ""):
    """
    Prints the visual directory tree of a given path.
    """
    path = Path(root_dir)
    if not path.exists():
        print(f"Directory not found: {root_dir}")
        return

    # Print the directory name
    if indent == "":
        print(f"📁 {path.name}/")
        indent = "    "

    # Sort items so files and folders are grouped nicely
    items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))

    for item in items:
        # Ignore hidden files (like __pycache__ or .git)
        if item.name.startswith("."):
            continue

        if item.is_dir():
            print(f"{indent}📁 {item.name}/")
            print_directory_tree(str(item), indent + "    ")
        elif item.is_file():
            print(f"{indent}📄 {item.name}")

if __name__ == "__main__":
    # Point to your dashboard folder
    target_dir = os.path.join("src", "dashboard")
    print_directory_tree(target_dir)