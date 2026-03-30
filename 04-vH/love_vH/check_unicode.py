import os

for root, dirs, files in os.walk("."):
    for f in files:
        if f.endswith((".py", ".md", ".txt", ".yaml", ".yml", ".toml")):
            path = os.path.join(root, f)
            try:
                with open(path, "r", encoding="ascii") as file:
                    file.read()
            except Exception:
                print(" Problem in:", path)