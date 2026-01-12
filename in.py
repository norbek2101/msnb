import os
import sys

if len(sys.argv) != 2:
    print("Usage: python script.py <foldername>")
    sys.exit(1)

target_dir = os.path.abspath(sys.argv[1])

if not os.path.isdir(target_dir):
    print(f"Error: '{target_dir}' is not a directory")
    sys.exit(1)

for current_path, dirnames, filenames in os.walk(target_dir):
    init_file = os.path.join(current_path, "__init__.py")
    if not os.path.exists(init_file):
        open(init_file, "w").close()