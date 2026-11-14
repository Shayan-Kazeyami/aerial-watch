# Matched published-e79 bytes versus frozen0116 diagnostic

Two bounded jobs: desktop1280x800 and mobile430x932, DPR1. Each runner launches
one fresh Chromium per release, same arguments/viewport/touch configuration,
fixed order published-e79 then frozen0116, no automated retry. Both builds are
served locally to remove public-network versus local transport confounding.
This is a published-baseline-bytes comparison, NOT public-live runtime census.

The checkout root must equal exact published b84 entry bytes. Frozen build's
existing builder verifies baseline closure before creating0116. prepare.py guards
published entry equality, manifest identities, module SHA256 and viewer digest.
Each browser independently fetches/hashes its actual viewer module and asserts
boot digest, expected release in iframe URL, same iframe query parameters.

Both real root wrappers use their existing mobile viewport metadata. Test logs
and asserts host viewport, iframe innerWidth, stage dimensions, Efficient and
Balanced backing dimensions. Mobile430x760→645x1140; desktop1280x546→1920x819.
Same real quality UI and CDP visible-stage clipping/nonblank-image gate remain.
No renderer-state source injection, route interception, forced clicks, lowered
quality, paused motion, or screenshot suppression. Read-only supported app
snapshot request waits for full leather detail with identical verified normal
identity before capture, removing the progressive-upgrade state difference.

Actual browser product and existing WebGL2 context/unmasked renderer are read,
not inferred from launch flags; null renderer identity fails the comparison.
Motion and initial view/camera/target must match
(camera tolerance0.0001); differences block matched-comparison acceptance.
Dynamic hand clock phase can differ; these are visual gates, not pixel-equality
tests. Initial camera/target equality is not proof of capture-matrix twins.
No periodic renderer heartbeat. External process sampling15s persists
no-process cases. ps%CPU is lifetime-average; RSS sum is not private/GPU memory.

Each release arm has1100s bound, captures180s, normal cleanup30s. Job50min envelope
includes setup and two bounded arms. Action logs carry arm prefix and distinguish
clip preflight, capture dispatch, completion, nested timeout, outer deadline and
cleanup failure. Capture outcomes and cleanup outcomes remain separate; neither
failure is hidden. Diagnostic passed remainsfalse; original release gates remain
required. If a build completes while cleanup fails it is still a failed job.
If baseline normal cleanup fails, skip candidate rather than running alongside
potential surviving baseline processes. No forced kill or cleanup retry is used;
this can yield baseline-only evidence and an explicit comparability blocker.

Single observations cannot establish a statistically reliable regression. Fixed
order/runner load, different release payloads and motion phase remain limits.
If initial cameras differ or visual/readiness gates fail, report the mismatch,
not a measured matched rendering regression. No production changes are included.

Local validation:9 mocked/static tests, Python compilation, exact baseline and
candidate identity preflight using verified local bytes. No browser run claimed
until CI evidence has been downloaded, hashes verified and PNGs inspected.
