// Copy beside the stable entry only after publication approval.
const target=new URL("releases/a2ee1cff3c620530dfd63add3ab7111ba493bfff9173d7de00802e9a97f75054/atelier-preview.html",import.meta.url);
target.search=location.search;
if(!target.searchParams.has('quality'))target.searchParams.set('quality','studio');
target.hash=location.hash;
location.replace(target.href);
