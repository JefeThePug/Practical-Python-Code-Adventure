from pathlib import Path

files = [
    "_variables.css",
    "_base.css",
    "_layout.css",
    "_forms_buttons.css",
    "components/_navbar.css",
    "components/_sponsor.css",
]

output = "\n".join(Path(f"app/static/style/{f}").read_text() for f in files)

Path("app/static/style/main.min.css").write_text(output)
