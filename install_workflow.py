"""Run locally once after uploading/extracting the project; creates required GitHub path."""
from pathlib import Path
import shutil
root=Path(__file__).resolve().parents[1]
target=root/'.github/workflows/monthly-update.yml'
if target.exists():
    raise SystemExit('Target already exists: inspect it before replacing; nothing overwritten.')
target.parent.mkdir(parents=True,exist_ok=True)
shutil.copyfile(root/'automation/monthly-update.yml',target)
print('Created .github/workflows/monthly-update.yml. Commit and push this file to GitHub.')
