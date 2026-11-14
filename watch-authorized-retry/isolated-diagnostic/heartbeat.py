"""Diagnostic-only observers. Never redraw, resize, or change viewer state."""
import asyncio, json, time

async def bounded(label, operation, seconds=3):
    started = time.monotonic()
    try:
        value = await asyncio.wait_for(operation(), seconds)
        return {"probe": label, "ok": True, "elapsed": time.monotonic()-started, "value": value}
    except Exception as error:
        return {"probe": label, "ok": False, "elapsed": time.monotonic()-started,
                "error": type(error).__name__ + ": " + str(error)}

async def observe(stop, frame, browser_session, sink, interval=5):
    """Browser-process CDP and frame JS are distinct from screenshot CDP session.

    This is not a completed-paint or GPU-health proof. Save each sample before
    another operation can stall. No repeated screenshot attempts are made.
    """
    while not stop.is_set():
        probes = await asyncio.gather(
            bounded("browser-process", lambda: browser_session.send("Browser.getVersion")),
            bounded("frame-dom", lambda: frame.evaluate("""()=>({
                timeOrigin:performance.timeOrigin, now:performance.now(),
                ready:document.body.dataset.ready,
                cameraReady:document.getElementById('stage')?.dataset.cameraReady,
                canvas:[document.getElementById('assembly-canvas')?.width,
                        document.getElementById('assembly-canvas')?.height]})""")),
            bounded("frame-two-raf", lambda: frame.evaluate(
                "()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(()=>r(performance.now()))))")),
        )
        with sink.open("a") as stream:
            stream.write(json.dumps({"monotonic":time.monotonic(), "probes":probes})+"\n")
        try:
            await asyncio.wait_for(stop.wait(), interval)
        except asyncio.TimeoutError:
            pass
