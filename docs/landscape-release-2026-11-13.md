# Compact landscape release — 2026-11-13

Release 832a0ce0005cffdf950455dcb578c805724bf92d29a81f9ca209ab59efdead51; QA source 9dea3bb843c1d915f525ee1da8c6bca1b9db1b69.
QA https://github.com/Shayan-Kazeyami/aerial-watch/actions/runs/43397994059
Rollback main 5a2448465bdf287e5c150eab14a5f9a56ab36ab7 and loader watch-home-first-use-7bff2470.js.

One header row, compact centered action dock, and fixed overlay sheets for landscape 568–1050px wide / <=600px tall. Stable canvas across open/closed tools. No renderer, geometry, material, selected quality or animation changes.

Verified actual PNGs at 568×320, 844×390, 932×430 and portrait 390×844; no missing headings. Primary panel controls visible, longer Studio tools intentionally scroll. All primary action hit targets >=44px and center hit-tested. Touch Explode, slider, Reset, Studio tools, Quality, close tested. Stable canvas bounds 568×207, 844×277, 932×317 respectively. At 844×390 this gains 59px canvas height versus prior 218px. Portrait first-use cue, dismissal persistence, Explode and Reset regression pass, zero additional paused frames. No JS errors.

Initial experiments failed visual review despite functional tests: :has() specificity retained portrait height cap, and sticky close row painted over title. Corrected before publication. A software-rasterizer screenshot timeout was fixed by allowing capture time, not weakening input assertions.

Limits: physical-phone FPS, screen reader speech and notched-device safe-area emulation unmeasured. Existing close-up camera framing retained; this is not a full strap framing redesign. Shared assets and their ownership paths retained.
