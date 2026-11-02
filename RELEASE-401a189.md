# Tested Aerial release

Frozen source: 401a189fdca6e1ec821b6bb3b19dc39555b468f8; runtime source: 6203da48e9bb1e00ab29f4b17f5293e4fcf1e1d2; source digest: 1bf22f7e2d28eaa4996d4529c4413e0de4a7c7cc5871fff5d0f34abbdf10f802.

Includes r187, native GTAO, tested crown/Reset/loading/strap/metal changes. R5 case stays opt-in. Unaccepted lighting, AA, strap-hide and loading candidates excluded. Existing immutable release namespaces stay unchanged.

To stay within GitHub Pages' 1 GB site limit, six duplicate mutable binary URLs are retired (these old raw URLs return 404):
- `/aerial-watch/assets/automatic.glb` → identical bytes retained at `/aerial-watch/preview-b/releases/68b516d5945b4b20af8bbf98558381891c5f9b3c81390ec2fc8ecdcfcaf6d45b/assets/automatic.glb`
- `/aerial-watch/preview-b/assets/automatic.glb` → identical bytes retained at `/aerial-watch/preview-b/releases/68b516d5945b4b20af8bbf98558381891c5f9b3c81390ec2fc8ecdcfcaf6d45b/assets/automatic.glb`
- `/aerial-watch/assets/manual-a.glb` → identical bytes retained at `/aerial-watch/preview-b/releases/68b516d5945b4b20af8bbf98558381891c5f9b3c81390ec2fc8ecdcfcaf6d45b/assets/manual-a.glb`
- `/aerial-watch/preview-b/assets/manual-a.glb` → identical bytes retained at `/aerial-watch/preview-b/releases/68b516d5945b4b20af8bbf98558381891c5f9b3c81390ec2fc8ecdcfcaf6d45b/assets/manual-a.glb`
- `/aerial-watch/assets/manual-b.glb` → identical bytes retained at `/aerial-watch/preview-b/releases/68b516d5945b4b20af8bbf98558381891c5f9b3c81390ec2fc8ecdcfcaf6d45b/assets/manual-b.glb`
- `/aerial-watch/preview-b/assets/manual-b.glb` → identical bytes retained at `/aerial-watch/preview-b/releases/68b516d5945b4b20af8bbf98558381891c5f9b3c81390ec2fc8ecdcfcaf6d45b/assets/manual-b.glb`

Four legacy loaders now use the identical immutable copies. All eight linked legacy HTML pages remain unchanged. Originals remain in prior Git history; canonical files are retained. No source model, license or active download is removed. Rollback: restore the six original blob SHAs and six text blob SHAs from the parent commit, preserving unrelated release additions.
