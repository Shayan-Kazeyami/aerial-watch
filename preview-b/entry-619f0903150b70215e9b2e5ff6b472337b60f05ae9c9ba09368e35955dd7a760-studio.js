// Copy beside the stable entry only after publication approval.
const target=new URL("releases/619f0903150b70215e9b2e5ff6b472337b60f05ae9c9ba09368e35955dd7a760/atelier-preview.html",import.meta.url);
target.search=location.search;
if(!target.searchParams.has('quality'))target.searchParams.set('quality','studio');
target.hash=location.hash;
location.replace(target.href);
