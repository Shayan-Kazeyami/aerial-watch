// Small focus policies for the existing native controls. No global listeners,
// event cancellation or viewer state changes are installed by this module.
export function closeDisclosureWithFocus(menu,activeElement){
  if(!menu||typeof menu.removeAttribute!=='function')return false;
  const contained=!!activeElement&&typeof menu.contains==='function'&&menu.contains(activeElement);
  const summary=contained?menu.querySelector?.(':scope > summary'):null;
  menu.removeAttribute('open');
  if(typeof summary?.focus!=='function')return false;
  summary.focus({preventScroll:true});
  return true;
}

export function isEditingControl(target){
  const element=target?.nodeType===3?target.parentElement:target;
  if(!element)return false;
  // Read-only and disabled native inputs still own their keyboard semantics.
  for(let node=element;node;node=node.parentElement){
    if(['INPUT','SELECT','TEXTAREA'].includes(String(node.tagName||'').toUpperCase()))return true;
  }
  if(typeof element.isContentEditable==='boolean')return element.isContentEditable;
  // Match native inheritance when used with light DOM adapters as well.
  for(let node=element;node;node=node.parentElement){
    const value=node.getAttribute?.('contenteditable');
    if(value===null||value===undefined)continue;
    const token=String(value).trim().toLowerCase();
    if(token==='false')return false;
    if(token===''||token==='true'||token==='plaintext-only')return true;
  }
  return false;
}

export function restoreExplorerFocus(list,key,search){
  const result=[...(list?.querySelectorAll('button')||[])].find(button=>button.dataset.key===key);
  // checkVisibility includes closed details and CSS-hidden ancestors in browsers.
  const visible=result&&!result.disabled&&(typeof result.checkVisibility==='function'
    ?result.checkVisibility({visibilityProperty:true}):result.getClientRects?.().length>0);
  const target=visible?result:search;
  if(typeof target?.focus!=='function')return false;
  target.focus({preventScroll:true});
  return true;
}
