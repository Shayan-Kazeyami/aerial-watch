"""Diagnostic-only observation; never changes viewer state or release approval."""
import asyncio, json, time, subprocess
from pathlib import Path

def record(path, event, **data):
    with Path(path).open('a') as stream:
        stream.write(json.dumps({'event':event,'monotonic':time.monotonic(),**data})+'\n')

async def action(path, name, operation):
    record(path,'action-start',name=name)
    try:
        result=await operation()
    except asyncio.CancelledError:
        record(path,'action-cancelled',name=name,attribution='Cancellation observed; caller must attribute overall timeout versus external cancellation')
        raise
    except Exception as error:
        record(path,'action-failed',name=name,error=repr(error))
        raise
    else:
        record(path,'action-completed',name=name)
        return result

async def bounded_run(path, operation, seconds):
    record(path,'run-start',timeoutSeconds=seconds)
    deadline=asyncio.timeout(seconds)
    try:
        async with deadline:
            return await operation()
    except TimeoutError:
        record(path,'run-timeout' if deadline.expired() else 'nested-operation-timeout',timeoutSeconds=seconds,passed=False)
        raise
    except asyncio.CancelledError:
        record(path,'run-external-cancellation',passed=False)
        raise
    finally:
        record(path,'run-exit')

def sample_processes(run=subprocess.run):
    # ps status1 means no matching processes, not observer termination.
    result=run(['ps','-C','chrome,chromium,chromium-browser,chrome-headless,headless_shell','-o','pid,ppid,pcpu,rss,comm'],capture_output=True,text=True,timeout=3,check=False)
    return {'psReturnCode':result.returncode,'processes':result.stdout,'stderr':result.stderr,'noMatchingProcesses':result.returncode==1}

async def sample_loop(stop, path, interval=5, sample=sample_processes):
    while not stop.is_set():
        try:
            result=await asyncio.to_thread(sample)
            try: result['meminfo']=Path('/proc/meminfo').read_text()
            except OSError as error: result['meminfoError']=repr(error)
            record(path,'process-sample',**result)
        except Exception as error:
            record(path,'process-sample-error',error=repr(error))
        try: await asyncio.wait_for(stop.wait(),interval)
        except TimeoutError: pass

def traced(path, label):
    def decorate(function):
        async def wrapped(*args, **kwargs):
            name=label+(':'+str(args[0]) if args and isinstance(args[0],str) else '')
            return await action(path,name,lambda:function(*args,**kwargs))
        return wrapped
    return decorate
