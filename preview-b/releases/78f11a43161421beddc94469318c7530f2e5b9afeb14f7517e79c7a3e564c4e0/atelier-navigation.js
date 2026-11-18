// Tool panels are temporary. Opening or closing them must not forget the scene
// task or reactivate its camera, crown or assembly actions.
export const EXPERIENCE_MODES=Object.freeze(['explore','inside','explode','time']);
export function createAtelierNavigation(){
 let experience='explore',tool=null,selectionReturn=null;
 const snapshot=()=>({experience,tool,selectionReturn:selectionReturn?{...selectionReturn}:null});
 return {
  snapshot,
  open(next){
   if(EXPERIENCE_MODES.includes(next))experience=next;
   tool=next==='explore'?null:next;
   if(next!=='selection')selectionReturn=null;
   return snapshot();
  },
  close(){tool=null;return snapshot();},
  select(){
   if(tool!=='selection')selectionReturn={tool,experience};
   tool='selection';return snapshot();
  },
  returnFromSelection(){
   const target=selectionReturn||{experience,tool:experience==='explore'?null:experience};
   experience=target.experience;tool=target.tool;selectionReturn=null;
   return snapshot();
  },
  restore({experience:next='explore',tool:nextTool=null}={}){
   experience=EXPERIENCE_MODES.includes(next)?next:'explore';tool=nextTool;selectionReturn=null;
   return snapshot();
  }
 };
}
