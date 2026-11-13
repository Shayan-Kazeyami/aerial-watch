// Load historical comparison layers only while requested. The caller owns
// asset cancellation and installed resources through its viewer lifecycle.
export function createDeferredComparisonDetails({loadForm,loadArchitecture,onError=()=>{}}={}){
 let needed=false,disposed=false,pending=null,formReady=false,architectureReady=false,failure=null;
 function start(){
  if(disposed||!needed||pending||architectureReady||failure)return pending;
  let stage='form';
  pending=Promise.resolve().then(async()=>{
   if(disposed||!needed)return;
   if(!formReady){await loadForm();if(disposed)return;formReady=true;}
   // Switching away during the form transfer must not start its hidden sibling.
   if(disposed||!needed)return;
   stage='architecture';await loadArchitecture();if(!disposed)architectureReady=true;
  }).catch(error=>{
   if(disposed)return;
   failure={stage,message:String(error?.message||error)};
   // Status observers cannot turn a handled asset failure into an orphan rejection.
   try{onError(error,stage);}catch{}
  }).finally(()=>{
   pending=null;
   if(!disposed&&needed&&!failure&&!architectureReady)start();
  });
  return pending;
 }
 return {
  update(value){
   if(disposed)return null;
   value=!!value;
   // A deliberate return to the comparison retries its failed stage, whereas
   // repeated material/visibility refreshes never create a network retry loop.
   if(value&&!needed)failure=null;
   needed=value;return start();
  },
  retry(){if(!disposed)failure=null;return start();},
  snapshot(){return {needed,disposed,loading:!!pending,formReady,architectureReady,failure:failure?{...failure}:null};},
  dispose(){disposed=true;needed=false;}
 };
}
