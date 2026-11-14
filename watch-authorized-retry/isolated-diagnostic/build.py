"""Guarded derived harness. Does not modify original source or any release bytes."""
import hashlib, pathlib, json
ROOT=pathlib.Path(__file__).resolve().parent
SOURCE=ROOT.parents[1]/'coordinated-release-successor/ui-check.py'
original=SOURCE.read_bytes()
assert hashlib.sha256(original).hexdigest()=='c52b78dfcb389eca2c570f02c66a908fc2eb227239277b33bb55950a9cf9373c'
s=original.decode()
def replace(old,new):
 global s
 assert s.count(old)==1,old
 s=s.replace(old,new)
replace('from PIL import Image, ImageStat','from PIL import Image, ImageStat\nfrom heartbeat import observe\nMODE=os.environ["DIAG_MODE"];assert MODE in ["behavior", "repeated-capture", "fresh-quality"]\nFRESH=os.getenv("DIAG_QUALITY","efficient");assert FRESH in ["efficient","balanced","detail","studio"]')
replace("O=Q/('evidence-ui-'+KIND)","O=pathlib.Path(__file__).resolve().parent/('evidence-'+MODE+'-'+KIND+('-'+FRESH if MODE=='fresh-quality' else ''))")
replace("frame=None", "frame=None;heartbeat_task=None;heartbeat_stop=asyncio.Event();screenshot_pending=False")
replace("cdp=await context.new_cdp_session(host)", "cdp=await context.new_cdp_session(host)\n   browser_probe=await browser.new_browser_cdp_session()\n   heartbeat_task=asyncio.create_task(observe(heartbeat_stop,frame,browser_probe,O/'heartbeat.jsonl'))")
replace("before=await settle(name+'-capture');path=O/(name+'.png')", "before=await settle(name+'-capture');path=O/(name+'.png')\n    if MODE=='behavior':\n     R.setdefault('omittedVisualChecks',[]).append(name);return\n    nonlocal screenshot_pending\n    screenshot_pending=True\n    (O/'capture-start.json').write_text(json.dumps({'name':name,'monotonic':time.monotonic(),'before':before},indent=2))")
replace("path.write_bytes(base64.b64decode(shot['data']));", "screenshot_pending=False\n    (O/'capture-completed.json').write_text(json.dumps({'name':name,'monotonic':time.monotonic()},indent=2))\n    path.write_bytes(base64.b64decode(shot['data']));")
replace("for quality in ['efficient','balanced','detail','studio','efficient']:", "for quality in ([FRESH] if MODE=='fresh-quality' else ['efficient','balanced','detail','studio','efficient']):")
replace("behavior=await explode_reset('quality-'+quality,quality);assert behavior['qualityAfterReset']==R['initial']['renderQuality'],behavior", "behavior=await explode_reset('quality-'+quality,quality) if MODE!='fresh-quality' else {'diagnostic':'fresh selection/capture only; no lifecycle coverage'}\n    if MODE!='fresh-quality':assert behavior['qualityAfterReset']==R['initial']['renderQuality'],behavior")
replace("await capture('final-efficient');R['final']=await frame.evaluate(SNAP);assert not R['errors'];R['passed']=True", "if MODE!='fresh-quality':await capture('final-efficient')\n   R['final']=await frame.evaluate(SNAP);assert not R['errors']\n   R['diagnosticCompleted']=True;R['mode']=MODE\n   R['passed']=False # A diagnostic never passes the original combined release gate.\n   R['behaviorSequenceCompleted']=MODE=='behavior' and len(R['qualityCycles'])==5\n   R['visualDiagnosticCompleted']=MODE!='behavior'")
replace("try:await host.screenshot(path=str(O/'final-page.png'),animations='disabled',timeout=30000)\n   except Exception as e:R['finalScreenshotError']=repr(e);(O/'report.json').write_text(json.dumps(R,indent=2))\n   await browser.close()", "# Do not queue another compositor screenshot after a pending/failed one.\n   R['screenshotPendingAtExit']=screenshot_pending\n   heartbeat_stop.set()\n   if heartbeat_task:\n    try:await asyncio.wait_for(heartbeat_task,8)\n    except Exception as e:R['heartbeatShutdownError']=repr(e)\n   (O/'report.json').write_text(json.dumps(R,indent=2))\n   await asyncio.wait_for(browser.close(),30)")
out=ROOT/'ui-check-diagnostic.py';out.write_text(s)
(ROOT/'source-proof.json').write_text(json.dumps({'originalSHA256':hashlib.sha256(original).hexdigest(),'derivedSHA256':hashlib.sha256(out.read_bytes()).hexdigest(),'originalUnchanged':SOURCE.read_bytes()==original,'remoteRun':False,'releaseGate':'Never passed by diagnostic harness'},indent=2))
print(out)
