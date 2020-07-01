import os


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
