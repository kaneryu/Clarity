from packaging.version import Version

try:
    with open("version.txt", encoding="utf-8") as f:
        # We might have a BOM marker, so let's handle that
        version = Version(f.read().replace("\ufeff", "").strip())
except FileNotFoundError:
    print("version.txt not found, using 0.0.0")
    version = Version("0.0.0")

release = "Pre-Release 1 (INDEV)"
print("Clarity", str(version), release)
