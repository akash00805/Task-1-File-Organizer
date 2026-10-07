from __future__ import annotations

import logging
import os
import time
from pathlib import Path

import pyzipper


TYPE_FOLDERS = {
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff", ".webp", ".svg", ".heic"},
    "Documents": {".pdf", ".doc", ".docx", ".odt", ".rtf", ".txt", ".md", ".csv", ".xls", ".xlsx", ".ppt", ".pptx"},
    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"},
    "Audio": {".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a", ".wma"},
    "Video": {".mp4", ".mkv", ".mov", ".avi", ".wmv", ".webm", ".mpeg", ".mpg"},
}


def category(path: Path) -> str:
    suffix = path.suffix.lower()
    return next((folder for folder, extensions in TYPE_FOLDERS.items() if suffix in extensions), "Other")


def unique_path(path: Path) -> Path:
    """Choose a deterministic free name: name (1).ext, name (2).ext, ..."""
    if not path.exists():
        return path
    counter = 1
    while True:
        candidate = path.with_name(f"{path.stem} ({counter}){path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def old_files(source: Path, archive: Path, cutoff: float, target: Path) -> list[Path]:
    result = []
    for path in source.rglob("*"):
        resolved = path.resolve()
        if not path.is_file() or resolved == archive.resolve() or target == resolved or target in resolved.parents:
            continue
        try:
            if path.stat().st_atime < cutoff:
                result.append(path)
        except OSError:
            continue
    return sorted(result, key=lambda p: str(p).casefold())


def organize(source: Path, target: Path, password: str | None, dry_run: bool,
             logger: logging.Logger, now: float | None = None) -> list[str]:
    """Organize immediate source files, then archive old files before deleting them."""
    source, target = source.expanduser().resolve(), target.expanduser().resolve()
    if not source.is_dir():
        raise NotADirectoryError(f"Source directory does not exist: {source}")
    target.mkdir(parents=True, exist_ok=True) if not dry_run else None
    archive = target / "Deep_Archive.zip"
    cutoff = (time.time() if now is None else now) - 365 * 24 * 60 * 60
    archived = old_files(source, archive, cutoff, target)
    archived_set = {p.resolve() for p in archived}
    actions: list[str] = []

    for path in sorted(source.iterdir(), key=lambda p: p.name.casefold()):
        if not path.is_file() or path.resolve() in archived_set:
            continue
        destination = unique_path(target / category(path) / path.name)
        action = f"MOVE {path} -> {destination}"
        actions.append(action)
        logger.info(action)
        if not dry_run:
            destination.parent.mkdir(parents=True, exist_ok=True)
            path.rename(destination)

    if archived:
        if not password:
            message = f"ARCHIVE SKIPPED {len(archived)} old file(s): set --password or FILE_ORGANIZER_PASSWORD"
            actions.append(message)
            logger.warning(message)
        else:
            action = f"ARCHIVE {len(archived)} old file(s) -> {archive} (AES-256 encrypted)"
            actions.append(action)
            logger.info(action)
            for path in archived:
                logger.info("  ARCHIVE ITEM %s", path)
            if not dry_run:
                archive.parent.mkdir(parents=True, exist_ok=True)
                temp_archive = archive.with_name(archive.name + ".tmp")
                try:
                    with pyzipper.AESZipFile(temp_archive, "w", compression=pyzipper.ZIP_DEFLATED,
                                             encryption=pyzipper.WZ_AES) as zf:
                        zf.setpassword(password.encode("utf-8"))
                        zf.setencryption(pyzipper.WZ_AES, nbits=256)
                        for path in archived:
                            zf.write(path, arcname=path.relative_to(source))
                    with pyzipper.AESZipFile(temp_archive, "r") as zf:
                        zf.setpassword(password.encode("utf-8"))
                        bad = zf.testzip()
                        expected = {str(p.relative_to(source)).replace("\\", "/") for p in archived}
                        if bad is not None or set(zf.namelist()) != expected:
                            raise RuntimeError(f"Archive verification failed: {bad or 'member list mismatch'}")
                    final_archive = unique_path(archive)
                    os.replace(temp_archive, final_archive)
                    logger.info("ARCHIVE VERIFIED %s", final_archive)
                    for path in archived:
                        path.unlink()
                        logger.info("DELETE ORIGINAL %s", path)
                finally:
                    if temp_archive.exists():
                        temp_archive.unlink()
    return actions
