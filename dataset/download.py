from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
import time
import zipfile
from collections.abc import Callable
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote, urlencode

import requests

OWNER = "odedgolden"
DATASET_SLUG = "movielens-1m-dataset"
API_BASE = "https://www.kaggle.com/api/v1"
DEFAULT_RAW_DIR = Path(__file__).resolve().parent / "raw"
REQUIRED_FILES = frozenset({"README", "movies.dat", "ratings.dat", "users.dat"})
EXPECTED_RATINGS = 1_000_209
CHUNK_SIZE = 1 << 20
DEFAULT_TIMEOUT = 30.0
DEFAULT_RETRIES = 3
USER_AGENT = "AIE425-MovieLens-downloader/1.0"
DISPLAY_NAME = "MovieLens-1M bundle"

ProgressCallback = Callable[[int, int | None], None]


class DownloadError(RuntimeError):
    """Base class for errors that can be shown directly to the user."""


class TransientError(DownloadError):
    """A retryable network or server failure."""

    def __init__(self, message: str, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


def build_url(version: str | None = None) -> str:
    """Build the Kaggle whole-dataset download URL, optionally pinned to a version."""
    segments = "/".join(quote(part, safe="") for part in (OWNER, DATASET_SLUG))
    url = f"{API_BASE}/datasets/download/{segments}"
    if version is not None:
        value = str(version).strip()
        if not value:
            raise DownloadError("--version cannot be empty.")
        url = f"{url}?{urlencode({'datasetVersionNumber': value})}"
    return url


def _resolve_dest_dir(dest_dir: str | Path | None) -> Path:
    """Resolve the destination directory; default to ``dataset/raw``."""
    base = Path(dest_dir).expanduser() if dest_dir is not None else DEFAULT_RAW_DIR
    return base.resolve()


def _create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "file"})
    return session


def _retry_after(response: Any) -> float | None:
    raw = getattr(response, "headers", {}).get("Retry-After")
    try:
        return max(0.0, float(raw))
    except (TypeError, ValueError):
        return None


def _http_error(response: Any) -> DownloadError:
    status = int(getattr(response, "status_code", 0))
    detail = ""
    try:
        payload = response.json()
    except (AttributeError, ValueError):
        payload = None
    if isinstance(payload, dict) and isinstance(payload.get("message"), str):
        detail = f" ({payload['message']})"

    if status in (401, 403):
        return DownloadError(
            f"Kaggle rejected the request (HTTP {status}){detail}. "
            "This token-free downloader only works for public datasets."
        )
    if status == 404:
        return DownloadError(
            f"Dataset not found (HTTP {status}){detail}. "
            "Check the dataset slug and --version."
        )
    if status == 429:
        return TransientError(
            f"Kaggle rate limit reached (HTTP {status}){detail}.",
            retry_after=_retry_after(response),
        )
    if 500 <= status < 600:
        return TransientError(
            f"Kaggle server error (HTTP {status}){detail}.",
            retry_after=_retry_after(response),
        )
    return DownloadError(f"Unexpected Kaggle response (HTTP {status}){detail}.")


def _stream_to_temp(
    session: requests.Session,
    url: str,
    timeout: float,
    temp_path: Path,
    progress: ProgressCallback | None,
) -> None:
    """Stream one GET response into ``temp_path`` without buffering it in memory."""
    response: Any = None
    try:
        response = session.get(
            url,
            stream=True,
            timeout=(timeout, timeout),
        )
        if getattr(response, "status_code", None) != 200:
            raise _http_error(response)

        raw_total = getattr(response, "headers", {}).get("Content-Length")
        try:
            total = int(raw_total) if raw_total is not None else None
        except (TypeError, ValueError):
            total = None

        downloaded = 0
        with temp_path.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if not chunk:
                    continue
                handle.write(chunk)
                downloaded += len(chunk)
                if progress is not None:
                    progress(downloaded, total)

        if downloaded == 0:
            raise DownloadError(
                "Kaggle returned an empty response; nothing was downloaded."
            )
    except requests.RequestException as exc:
        raise TransientError(f"Network error while downloading: {exc}") from exc
    finally:
        if response is not None:
            close = getattr(response, "close", None)
            if callable(close):
                close()


