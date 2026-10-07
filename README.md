# File Organizer

A Python command-line utility that sorts files by type and can move files whose **last access time** is older than 365 days into an AES-256 encrypted `Deep_Archive.zip`. It deletes archived originals only after writing and checking the encrypted archive.

## Setup

Requires Python 3.10+.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Usage

Preview the proposed actions first; a dry run never creates folders or changes files:

```powershell
python -m organizer --source "C:\Users\me\Downloads" --target "D:\Organized" --dry-run --log "run.log"
```

Run the organizer. Set the archive password in the environment so it does not appear in command history:

```powershell
$env:FILE_ORGANIZER_PASSWORD = "use-a-long-unique-password"
python -m organizer --source "C:\Users\me\Downloads" --target "D:\Organized" --log "run.log"
Remove-Item Env:FILE_ORGANIZER_PASSWORD
```

`--password` is also available for automation, but command-line arguments may be visible in process listings. If old files are found and no password is configured, they are left in place and a warning is logged. `--source` and `--target` are required; the log is optional.

## Behavior

- Sorts immediate files in the source into `Images`, `Documents`, `Archives`, `Audio`, `Video`, or `Other` under the target. Unknown extensions go to `Other`.
- Checks files recursively for archive eligibility. Eligibility uses filesystem access time (`atime`), which some filesystems or mount options may not reliably update.
- Files older than 365 days are archived with their relative paths preserved in `Deep_Archive.zip` in the target. If an archive by that name exists, the next free numbered archive name is used.
- Name collisions in category folders are resolved as `name (1).ext`, then `name (2).ext`, and so on. Existing files are not overwritten.
- The encrypted archive uses WinZip AES-256. The program validates the encrypted archive and its member list before deleting source files. If verification or archive creation fails, source originals remain.
- Archive creation and deletion are sequential; sorting is performed before archival. Use a backup and inspect the dry-run log before the first live run.

## Sample artifacts

- [Sample dry-run log](examples/sample-run.log)
- [Before screenshot](screenshots/before.svg)
- [After screenshot](screenshots/after.svg)

The screenshots are illustrative mockups of the sample file listing and planned result, not captures from a user's machine. Generate a fresh log for your own directories with `--dry-run --log run.log`.
