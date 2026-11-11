# Frame-by-frame video export

Release: 4567e2c67548a8c32114cc76deeb8ae19491d0c4a7731c6d0dcfb33c974f3511
Viewer revision: 37778368c0b48542f8a4ff8d7bd1837bcbd7dd6badc34bef5bf8a23230c3eedd

- Capture now renders a complete eight-second,30fps WebM independently of live frame cadence, using bounded CPU-owned RGBA frame snapshots to avoid stalled GPU-backed WebCodecs frames.
- Cancellation remains available during encoder setup and rendering. Escape, resize and departure cancel without saving a partial video. View pose, motion settings, controls and keyboard focus restore.
- Opening or closing Capture on a short desktop viewport no longer recenters the camera. Panel-only width and height changes preserve framing; actual viewport changes still refit.
- Older browsers retain the existing live-recording fallback.

Verification: https://github.com/Shayan-Kazeyami/aerial-watch/actions/runs/43070372679
Actual UI export decoded by PyAV/FFmpeg: VP9,360×252,8.000s,240 distinct frames,30fps,seek at6s. Download SHA-256:454c30e4bcb5d744e0618c1ea472c3561b27af0293dc24360743eb4759d3e911. First and final decoded frames visually checked upright and without dialog overlays.
Desktop cancellation/framing checks used640×480 viewport. Mobile checks used430×700 Chromium emulation.25 exporter/codec/readback tests and52 related navigation/explosion/framing/reset tests passed locally. Software-rendered full clip took565 seconds; this is not a hardware or phone performance claim. Physical S24 and hardware WebGPU/WebGL comparison remain unverified.

QA source commit:7e825082a40ec254f012d94dec5f804b724f1137 on qa/offline-watch-video-20261111.
