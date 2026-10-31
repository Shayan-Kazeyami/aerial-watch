export const normalizeComponentText=value=>String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
const categories=[
 [/contre pivot/,'Cap jewel'],[/pierre|cheville de plateau/,'Bearing jewel'],
 [/serge de balancier/,'Balance rim'],[/spiral/,'Hairspring'],[/balancier/,'Balance component'],
 [/echappement/,'Escapement component'],[/ancre/,'Pallet fork component'],
 [/barillet/,'Mainspring barrel'],[/rochet/,'Winding ratchet wheel'],[/ressort/,'Spring'],
 [/roue seconde/,'Seconds wheel'],[/pignon/,'Pinion'],[/planche|roue/,'Gear wheel'],
 [/\bvis\b/,'Screw'],[/pont|platine|coq|plaque/,'Movement plate'],
 [/tige|remontoir/,'Winding component'],[/tirette|bascule/,'Setting mechanism'],
 [/goupille|axe|arbre|tenon/,'Pin or staff'],
];
const exterior={HOUR:'Hour hand',MINUTE:'Minute hand',SECONDS:'Small-seconds hand',CASE:'Case',CASEBACK:'Caseback',CROWN:'Crown',DIAL:'Original dial',CHAPTER:'Original chapter ring','FRONT-CRYSTAL':'Front glass','REAR-CRYSTAL':'Rear glass','STRAP-UPPER':'Upper strap','STRAP-LOWER':'Lower strap'};
export function componentLabel(data={},name=''){
 if(data.sourceIndex!==undefined){
  const raw=normalizeComponentText(`${data.description||''} ${name}`);
  const friendly=categories.find(([pattern])=>pattern.test(raw))?.[1]||'Movement component';
  return `${friendly} · OM10 #${data.sourceIndex}`;
 }
 const id=data.assemblyId||'';
 const friendly=exterior[id]||(/^BACK-SCREW/.test(id)?'Caseback screw':/^SPRINGBAR/.test(id)?'Strap spring bar':/^BUCKLE/.test(id)?'Buckle component':/^KEEPER/.test(id)?'Strap keeper':id.replaceAll('-',' ').toLowerCase()||name);
 return friendly;
}
export function componentSearchText(data={},name=''){
 const original=normalizeComponentText(`${data.description||''} ${data.role||''} ${name}`);
 const aliases=[/balancier/.test(original)?'balance wheel oscillator':'',/spiral/.test(original)?'balance hairspring spring':'',/planche|roue|pignon/.test(original)?'gear wheel train':'',/pierre|contre pivot/.test(original)?'jewel bearing':''];
 return normalizeComponentText([componentLabel(data,name),data.partNumber,data.assemblyId,original,...aliases].join(' '));
}
