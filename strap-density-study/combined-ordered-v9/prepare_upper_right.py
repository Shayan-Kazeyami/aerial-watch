from pathlib import Path
import shutil,subprocess,sys
D=Path('strap-density-study').resolve();S=D/'shell/ordered-v9';O=D/'combined-ordered-v9/upper-right';O.mkdir(parents=True,exist_ok=True)
for name in ['stitched-new.npz','outside-0.npz','outside-1.npz','outside-2.npz']:shutil.copyfile(S/name,O/name)
s=(D/'shell/attributes_ordered.py').read_text().replace("O=D/'shell/ordered-v9'","O=D/'combined-ordered-v9/upper-right'")
s=s.replace('new=np.concatenate([t,n,uv],2);old=',"new=np.concatenate([t,n,uv],2);np.savez_compressed(O/f'new-patch-{mi}.npz',triangles=new.astype('<f4'));old=")
p=O/'attributes_patch.py';p.write_text(s);subprocess.run([sys.executable,str(p)],check=True)
