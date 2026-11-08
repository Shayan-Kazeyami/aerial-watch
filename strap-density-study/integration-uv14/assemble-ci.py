"""Execute reviewed two-phase UV14 assembler on reconstructed validated density faces."""
from pathlib import Path
import sys,subprocess,os
assembler=Path(sys.argv[1]);inputs=Path(sys.argv[2]).resolve();out=Path(sys.argv[3]).resolve();source=Path(sys.argv[4]).resolve();out.mkdir(parents=True,exist_ok=True);s=assembler.read_text()
assert s.count("O=D/'combined-uv14'")==1;s=s.replace("O=D/'combined-uv14'",f'O=Path({str(out)!r});INPUT=Path({str(inputs)!r})')
assert s.count("src=np.load(D/f'input-{mesh}-{mi}.npz')")==1;s=s.replace("src=np.load(D/f'input-{mesh}-{mi}.npz')","src=np.load(INPUT/f'input-{mesh}-{mi}.npz')")
assert s.index('temp,owners=split(temp)')<s.index("ret[:,:,:8]=ret[:,:,:8].astype('<f4').astype(float)")<s.index('temp,owners=uv_splitter(name)(temp)');assert 't,more=second(t)'not in s
(out/'assemble.executed.py').write_text(s);exec(compile(s,str(assembler),'exec'),{})
normal=Path('strap-density-study/combined-wide-v13/normalize_arrays.py').read_text();assert normal.count("O=D/'combined-wide-v13'")==1;normal=normal.replace("O=D/'combined-wide-v13'",f'O=Path({str(out)!r})');exec(compile(normal,'source-aware-normalization','exec'),{})
os.environ.update(STRAP_STUDY_DIR=str(out),STRAP_SOURCE_ASSET_DIR=str(source));subprocess.run([sys.executable,'strap-density-study/ci/all-ends/export_all.py'],check=True);subprocess.run([sys.executable,'strap-density-study/ci/compact_export.py'],check=True)
