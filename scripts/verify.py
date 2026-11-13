from pathlib import Path
import hashlib

site = Path(__file__).resolve().parents[1] / "site"
count = 0
for line in (site / "SHA256SUMS.txt").read_text().splitlines():
    digest, name = line.split("  ", 1)
    file = (site / name).resolve()
    if not file.is_relative_to(site.resolve()):
        raise SystemExit("Unsafe manifest path")
    if not file.is_file():
        raise SystemExit(f"Missing file: {name}")
    if hashlib.sha256(file.read_bytes()).hexdigest() != digest:
        raise SystemExit(f"Hash mismatch: {name}")
    count += 1
print(f"PASS: {count} site files match SHA256SUMS.txt")
