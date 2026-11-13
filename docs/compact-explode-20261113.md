# Compact mobile Explode controls

The mobile Explode panel now measures 102 CSS pixels instead of roughly 220, leaving about 118 pixels more of the scene visible. The change is restricted to narrow screens and short landscape layouts. Desktop presentation is retained.

The range, full-explosion and reassembly controls remain available. All touch targets are at least 44 pixels. Accessible names and range help remain; compact visual order matches keyboard order. No geometry, materials, camera, quality settings, explosion hierarchy or interaction event handlers changed. The panel overlays the existing canvas without resizing it.

Exact immutable release `ce5580ac6f1299485a507149235bee5135360b538564d3d28921d72da84b415b` passed run 43423041919 at QA commit `1115c11fa6ceb856826976e34c3e5525512ab54b`. Actual rendered tests covered 430×932, 360×800, 932×430, 740×360 and 1440×1000; slider touch, keyboard Home/End/arrows, immediate input, both endpoint actions, close/reopen/focus return, no overflow/title overlap, stable canvas, no navigation/model redownload and no JavaScript errors. Actual portrait, landscape and desktop screenshots were inspected.

A prior route-patched candidate passed all four mobile cases but hit a 90-second desktop capture timeout; its fallback image was usable. The exact release subsequently passed all five cases under the original limit. A separate repeat allows up to 300 seconds per screenshot; that timeout adjustment changes only QA, not runtime or acceptance thresholds.

These are Chromium SwiftShader functional/layout tests, not physical-phone latency or hardware WebGPU measurements. Prior release 51e744f3 and its recovery backup remain available for rollback. Public deployment verification is a separate gate.
