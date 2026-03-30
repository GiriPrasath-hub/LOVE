import os

for root, dirs, files in os.walk("."):
    for f in files:
        if f.endswith((".py", ".md", ".txt", ".yaml", ".yml", ".toml")):
            path = os.path.join(root, f)

            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as file:
                    content = file.read()

                # remove all non-ascii
                clean = content.encode("ascii", errors="ignore").decode()

                with open(path, "w", encoding="utf-8") as file:
                    file.write(clean)

                print(" cleaned:", path)

            except Exception as e:
                print(" error:", path, e)