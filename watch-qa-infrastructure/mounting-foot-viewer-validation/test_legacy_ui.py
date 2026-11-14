import asyncio,unittest,hashlib,json,re
from pathlib import Path
from legacy_ui_actions import pause_visible_motion,set_visible_finish
from test_ui_actions import Page,op
Q=Path(__file__).resolve().parent
class LegacyUI(unittest.TestCase):
 def test_running_uses_native_visible_button(self):
  p=Page('true');asyncio.run(pause_visible_motion(p,op));self.assertEqual([x[0]for x in p.events if x[1]=='click'],['#play-motion']);self.assertNotIn('force',repr(p.events))
 def test_paused_does_not_toggle(self):
  p=Page('false');asyncio.run(pause_visible_motion(p,op));self.assertFalse(any(x[1]=='click'for x in p.events))
 def test_native_finish(self):
  p=Page('false');asyncio.run(set_visible_finish(p,op,True));self.assertEqual([x[0]for x in p.events if x[1]=='check'],['#finish'])
 def test_exact_shell_only_importmap(self):
  rid='e79b22365b4874327d308eca789326fbea0da8d717ffca20da80b611e36b39c6';original=(Q/'published-legacy-shell.html').read_bytes();derived=(Q/'qa-legacy-viewer/preview-b/releases'/rid/'assembly-review.html').read_bytes();pattern=rb'<script type="importmap">(.*?)</script>';a=re.search(pattern,original).group(1);b=re.search(pattern,derived).group(1);self.assertEqual(derived.replace(b,a),original);self.assertEqual(hashlib.sha256(original).hexdigest(),'69353b26460eb00d5151e32ef2dae2a154825128e73a204212a4c49fdc86a2df');self.assertNotIn(b'atelier-live',original);self.assertNotIn(b'runtime-bridge',original)
if __name__=='__main__':unittest.main()
