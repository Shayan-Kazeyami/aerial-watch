# Compact mobile Explode candidate (unpublished)
Baseline51e744f388b6989632e125d50090f119ce36bd8781a9cb16587ecb3f5a7d2aad.
Changed first-party files: atelier-preview.js (only Explode template; stable IDs/listeners), atelier-preview.css (append-only compact scoped rules). No production source modified.
Layout:44px title/percentage/close row and44px slider+Assemble+Full row,12px vertical padding plus borders (~102px total). Both endpoint actions remain available after partial adjustment. Desktop retains full labels/actions. Mobile uses Assemble/Full with explicit accessible Reassemble/Explode fully labels. Range label/help retained programmatically; lengthy status visually hidden. Canvas/camera/model untouched.
Run node --check compact-explode-qa/atelier-preview.js and node compact-explode-qa/source-check.mjs. Static checks pass; layout-fixture.html is generated for isolated screenshot inspection. measure.mjs exports a Playwright measurement helper; actual browser QA remains pending.

CI acceptance checklist:
- Real viewer at360x800,430x932,932x430,desktop1440x900. Open Explode and await amount1.
- Mobile panel height<=130, no panel vertical or page horizontal overflow, target boxes44pxminimum, range visible usable width>=100px. Verify no title/value/action overlap, close remains visible. Landscape canvas remains usable next to compact right sheet.
- Set slider37 through input event then real pointer drag; amount tracks without reload. Full returns100; Assemble returns0; Full can explode again without closing panel.
- ArrowLeft/ArrowRight/Home/End on focused range; actual keyboard behavior and dispatch preserved.
- Close returns focus to opener; reopening at partial amount does not reset unexpectedly. Saved configuration retains explode amount and mode, including saved0.
- Capture canvas DOM identity, buffer dimensions, camera and target before/after opening/closing. No change induced by panel. Compare mode switching and reset behavior with baseline.
- Portrait/landscape orientation change while open: layout adapts, hidden Full label stays programmatically named, no stale focus/amount.
- Desktop screenshot parity except explicit accessible range help and button labels (visual labels unchanged).
