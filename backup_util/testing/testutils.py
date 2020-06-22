import os
import shutil

test_file_dir = "_test_temp_"


def rel_path(*path: str) -> str:
    "create a path relative to the testing file directory"
    return os.path.join(test_file_dir, *path)


# From https://stackoverflow.com/questions/9727673/list-directory-tree-structure-in-python
def list_files(startpath: str) -> str:
    res = ""
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        res += '{}{}/\n'.format(indent, os.path.basename(root))
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            res += '{}{}\n'.format(subindent, f)
    return res


def temp_cleanup(log):
    log.info("Cleaning up temp...")
    if os.path.exists(test_file_dir) and len(os.listdir(test_file_dir)) > 0:
        for item in os.listdir(test_file_dir):
            path = rel_path(item)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
    log.info("Teardown done")
