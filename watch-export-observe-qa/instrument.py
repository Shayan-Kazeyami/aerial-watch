"""Fail-closed test overlay for exactly one held immutable export module."""
import hashlib,json,pathlib
P=pathlib.Path(__file__).parent;IDENTITY=json.loads((P/'IDENTITY.json').read_text());RID=IDENTITY['release']
def instrument(source,release):
 b=source.encode('utf-8');spec=IDENTITY['source']
 if release!=RID or len(b)!=spec['sizeBytes'] or hashlib.sha256(b).hexdigest()!=spec['sha256']:raise ValueError('Refusing unrecognized release/source')
 def replace(a,b):
  nonlocal source
  if source.count(a)!=1:raise ValueError('Expected one phase boundary: '+a)
  source=source.replace(a,b)
 replace("   const chunks=[];", "   const chunks=[];const qa=globalThis.__watchExportTestTrace;if(!qa)throw new Error('Test trace missing');qa.note('export-start',{frameCount,width,height});")
 replace("const support=await bounded(session,Encoder.isConfigSupported(proposed),'Video encoder setup');", "qa.begin('encoder-setup');const support=await bounded(session,Encoder.isConfigSupported(proposed),'Video encoder setup');qa.end('encoder-setup');")
 replace("}catch(error){check(session);if(/timed out/.test(error.message))throw error;}", "}catch(error){qa.fail(error);check(session);if(/timed out/.test(error.message))throw error;}")
 replace("     synchronous(renderFrame,[index/frameRate,{index,frameCount,frameRate,context}],'Watch frame render');check(session);", "     qa.begin('render',{index});synchronous(renderFrame,[index/frameRate,{index,frameCount,frameRate,context}],'Watch frame render');qa.end('render');check(session);")
 replace("frame=createFrame(canvas,{timestamp,duration:next-timestamp,alpha:'discard'});encoder.encode(frame,{keyFrame:index===0||index%Math.round(frameRate*2)===0});", "qa.begin('readback',{index});frame=createFrame(canvas,{timestamp,duration:next-timestamp,alpha:'discard'});qa.end('readback');qa.begin('encode-submit',{index});encoder.encode(frame,{keyFrame:index===0||index%Math.round(frameRate*2)===0});qa.end('encode-submit');")
 replace("if(encoder.encodeQueueSize>=4)await bounded(session,encoder.flush(),'Video encoding');", "if(encoder.encodeQueueSize>=4){qa.begin('encode-flush',{index});await bounded(session,encoder.flush(),'Video encoding');qa.end('encode-flush');}")
 replace("await bounded(session,yieldTask(),'Video render scheduling');", "qa.begin('scheduling',{index});await bounded(session,yieldTask(),'Video render scheduling');qa.end('scheduling');")
 replace("    await bounded(session,encoder.flush(),'Video encoding');check(session);", "    qa.begin('encode-final-flush');await bounded(session,encoder.flush(),'Video encoding');qa.end('encode-final-flush');check(session);")
 replace("    const bytes=mux({chunks,width,height,frameRate,durationMs:encodedDurationMs,codec,expectedFrames:frameCount,maxOutputBytes});check(session);", "    qa.begin('finalize');const bytes=mux({chunks,width,height,frameRate,durationMs:encodedDurationMs,codec,expectedFrames:frameCount,maxOutputBytes});qa.end('finalize');check(session);")
 replace("   }finally{\n    session.settled=true;", "   }catch(error){qa.fail(error);throw error;}finally{\n    qa.note('export-settled');session.settled=true;")
 return '// TEST OBSERVABILITY OVERLAY, NOT A DEPLOYABLE RELEASE\n'+source
if __name__=='__main__':
 import sys
 pathlib.Path(sys.argv[2]).write_text(instrument(pathlib.Path(sys.argv[1]).read_text(),RID))
