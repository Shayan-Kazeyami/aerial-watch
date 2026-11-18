# REL-03 resolution chooser candidate (frame-by-frame WebCodecs only)

Save video opens a native choice between current view and compact, listing actual output pixel dimensions. Both preserve the watch framing and default eight seconds at 30 fps; no upscale, renderer resize, or HD/device claims. The compact option is bounded to 540 pixels on the long edge and at most 75% of current size. It reduces encoder dimensions and target bitrate, not the work to render the original view. The progress dialog reports frames and an indeterminate finishing phase. Escape/Cancel discard before or during render. Playback duration is distinct from export wall time. Older-browser live recording is unchanged and is not claimed to support discard cancellation or profile choice.

Encoder input frames retain current view dimensions/ownership; the standards-defined VideoEncoder output-dimension scaling applies. The same exact output size goes to both codec configuration and WebM muxer; browser CI must inspect decoded frames before claims.

The candidate runs on a nonproduction branch with exact module overlays on public 145aba only; nothing is deployed.
