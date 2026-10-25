// A bfcache entry retains GPU resources and pending loads. A true departure
// aborts network work, cancels animation and disposes the scene exactly once.
export function createViewerLifecycle({pause=()=>{},resume=()=>{},dispose=()=>{},controller=new AbortController()}={}){
  let disposed=false,suspended=false;
  return {
    get signal(){return controller.signal;},get disposed(){return disposed;},
    hide({persisted=false}={}){if(disposed)return;pause();suspended=true;if(!persisted){disposed=true;controller.abort();dispose();}},
    show(){if(disposed)return false;if(suspended){suspended=false;resume();}return true;},
  };
}
