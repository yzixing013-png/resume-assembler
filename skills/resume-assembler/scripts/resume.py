"""Local storage and PDF commands used by the resume-assembler Skill."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import urllib.request
import uuid
import xml.etree.ElementTree as ET
import zipfile

from resume_core import render, safe_extract, validate
from resume_evidence import prepare_context


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def backup_library(data):
    path = data / "library.json"
    if not path.exists():
        return None
    destination = data / "backups" / (uuid.uuid4().hex + ".json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, destination)
    return str(destination)


def write_library(data, library):
    backup = backup_library(data)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=data,
                                     suffix=".tmp", delete=False) as stream:
        temporary = Path(stream.name)
        json.dump(library, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    try:
        temporary.replace(data / "library.json")
    finally:
        temporary.unlink(missing_ok=True)
    return backup


def initialize(data):
    for name in ("materials", "templates", "outputs", "backups"):
        (data / name).mkdir(parents=True, exist_ok=True)
    path = data / "library.json"
    if path.exists():
        library = read_json(path)
        backup = backup_library(data)
    else:
        library = {
            "schema_version": 2,
            "profile": {"name": "", "contact": "", "education": [], "skills": [],
                        "awards": [], "availability": ""},
            "projects": [], "sources": [], "template": "public",
        }
        backup = write_library(data, library)
    return {
        "data": str(data), "library": str(path), "backup": backup,
        "projects": len(library.get("projects", [])),
        "template": library.get("template", "public"),
        "ready": {"pymupdf": importlib.util.find_spec("pymupdf") is not None,
                  "tectonic": shutil.which("tectonic")},
        "next": "Read the library. Collect missing project materials and a template, then ask for the target JD.",
    }


def extract_text(path):
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        import pymupdf
        with pymupdf.open(path) as document:
            return "\n\n".join(
                f"[Page {index + 1}]\n{page.get_text()}"
                for index, page in enumerate(document)
                if page.get_text().strip()
            )
    if suffix == ".docx":
        with zipfile.ZipFile(path) as archive:
            document = ET.fromstring(archive.read("word/document.xml"))
        namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        return "\n".join(
            "".join(node.itertext())
            for node in document.findall(".//w:p", namespace)
        )
    if suffix in {".txt", ".md", ".tex", ".json", ".csv", ".py", ".rst"}:
        return path.read_text(encoding="utf-8-sig")
    return ""


def github_readme(url):
    match = re.fullmatch(r"https://github\.com/([\w.-]+)/([\w.-]+?)(?:\.git)?/?", url)
    if not match:
        raise ValueError("Use a repository URL such as https://github.com/owner/repo.")
    owner, repository = match.groups()
    request = urllib.request.Request(
        f"https://api.github.com/repos/{owner}/{repository}/readme",
        headers={"User-Agent": "ResumeAssembler", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read(2_000_000))
    content = base64.b64decode(payload["content"]).decode("utf-8")
    return (f"Repository README from {url}\nFull source and personal contribution have not been assessed.\n\n"
            + content).encode("utf-8")


def import_material(args, data):
    library = read_json(data / "library.json")
    if args.github:
        if args.kind == "template":
            raise ValueError("Templates must be imported from a local LaTeX ZIP.")
        original = args.github
        raw = github_readme(args.github)
        filename = "github-readme.md"
    else:
        original = str(Path(args.file).expanduser().resolve())
        path = Path(original)
        if not path.is_file():
            raise ValueError("Choose a file. For a project directory, inspect it and import the relevant reports or files individually.")
        raw = path.read_bytes()
        filename = path.name
    digest = hashlib.sha256(raw).hexdigest()
    sources = library.setdefault("sources", [])
    previous = next((source for source in sources
                     if source.get("sha256") == digest and source.get("kind") == args.kind), None)
    if previous:
        if args.kind == "template" and library.get("template") != previous["template_id"]:
            library["template"] = previous["template_id"]
            write_library(data, library)
        return {"reused": True, "source": previous}

    folder = data / "materials" / digest
    folder.mkdir(parents=True, exist_ok=True)
    snapshot = folder / "original" / filename
    snapshot.parent.mkdir(exist_ok=True)
    snapshot.write_bytes(raw)
    source = {
        "id": f"source-{args.kind}-{digest[:16]}", "kind": args.kind,
        "original_path": original, "snapshot": snapshot.relative_to(data).as_posix(),
        "sha256": digest, "captured_at": datetime.now(timezone.utc).isoformat(),
        "verification": "Imported material; claims and personal contribution need assessment.",
    }
    if args.kind == "template":
        key = uuid.uuid4().hex
        with tempfile.TemporaryDirectory(dir=data / "templates") as staging:
            safe_extract(raw, Path(staging))
            shutil.copytree(staging, data / "templates" / key)
        source["template_id"] = key
        library["template"] = key
    else:
        text = extract_text(snapshot)
        if text.strip():
            text_path = folder / "extracted.txt"
            text_path.write_text(text, encoding="utf-8")
            source["text_snapshot"] = text_path.relative_to(data).as_posix()
        else:
            source["note"] = "Archived without extracted text. Use the agent's image/OCR tools for images or scanned PDFs."
    sources.append(source)
    backup = write_library(data, library)
    return {"reused": False, "source": source, "backup": backup}


def render_assembly(args, data):
    library = read_json(data / "library.json")
    result = read_json(args.assembly)
    validate(result, library)
    engine = args.tectonic or shutil.which("tectonic")
    if not engine:
        raise ValueError("Install Tectonic or supply --tectonic with its executable path.")
    folder = data / "outputs" / uuid.uuid4().hex
    folder.mkdir(parents=True)
    (folder / "assembly.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (folder / "library-snapshot.json").write_text(json.dumps(library, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.jd:
        jd = Path(args.jd).read_text(encoding="utf-8-sig")
        (folder / "jd.txt").write_text(jd, encoding="utf-8")
        _, audit = prepare_context(library, jd)
        (folder / "retrieval.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        quality = render(result, library, folder, data, engine)
    except Exception as error:
        raise ValueError(f"{error} Output and logs are in {folder}") from error
    (folder / "quality.json").write_text(json.dumps(quality, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"pdf": str(folder / "resume.pdf"), "preview": str(folder / "preview.png"),
            "tex": str(folder / "resume.tex"), "assembly": str(folder / "assembly.json"),
            "quality": quality}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "import", "render"):
        command = commands.add_parser(name)
        command.add_argument("--data", default="resume-data", help="Persistent user data directory, outside the installed Skill.")
        if name == "import":
            inputs = command.add_mutually_exclusive_group(required=True)
            inputs.add_argument("--file")
            inputs.add_argument("--github")
            command.add_argument("--kind", choices=("material", "template"), default="material")
        elif name == "render":
            command.add_argument("--assembly", required=True)
            command.add_argument("--jd", help="JD text file to archive with this resume.")
            command.add_argument("--tectonic", help="Optional Tectonic executable path.")
    args = parser.parse_args()
    data = Path(args.data).expanduser().resolve()
    try:
        if args.command == "init":
            result = initialize(data)
        else:
            if not (data / "library.json").is_file():
                raise ValueError("Run init with the same --data directory first.")
            for name in ("materials", "templates", "outputs", "backups"):
                (data / name).mkdir(exist_ok=True)
            if args.command == "import":
                result = import_material(args, data)
            else:
                result = render_assembly(args, data)
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0
    except (ValueError, KeyError, TypeError, OSError, ImportError, RuntimeError,
            zipfile.BadZipFile, ET.ParseError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
