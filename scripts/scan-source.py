"""Small explicit leak-pattern check; not a replacement for a dedicated secret scanner."""
from pathlib import Path
import argparse
import re

parser = argparse.ArgumentParser()
parser.add_argument('--report', default='docs/qa/secret-scan.md', help='Repository-relative evidence filename')
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
report_path = (root / args.report).resolve()
if not report_path.is_relative_to(root):
    parser.error('Report must stay inside repository')
patterns = [r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----', r'gh[pousr]_[A-Za-z0-9]{30,}', r'AKIA[0-9A-Z]{16}']
paths = [*root.joinpath('apps/api/akus').rglob('*.py'), *root.joinpath('apps/web/src').rglob('*.ts*'), *root.joinpath('infra').glob('*'), root/'compose.yaml', root/'.env.example']
findings = []
for path in paths:
    data = path.read_text()
    if any(re.search(pattern, data) for pattern in patterns):
        findings.append(str(path.relative_to(root)))
report = '# Source secret-pattern check\n\nChecked authored API/frontend/infrastructure files, Compose and .env.example for private-key blocks, GitHub token shapes and AWS access-key IDs. Values are never printed.\n\n'
report += f'Files checked: {len(paths)}. Matching files: {len(findings)}.\n\n'
report += '\n'.join(findings) if findings else 'No matches. Local database fixture credentials are intentional and labeled DEMO. This limited pattern check is not a comprehensive security scan or proof that no secrets exist.\n'
if report_path.exists():
    parser.error('Preserve earlier evidence: choose a new --report path')
report_path.write_text(report)
print(f'Checked {len(paths)} source/config files; matching files: {len(findings)}')
raise SystemExit(bool(findings))
