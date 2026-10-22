# Fast File Search

A lightweight Windows desktop utility for finding files by filename across folders. Built with Python, Tkinter, and CustomTkinter.

## Features

- Search filenames using multiple keywords.
- Filter results by file type (PDF, Excel/CSV, Word, PowerPoint, images, and archives).
- Scan folders in a background thread so the interface stays responsive.
- Cache file indexes locally to speed up repeat searches.
- Open a selected file, reveal it in File Explorer, or copy its full path.
- Light and dark appearance modes.
- Select the folder to scan; the app does not automatically scan a personal or work directory on startup.

## Requirements

- Windows 10 or Windows 11
- Python 3.10 or newer
- The Python package listed in `requirements.txt`

## Run from source

1. Install Python from [python.org](https://www.python.org/downloads/) if it is not already installed. During setup, enable **Add Python to PATH**.
2. Download or clone this repository.
3. Open Command Prompt or PowerShell in the project folder.
4. Install the dependency:

   ```powershell
   py -m pip install -r requirements.txt
   ```

5. Start the app:

   ```powershell
   py fastsearchfile.py
   ```

6. Click **Pilih folder** to select the folder you want to search, type one or more keywords, and optionally choose a file-type filter.

## Cache and privacy

The app indexes filenames and their local paths for the folder you choose. The index cache is stored locally in the current user's application-data directory (normally `%LOCALAPPDATA%\FastSearchFile\file_index.json` on Windows). It is not uploaded or transmitted by this application.

The cache uses JSON rather than Python's executable `pickle` format. You can delete `file_index.json` to clear the local index cache. The cache file is intentionally kept outside this repository so it is not committed with the source code.

**Important:** search results can display full local paths. Do not share screenshots or logs containing private folder names or filenames unless you have checked them first.

## Limitations

- Search matches filenames, not the contents of documents.
- The first scan of a large folder can take time; subsequent scans may benefit from the local cache.
- Files and folders that Windows does not allow the current user to access may be skipped.
- This project has been syntax-checked, but should still be tested on the Windows versions and folder structures you intend to support.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
