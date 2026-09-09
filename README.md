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

Use the Python environment configured for your installed PSS/E version so that
`dyntools` is available.

```bat
python dmat_initialization_checker.py
```

A folder picker opens. Select `Output`. The program creates and opens:

```text
Output\DMAT_Initialization_Summary.csv
```

You may also provide the folder on the command line:

```bat
python dmat_initialization_checker.py "C:\Project\Output"
```

## Status meaning

- `READ OK`: all three requested channels were present and contained finite
  values at the nearest sample to 4.9000 seconds.
- `FAIL`: the file could not be read, the time/channel was missing, or a value
  was NaN/infinite.

Because expected active and reactive power differ between DMAT tests, the
program reports the measured P/Q/V without assuming universal pass limits.
Compare these values with each test's intended initialization setpoints.
