// Copy beside the stable entry only after publication approval.
const target=new URL("releases/ccb31fdf75b1ce58aff97d09dbc2ef500b972bf01916cd368e7e8c6a0800afbe/atelier-preview.html",import.meta.url);
target.search=location.search;
if(!target.searchParams.has('quality'))target.searchParams.set('quality','studio');
target.hash=location.hash;
location.replace(target.href);
