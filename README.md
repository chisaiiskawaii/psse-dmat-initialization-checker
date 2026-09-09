# PSS/E DMAT Initialization Checker

Reads POC voltage, active power, and reactive power from every PSS/E `.outx`
file at **4.9000 seconds**, then writes one combined CSV summary.

## Channels

| Channel | Measurement |
|---:|---|
| 5 | POC Voltage |
| 7 | POC Active Power |
| 9 | POC Reactive Power |

## Folder structure

Folder names may vary. Only the `PSSE` folder name and `.outx` extension are
fixed.

```text
Output/
├── DMAT_Power_Factor_Reference/
│   ├── D163_2S/
│   │   └── PSSE/
│   │       └── results.outx
│   └── Any_Other_Test_Name/
│       └── PSSE/
│           └── results.outx
└── Any_Other_DMAT_Study_Name/
    └── Any_Test_Number/
        └── PSSE/
            └── another_file.outx
```

## Run

### Recommended: drag and drop

Drag one DMAT study folder, such as `DMAT_Power_Factor_Reference`, onto:

```text
DROP_OUTPUT_FOLDER_HERE.bat
```

This scans every `<test>/PSSE/*.outx` below that DMAT folder. The summary is
saved as `DMAT_Initialization_Summary.csv` beside the Python file in the
`psse-dmat-initialization-checker` program folder. Dragging the higher-level
`Output` folder is still supported when a combined summary across multiple
DMAT studies is wanted.

The launcher starts Python 2.7 with the configured PSS/E 34.5 environment,
displays progress for every OUTX file, and keeps the window open when processing
finishes. This avoids a folder-selection window being hidden behind VS Code.

The program first tries the current Python environment, then automatically
searches common `C:\Program Files\PTI\PSSE...` locations for `dyntools.py`.

```bat
python dmat_initialization_checker.py
```

### PSS/E 34.5 and VS Code

Open `dmat_initialization_checker.py` in VS Code and select **Run Python File**.
It is safe if VS Code initially uses Python 3.14: the script automatically
restarts itself using:

```text
C:\Python27\python.exe
```

The Python file configures these PSS/E paths internally:

- `C:\Python27\python.exe`
- `C:\Program Files (x86)\PTI\PSSE34\PSSPY27`
- `C:\Program Files (x86)\PTI\PSSE34\PSSBIN`
- `%USERPROFILE%\Downloads\Temporary\_Script\_Spotswood\Temporary\_Script\_Spotswood\dyntools.py`

The configuration applies only to the checker process and does not change the
computer's global Python or VS Code settings. For step-through debugging, select
`C:\Python27\python.exe` using **Python: Select Interpreter** first; VS Code does
not automatically attach its debugger to the relaunched child process.

The switch to Python 2.7 happens before `dyntools` is imported. If the configured
copy of `dyntools.py` has moved, the checker also performs a bounded search below
the current user's Downloads folder.

A folder picker opens. Select a DMAT study folder or `Output`. The program
creates and opens the summary beside the Python file:

```text
psse-dmat-initialization-checker\DMAT_Initialization_Summary.csv
```

You may also provide the folder on the command line:

```bat
python dmat_initialization_checker.py "C:\Project\Output"
```

### If `dyntools` still cannot be imported

Python must match a version supported by the installed PSS/E release. Open the
PSS/E Command Prompt from the Windows Start menu, change to this project folder,
and run the script there. Alternatively, set `PSSPYTHON_PATH` to the folder
containing `dyntools.py` before running it:

```bat
set "PSSPYTHON_PATH=C:\Program Files\PTI\PSSE35\<version>\PSSPY39"
python dmat_initialization_checker.py
```

Replace `<version>` and `PSSPY39` with the directories actually present on the
computer. For example, `PSSPY39` requires Python 3.9.

## Status meaning

- `READ OK`: all three requested channels were present and contained finite
  values at the nearest sample to 4.9000 seconds.
- `FAIL`: the file could not be read, the time/channel was missing, or a value
  was NaN/infinite.

Because expected active and reactive power differ between DMAT tests, the
program reports the measured P/Q/V without assuming universal pass limits.
Compare these values with each test's intended initialization setpoints.
