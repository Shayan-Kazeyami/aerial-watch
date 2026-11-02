// Copy beside the stable entry only after publication approval.
const target=new URL("releases/a5d6442fe1e1d7bc0582bf6024d125d184693b24f2e1f8e9d329bc3736052368/atelier-preview.html",import.meta.url);
target.search=location.search;
if(!target.searchParams.has('quality'))target.searchParams.set('quality','studio');
target.hash=location.hash;
location.replace(target.href);
