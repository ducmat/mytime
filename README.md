# mytime
Time recorder

[![Build and Test Python application](https://github.com/ducmat/mytime/actions/workflows/python-app.yml/badge.svg?branch=main)](https://github.com/ducmat/mytime/actions/workflows/python-app.yml)

[![Pylint](https://github.com/ducmat/mytime/actions/workflows/pylint.yml/badge.svg?branch=main)](https://github.com/ducmat/mytime/actions/workflows/pylint.yml)

## Run

```bash
python -m pip install -r requirements.txt
python app.py
```

Then open: `http://127.0.0.1:8000`

## Features

- Create and list work activities
- Start and stop time tracking for an activity
- Local YAML database at `mytime.yml`
- Export monthly CSV reports to `reports/report-YYYY-MM.csv`

## Test

Run all tests using pytest:

```bash
pytest
```
