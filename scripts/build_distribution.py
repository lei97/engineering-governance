import argparse
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description="Build a portable Engineering Governance ZIP.")
    parser.add_argument("variant", choices=("light", "full"))
    parser.add_argument("output", type=Path, help="path to a new ZIP file")
    args = parser.parse_args()

    skill = Path("skills/engineering-governance")
    files = [Path("LICENSE"), Path("docs/install.md"), skill / "SKILL.md"]
    references = ROOT / skill / "references"
    files.extend(path.relative_to(ROOT) for path in sorted(references.glob("*.md")))
    if args.variant == "full":
        specifications = ROOT / "specifications"
        files.extend(path.relative_to(ROOT) for path in sorted(specifications.glob("*.md")))
        files.extend([
            Path("requirements.txt"),
            Path("schemas/knowledge.schema.json"),
            Path("scripts/validate_truth.py"),
        ])

    archive = BytesIO()
    try:
        with ZipFile(archive, "w", ZIP_DEFLATED) as bundle:
            for path in files:
                bundle.write(ROOT / path, arcname=path.as_posix())

        output = args.output.open("xb")
        try:
            with output:
                output.write(archive.getbuffer())
        except OSError:
            args.output.unlink(missing_ok=True)
            raise
    except FileExistsError:
        parser.exit(1, f"Output already exists: {args.output}\n")
    except OSError as exc:
        parser.exit(1, f"Could not build distribution: {exc}\n")

    print(f"Built {args.variant} distribution at {args.output}")


if __name__ == "__main__":
    main()
