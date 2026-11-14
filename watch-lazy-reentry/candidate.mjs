export function createLazyDetail({create,attach}) {
 let value=null,disposed=false,creating=false;
 return {
  get value(){return value;},
  ensure(){
   if(disposed)throw new Error('Detail already disposed.');
   if(creating)throw new Error('Detail creation already in progress.');
   if(!value){
    creating=true;let next;
    try{
     next=create();
     if(disposed)throw new Error('Detail already disposed.');
     attach(next);
     if(disposed)throw new Error('Detail already disposed.');
     value=next;
    }catch(error){next?.dispose();throw error;}finally{creating=false;}
   }
   return value;
  },
  dispose(){if(disposed)return;disposed=true;const old=value;value=null;old?.dispose();}
 };
}
