"""Normal navigation teardown diagnostic, not a forced resource workaround."""
async def normal_unload_then_close(page,browser,traced,unload_seconds=30,close_seconds=30):
    result={'normalUnloadCompleted':False,'unloadFailure':None,'cleanupFailure':None}
    if page is not None:
        try:
            await traced('normal-about-blank-unload',lambda:page.goto('about:blank',wait_until='load',timeout=unload_seconds*1000),unload_seconds)
            result['normalUnloadCompleted']=True
        except Exception as error:result['unloadFailure']=repr(error)
    else:result['unloadFailure']='No page available for normal unload'
    try:await traced('browser-close-after-unload',browser.close,close_seconds)
    except Exception as error:result['cleanupFailure']=repr(error)
    return result
