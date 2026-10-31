// Visible alternatives to selects. Keep native fields as the viewer state source.
export function installVisibleChoices(root=document){
 const disposers=[];
 for(const select of root.querySelectorAll('#showcase-controls select')){
  const group=document.createElement('div');group.className='visible-choices';group.setAttribute('role','group');
  const label=root.querySelector(`label[for="${select.id}"]`);
  group.setAttribute('aria-label',label?.firstChild?.textContent?.trim()||select.id);
  select.insertAdjacentElement('afterend',group);select.hidden=true;
  let signature='';
  function refresh(){
   const options=[...select.options];
   const next=JSON.stringify(options.map(o=>[o.value,o.textContent]));
   // Preserve focused buttons when only the selected value changes.
   if(next!==signature){
    const focused=group.contains(document.activeElement)?document.activeElement.dataset.value:null;
    group.replaceChildren();signature=next;
    for(const option of options){
     const button=document.createElement('button');button.type='button';button.textContent=option.textContent;button.dataset.value=option.value;
     button.onclick=()=>{select.value=option.value;select.dispatchEvent(new Event('change',{bubbles:true}));refresh();};group.append(button);
    }
    if(focused!==null)[...group.children].find(b=>b.dataset.value===focused)?.focus();
   }
   [...group.children].forEach((button,i)=>{button.setAttribute('aria-pressed',String(options[i].value===select.value));button.disabled=select.disabled||options[i].disabled;});
  }
  const sync=()=>queueMicrotask(refresh);
  root.addEventListener('click',sync);root.addEventListener('change',sync);root.addEventListener('studio-state-change',sync);
  const observer=new MutationObserver(sync);observer.observe(select,{childList:true,subtree:true,attributes:true});refresh();
  disposers.push(()=>{observer.disconnect();root.removeEventListener('click',sync);root.removeEventListener('change',sync);root.removeEventListener('studio-state-change',sync);group.remove();select.hidden=false;});
 }
 return ()=>disposers.forEach(dispose=>dispose());
}
if(typeof document!=='undefined')installVisibleChoices();