def _validate_ratings(path: Path) -> None:
    """Check that the ratings file has the expected MovieLens-1M format."""
    try:
        with path.open("rb") as handle:
            first_line = handle.readline()
    except OSError as exc:
        raise DownloadError(f"Cannot read ratings file: {exc}") from exc

    if not first_line.strip():
        raise DownloadError("ratings.dat in the archive is empty.")

    fields = first_line.decode("utf-8", errors="replace").rstrip("\r\n").split("::")
    if len(fields) != 4:
        raise DownloadError(
            "ratings.dat does not look like MovieLens-1M data: "
            "expected four '::'-separated fields on the first line."
        )


def _member_target(name: str, staging: Path) -> Path:
    """Map an archive member to a path inside ``staging``, rejecting unsafe names."""
    normalized = name.replace("\\", "/")
    candidate = PurePosixPath(normalized)
    if (
        not candidate.parts
        or candidate.is_absolute()
        or ".." in candidate.parts
        or ":" in candidate.parts[0]
    ):
        raise DownloadError(f"Unsafe path in Kaggle archive: {name}")
    target = staging.joinpath(*candidate.parts)
    if not target.resolve().is_relative_to(staging.resolve()):
        raise DownloadError(f"Unsafe path in Kaggle archive: {name}")
    return target


def _extract_archive(archive: Path, staging: Path) -> None:
    """Extract the whole archive into a staging directory, safely."""
    try:
        with zipfile.ZipFile(archive) as bundle:
            for info in bundle.infolist():
                if info.is_dir():
                    continue
                target = _member_target(info.filename, staging)
                target.parent.mkdir(parents=True, exist_ok=True)
                with bundle.open(info) as source, target.open("wb") as handle:
                    shutil.copyfileobj(source, handle, CHUNK_SIZE)
    except (zipfile.BadZipFile, OSError) as exc:
        raise DownloadError(f"Cannot read Kaggle dataset archive: {exc}") from exc


def _validate_dataset(staging: Path) -> None:
    present = {path.name for path in staging.iterdir() if path.is_file()}
    missing = sorted(REQUIRED_FILES - present)
    if missing:
        raise DownloadError(
            f"Dataset archive is missing expected files: {', '.join(missing)}."
        )
    for name in sorted(REQUIRED_FILES):
        if (staging / name).stat().st_size == 0:
            raise DownloadError(f"Dataset file {name} is empty.")
    _validate_ratings(staging / "ratings.dat")


def _finalise(temp_path: Path, dest_dir: Path) -> None:
    """Validate the bundle and atomically move every member into place."""
    if not zipfile.is_zipfile(temp_path):
        raise DownloadError(
            "Kaggle did not return a zip bundle; expected the full dataset archive."
        )

    staging = Path(tempfile.mkdtemp(dir=dest_dir.parent, prefix=".raw-staging-"))
    try:
        _extract_archive(temp_path, staging)
        _validate_dataset(staging)
        dest_dir.mkdir(parents=True, exist_ok=True)
        for source in sorted(staging.rglob("*")):
            if not source.is_file():
                continue
            target = dest_dir / source.relative_to(staging)
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(source, target)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
        temp_path.unlink(missing_ok=True)


def _new_temp_path(dest_dir: Path) -> Path:
    handle, name = tempfile.mkstemp(
        dir=dest_dir, prefix=f".{DATASET_SLUG}.", suffix=".part"
    )
    os.close(handle)
    return Path(name)


