# Touch-target investigation — 2026-11-13

Production remained unchanged at 0372398e. Do not publish the speculative CSS candidate in this branch.

## Finding
The suspected SVG hit-target defect was not established. A zero-duration CDP drag suppressed the next compatibility click even in a minimal plain HTML canvas plus native SVG button fixture, independent of Aerial Watch. With 100 ms between drag phases, the native click was generated. This is a synthetic-input timing artifact in the tested Chromium environment, not evidence of a physical phone defect.

## Evidence
- Production raw fast-input reproduction, run 43391506479: first icon-center tap had pointer/touch events but no click. A subsequent edge tap worked.
- Speculative CSS candidate, run 43392262575: despite targeting BUTTON rather than SVG, the first tap still failed. Therefore the earlier injected-CSS success was not causal proof.
- Unmodified production paced gestures, run 43392620696: six cases passed (fresh and repeated icon-center touches, with and without prior drag, raw CDP and Playwright touchscreen).
- Minimal native-button fixture, run 43393132556: zero-duration drag failed; 100 ms dwell between drag phases passed.

## QA correction
Removed diagnostic page.add_style_tag pointer-events injection from qa/first-use-20261113 and added realistic drag timing at 74f3a071. Its workflow must pass before any first-use UI promotion. The correction does not relax the expected explosion state.

No physical-device FPS, latency, or phone-input verification is claimed.
