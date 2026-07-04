import difflib

def apply_patch(file_path, old, new):
    with open(file_path, "r") as f:
        content = f.read()

    if old not in content:
        return "OLD CODE NOT FOUND"

    new_content = content.replace(old, new)

    diff = difflib.unified_diff(
        content.splitlines(),
        new_content.splitlines(),
        lineterm=""
    )

    with open(file_path, "w") as f:
        f.write(new_content)

    return "\n".join(diff)
