"""Package code and verified artifacts, excluding runtime logs and tokens."""
import hashlib
import json
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
assert json.loads((ROOT/'output/verification.json').read_text())['passed']
destination=ROOT.parent/'deliverables'
destination.mkdir(exist_ok=True)
excluded={'logs','__pycache__','.ipynb_checkpoints','.git'}
files=sorted(p for p in ROOT.rglob('*') if p.is_file() and not any(part in excluded for part in p.relative_to(ROOT).parts) and p.name!='delivery_manifest.json')
manifest={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
(ROOT/'output/delivery_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
files.append(ROOT/'output/delivery_manifest.json')
target=destination/'PAI_step1_53772.zip'
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
    for p in files: z.write(p,Path(ROOT.name)/p.relative_to(ROOT))
with zipfile.ZipFile(target) as z:
    assert z.testzip() is None
    assert not any('/logs/' in name or '__pycache__' in name for name in z.namelist())
print(json.dumps({'archive':str(target),'files':len(files),'bytes':target.stat().st_size},ensure_ascii=False))
