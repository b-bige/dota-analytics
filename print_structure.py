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
    print_directory_tree('')

# import os
# from pathlib import Path

# def print_directory_tree(root_dir, indent="", ignored_dirs={".git", "__pycache__", ".vscode", "venv", ".env"}):
#     """Prints the directory tree structure."""
#     path = Path(root_dir)
    
#     # Exclude items
#     if path.name in ignored_dirs or path.name.endswith('.egg-info'):
#         return
        
#     print(indent + "|-- " + path.name + ("/" if path.is_dir() else ""))
    
#     if path.is_dir():
#         indent += "    "
#         for item in sorted(path.iterdir()):
#             print_directory_tree(item, indent, ignored_dirs)

# if __name__ == "__main__":
#     # Start from the current working directory (project root)
#     print("Project Directory Structure:")
#     print_directory_tree(os.getcwd())