def _dataset_is_complete(dest_dir: Path) -> bool:
    """Return True when every expected file is already on disk and non-empty."""
    return all(
        (dest_dir / name).is_file() and (dest_dir / name).stat().st_size > 0
        for name in REQUIRED_FILES
    )


def download_dataset(
    dest_dir: str | Path | None = None,
    *,
    version: str | None = None,
    force: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
    progress: ProgressCallback | None = None,
) -> Path:
    """Download and extract the whole dataset into ``dest_dir`` (default ``dataset/raw``).

    Returns the destination directory. A complete existing copy is left alone
    unless ``force`` is set, so repeat runs make no network request.
    """
    if retries < 1:
        raise DownloadError("--retries must be at least 1.")
    if timeout <= 0:
        raise DownloadError("--timeout must be positive.")

    destination = _resolve_dest_dir(dest_dir)
    if _dataset_is_complete(destination) and not force:
        return destination

    destination.parent.mkdir(parents=True, exist_ok=True)
    url = build_url(version)
    session = _create_session()
    try:
        for attempt in range(1, retries + 1):
            temp_path = _new_temp_path(destination.parent)
            try:
                _stream_to_temp(session, url, timeout, temp_path, progress)
                _finalise(temp_path, destination)
                return destination
            except TransientError as exc:
                temp_path.unlink(missing_ok=True)
                if attempt == retries:
                    raise
                delay = (
                    exc.retry_after
                    if exc.retry_after is not None
                    else 0.5 * (2 ** (attempt - 1))
                )
                print(
                    f"warning: attempt {attempt}/{retries} failed ({exc}); "
                    f"retrying in {delay:.1f}s",
                    file=sys.stderr,
                )
                time.sleep(delay)
            except BaseException:
                temp_path.unlink(missing_ok=True)
                raise
    finally:
        session.close()


def _console_progress(quiet: bool) -> ProgressCallback | None:
    if quiet:
        return None
    last = {"percent": -1}

    def report(done: int, total: int | None) -> None:
        if total:
            percent = min(100, done * 100 // total)
            if percent == last["percent"]:
                return
            last["percent"] = percent
            text = f"\rDownloading {DISPLAY_NAME}: {percent:3d}% ({done:,}/{total:,} bytes)"
        else:
            text = f"\rDownloading {DISPLAY_NAME}: {done:,} bytes"
        print(text, end="", flush=True)

    return report


def _count_lines(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            f"Download the full {DATASET_SLUG} dataset from {OWNER} into dataset/raw/."
        )
    )
    parser.add_argument("--dest", help="Destination directory (default: dataset/raw)")
    parser.add_argument(
        "--version", help="Kaggle dataset version number (default: latest)"
    )
    parser.add_argument(
        "--force", action="store_true", help="Overwrite existing dataset files"
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress progress output")
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help="Connect/read timeout in seconds (default: %(default)s)",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=DEFAULT_RETRIES,
        help="Attempts on transient failures (default: %(default)s)",
    )
    args = parser.parse_args(argv)

    destination = _resolve_dest_dir(args.dest)
    progress = _console_progress(args.quiet)
    attempted = False
    try:
        if _dataset_is_complete(destination) and not args.force:
            if not args.quiet:
                print(
                    f"{destination} already contains the dataset; use --force to re-download."
                )
            return 0
        attempted = True
        path = download_dataset(
            args.dest,
            version=args.version,
            force=args.force,
            timeout=args.timeout,
            retries=args.retries,
            progress=progress,
        )
    except DownloadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        if attempted and progress is not None:
            print(flush=True)

    files = sorted(item.name for item in path.iterdir() if item.is_file())
    print(f"Saved {len(files)} files to {path}: {', '.join(files)}.")
    lines = _count_lines(path / "ratings.dat")
    note = (
        "" if lines == EXPECTED_RATINGS else f" (expected about {EXPECTED_RATINGS:,})"
    )
    print(f"ratings.dat has {lines:,} lines{note}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
