# AutoLogup

AutoLogup is a small desktop tool for inspecting log files from different sources in one place.

It can load multiple files, normalize common fields, show the raw log line, and let you filter or group the result set. The UI is built with PySide6.

## What it supports

- File formats: `.json`, `.csv`, `.xml`, `.sql`, `.log`, `.txt`
- Combined view for multiple files
- Normalized fields such as `timestamp`, `username`, `ip`, `status`, `method`, `path`, `level`, `message`
- Dynamic fields from the source data, for example `gender`
- Search inside the visible logs
- Grouping by field values
- Advanced filter queries with boolean logic

## Requirements

You need:

- Python 3
- `pip`
- `PySide6`

Install PySide6:

```bash
pip install PySide6
```

If `pip` points to the wrong Python version, use:

```bash
python -m pip install PySide6
```

## OS notes

### Windows

- Install Python from [python.org](https://www.python.org/downloads/)
- During setup, enable `Add Python to PATH`
- Start the app with:

```bash
python main.py
```

If `python` does not work, try:

```bash
py main.py
```

### macOS

- Install Python with Homebrew or from [python.org](https://www.python.org/downloads/)
- Start the app with:

```bash
python3 main.py
```

### Linux

- Install Python 3 and `pip` with your package manager
- Install `PySide6` with `pip`
- On minimal desktop systems, you may also need the usual Qt/X11 desktop packages
- Start the app with:

```bash
python3 main.py
```

## How to use it

1. Start the app.
2. Click `Load Files` and select one or more log files.
3. Browse the combined table view.
4. Select a row to see the formatted details below.
5. Use the filter bar to narrow the result.
6. Press `Ctrl+F` to search inside the visible rows.
7. Use `Group` to group by a field and drill into one value.

## Filter query examples

Simple equality:

```text
status=401
gender=male
protocol=tcp
```

Not equal:

```text
action!=allow
status!=200
```

Substring match:

```text
message contains failed
message contains timeout
```

Starts with:

```text
path startsWith /api
email startsWith admin
```

Numeric or lexical comparisons:

```text
severity>=8
status<500
```

Time ranges:

```text
timestamp >= 2022-03-16 15:58:00
timestamp >= 3/16/2022 15:58:00
```

Regex:

```text
email regex ".*@example\\.com$"
message regex "^failed.*login"
```

Boolean logic:

```text
username=tim AND status=401
gender=male OR gender=female
(username=tim AND status=401) OR message contains timeout
```

Legacy contains syntax is still supported:

```text
message~failed
```

## Notes

- The filter works on both normalized fields and dynamic fields found in the source data.
- Different file formats may expose different fields.
- If a file cannot be parsed, the app keeps running and reports `0` parsed entries for that file.
