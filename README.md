# mytime
Time recorder

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

```bash
python -m unittest discover -s tests -q
```
