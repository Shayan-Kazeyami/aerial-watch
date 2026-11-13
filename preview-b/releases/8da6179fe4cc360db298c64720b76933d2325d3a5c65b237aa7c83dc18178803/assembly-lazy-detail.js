// Defer optional display detail until it is first shown; preserve the same
// instance on later visits so its appearance and disposal remain stable.
export function createLazyDetail({create,attach}) {
 let value=null,disposed=false;
 return {
  get value(){return value;},
  ensure(){
   if(disposed)throw new Error('Detail already disposed.');
   if(!value){const next=create();try{attach(next);}catch(error){next.dispose();throw error;}value=next;}
   return value;
  },
  dispose(){if(disposed)return;disposed=true;value?.dispose();value=null;}
 };
}
