from pathlib import Path
import shutil
R=Path(__file__).resolve().parents[2];D=Path('strap-density-study');(D/'end-shell-audit').mkdir(parents=True,exist_ok=True);(D/'shell/uv-v10').mkdir(parents=True,exist_ok=True)
for i in range(3):shutil.copyfile(R/f'input-0-{i}.npz',D/f'input-0-{i}.npz')
