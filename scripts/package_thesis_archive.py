"""
ArchSynth v2.0 - Thesis Research Package Builder
Packages the complete research repository into ArchSynth_Thesis_Research_Package.zip
with strict exclusion rules (.venv, __pycache__, .env, scratch, root .git).
Computes SHA-256 checksum and updates PACKAGE_MANIFEST.md.
"""

import os
import sys
import zipfile
import hashlib
from pathlib import Path

def package_archive():
    base_dir = Path(__file__).parent.parent.resolve()
    zip_name = "ArchSynth_Thesis_Research_Package.zip"
    zip_path = base_dir / zip_name
    manifest_path = base_dir / "PACKAGE_MANIFEST.md"

    if zip_path.exists():
        print(f"Removing existing archive: {zip_path.name}")
        zip_path.unlink()

    exclude_dirs = {".venv", "__pycache__", ".pytest_cache", ".git"}
    exclude_root_dirs = {".git", "scratch"}
    exclude_path_prefixes = {
        "output/web_runs",
        "output/navigation2_pipeline",
        "output/test_phase2"
    }
    exclude_extensions = {".pyc", ".tmp", ".gif", ".mp4", ".avi"}
    exclude_files = {".env", zip_name}

    count = 0
    total_size = 0

    print(f"Packaging Option B (Slim Package): {zip_name} from {base_dir}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for root, dirs, files in os.walk(base_dir):
            p_root = Path(root)
            try:
                rel_root = p_root.relative_to(base_dir)
            except ValueError:
                continue

            rel_posix = rel_root.as_posix()

            # Exclude specific root-level directories
            if len(rel_root.parts) > 0 and rel_root.parts[0] in exclude_root_dirs:
                dirs[:] = []
                continue

            # Exclude specific path prefixes (e.g. output/web_runs, output/navigation2_pipeline)
            if any(rel_posix == p or rel_posix.startswith(p + "/") for p in exclude_path_prefixes):
                dirs[:] = []
                continue

            # Prune excluded directories (including all .git and .venv folders)
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith(".venv")]

            for f in files:
                if f in exclude_files:
                    continue
                if any(f.endswith(ext) for ext in exclude_extensions):
                    continue
                f_path = p_root / f
                rel_f = f_path.relative_to(base_dir)
                zf.write(f_path, rel_f)
                count += 1
                total_size += f_path.stat().st_size
                if count % 1000 == 0:
                    print(f"  Processed {count} files...")

    zip_size = zip_path.stat().st_size
    zip_size_mb = zip_size / (1024 * 1024)
    total_size_mb = total_size / (1024 * 1024)
    print(f"Archive created successfully:")
    print(f"  Files packed:     {count}")
    print(f"  Uncompressed:     {total_size_mb:.2f} MB")
    print(f"  Compressed Size:  {zip_size_mb:.2f} MB")

    # Compute SHA-256
    print("Computing SHA-256 checksum...")
    sha256 = hashlib.sha256()
    with open(zip_path, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    hash_str = sha256.hexdigest()
    print(f"  SHA-256 Checksum: {hash_str}")

    # Verify exclusions
    print("Verifying archive exclusions...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        has_env = any(n == ".env" or n.endswith("/.env") for n in names)
        has_pycache = any("__pycache__" in n for n in names)
        has_venv = any(".venv" in n for n in names)
        assert not has_env, "ERROR: .env found in archive!"
        assert not has_pycache, "ERROR: __pycache__ found in archive!"
        assert not has_venv, "ERROR: .venv found in archive!"
        print(f"  Verification PASSED: {len(names)} entries. No .env, no .venv, no __pycache__.")

    # Update PACKAGE_MANIFEST.md
    if manifest_path.exists():
        content = manifest_path.read_text(encoding="utf-8")
        # Replace or append checksum section
        lines = content.splitlines()
        clean_lines = []
        for line in lines:
            if line.startswith("- **Archive File Size**:") or line.startswith("- **SHA-256 Checksum**:"):
                continue
            clean_lines.append(line)
        clean_lines.append(f"- **Archive File Size**: {zip_size_mb:.2f} MB")
        clean_lines.append(f"- **SHA-256 Checksum**: `{hash_str}`")
        manifest_path.write_text("\n".join(clean_lines) + "\n", encoding="utf-8")
        print(f"Updated {manifest_path.name} with new checksum.")

if __name__ == "__main__":
    package_archive()
