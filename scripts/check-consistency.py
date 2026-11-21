"""Run the AKUS read-only discrepancy queries and fail on missing or nonzero counters."""

import argparse
import csv
import io
import re
import subprocess
from pathlib import Path

scripts = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("databases", nargs="+")
args = parser.parse_args()
for database in args.databases:
    if database != "akus" and not re.fullmatch(r"[a-z][a-z0-9_]*_test", database):
        parser.error(f"Expected akus or a named test database, received {database!r}")

queries = []
counters = set()
for group, count in (
    ("quota", 6),
    ("compliance", 7),
    ("employment", 5),
    ("workspace", 4),
):
    sql = (scripts / f"verify-{group}.sql").read_text()
    names = set(
        re.findall(r"^SELECT count\(\*\) AS (\w+)", sql, re.MULTILINE | re.IGNORECASE)
    )
    names.discard("recorded_transfer_movements")
    if len(names) != count or counters.intersection(names):
        raise SystemExit(f"Review the expected discrepancy counters for {group}")
    counters.update(names)
    queries.append(sql)

failed = False
for database in args.databases:
    result = subprocess.run(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "db",
            "psql",
            "-X",
            "-q",
            "--csv",
            "-v",
            "ON_ERROR_STOP=1",
            "-U",
            "akus_demo",
            "-d",
            database,
        ],
        cwd=scripts.parent,
        input="\n".join(queries),
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    )
    rows = csv.reader(io.StringIO(result.stdout))
    found = {}
    for row in rows:
        if len(row) == 1 and row[0] in counters:
            (value,) = next(rows)
            found[row[0]] = int(value)
    print(database)
    for name in sorted(counters):
        print(f"  {name} = {found.get(name, 'MISSING')}")
    failed |= set(found) != counters or any(found.values())
raise SystemExit(int(failed))
