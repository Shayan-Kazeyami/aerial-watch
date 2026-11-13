export function createAssemblyMeshRegistry(){
 let root=null,dirty=true,disposed=false,meshes=[],nodes=new Set();
 const invalidate=()=>{dirty=true;};
 const unwatch=node=>{node.removeEventListener('childadded',invalidate);node.removeEventListener('childremoved',invalidate);};
 return {
  collect(nextRoot){
   if(disposed)return [];
   if(root!==nextRoot){for(const node of nodes)unwatch(node);nodes.clear();root=nextRoot;dirty=true;}
   if(!dirty)return meshes;
   dirty=false;const nextNodes=new Set(),nextMeshes=[];
   root?.traverse(node=>{nextNodes.add(node);if(node.isMesh)nextMeshes.push(node);if(!nodes.has(node)){node.addEventListener('childadded',invalidate);node.addEventListener('childremoved',invalidate);}});
   for(const node of nodes)if(!nextNodes.has(node))unwatch(node);
   nodes=nextNodes;meshes=nextMeshes;return meshes;
  },invalidate,
  dispose(){if(disposed)return;for(const node of nodes)unwatch(node);nodes.clear();meshes=[];root=null;disposed=true;}
 };
}
