"""
Download NYC TLC Yellow Taxi parquet files.

Usage:
    python scripts/download_nyc_taxi.py --month 2023-01
    python scripts/download_nyc_taxi.py --month 2023-01 --months 6
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

# Try multiple download methods
try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


NYC_TLC_BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"
MONTHS = [
    "2023-01", "2023-02", "2023-03", "2023-04", "2023-05", "2023-06",
    "2023-07", "2023-08", "2023-09", "2023-10", "2023-11", "2023-12",
    "2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06",
    "2024-07", "2024-08", "2024-09", "2024-10", "2024-11", "2024-12",
    "2025-01", "2025-02", "2025-03",
]


def download_with_requests(url: str, dest: Path, chunk_size: int = 8192) -> bool:
    """Download file using requests library."""
    import requests
    resp = requests.get(url, stream=True, timeout=300)
    resp.raise_for_status()
    total = int(resp.headers.get("Content-Length", 0))
    downloaded = 0
    print(f"  Downloading {dest.name} ({total / 1024 / 1024:.1f} MB)...")

    with open(dest, "wb") as f:
        for chunk in resp.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    pct = 100 * downloaded / total
                    if downloaded % (chunk_size * 50) == 0:
                        print(f"\r  Progress: {pct:.0f}%", end="", flush=True)
    print()  # newline after progress
    return True


def download_nyc_taxi(month: str, output_dir: Path = None, force: bool = False) -> Path:
    """
    Download a single NYC TLC Yellow Taxi parquet file.

    Args:
        month: YYYY-MM format (e.g. "2023-01")
        output_dir: Directory to save file
        force: Overwrite existing file

    Returns:
        Path to downloaded parquet file
    """
    if output_dir is None:
        output_dir = Path("data/nyc-taxi")
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"yellow_tripdata_{month}.parquet"
    url = f"{NYC_TLC_BASE_URL}/{filename}"
    dest = output_dir / filename

    if dest.exists() and not force:
        print(f"  File already exists: {dest} ({dest.stat().st_size / 1024 / 1024:.1f} MB)")
        # Verify it's a valid parquet file
        try:
            if HAS_PANDAS:
                df = pd.read_parquet(dest)
                print(f"  Verified: {len(df):,} rows, {len(df.columns)} columns")
                return dest
            return dest
        except Exception:
            print(f"  File corrupt, re-downloading...")
            dest.unlink()

    print(f"Downloading NYC TLC Yellow Taxi: {month}")
    print(f"  URL: {url}")
    print(f"  Dest: {dest}")

    if HAS_REQUESTS:
        download_with_requests(url, dest)
    else:
        import subprocess
        print("  Using curl...")
        result = subprocess.run(
            ["curl", "-L", "-o", str(dest), url],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"  curl failed: {result.stderr}")
            raise RuntimeError(f"Download failed: {result.stderr}")

    # Verify
    if HAS_PANDAS:
        try:
            df = pd.read_parquet(dest)
            print(f"  Verified: {len(df):,} rows, {len(df.columns)} columns")
        except Exception as e:
            dest.unlink()
            raise RuntimeError(f"Downloaded file is not valid parquet: {e}")

    return dest


def main():
    parser = argparse.ArgumentParser(description="Download NYC TLC Yellow Taxi data")
    parser.add_argument("--month", type=str, default="2023-01", help="Month in YYYY-MM format")
    parser.add_argument("--months", type=int, default=1, help="Download N consecutive months starting from --month")
    parser.add_argument("--output-dir", type=str, default="data/nyc-taxi", help="Output directory")
    parser.add_argument("--force", action="store_true", help="Force re-download")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    downloaded = []

    for i in range(args.months):
        # Calculate month string
        year, month = map(int, args.month.split("-"))
        month_num = month + i
        year_offset = (month_num - 1) // 12
        actual_month = ((month_num - 1) % 12) + 1
        actual_year = year + year_offset
        month_str = f"{actual_year}-{actual_month:02d}"

        try:
            dest = download_nyc_taxi(month_str, output_dir, args.force)
            downloaded.append(dest)
        except Exception as e:
            print(f"Failed to download {month_str}: {e}")
            continue

    print(f"\nDownload complete. {len(downloaded)} files.")
    for d in downloaded:
        print(f"  {d}")


if __name__ == "__main__":
    main()
