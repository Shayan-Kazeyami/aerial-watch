# r187 study: no transmission MSAA patch

The r180 single-line patch is deliberately retired in this isolated study.
Official r187 uses `samples: Math.max( 4, capabilities.samples )` with an explicit
requirement to resolve the transmission render target to avoid feedback loops
(three.js issue #26177). No public transmission sample-count option exists here.
All vendor source is byte-identical to official r187; identities and upstream
URLs are in `THREE-R187-PROVENANCE.json` and verified by regression tests.

SMAA still disables canvas and composer MSAA, but not the internal transmission
resolve. This may increase work relative to patched r180. It is a correctness-first
migration decision, not a claimed performance improvement. Captured diagnostics
report the stock clamped sample count and `transmissionPatchActive: false`.
