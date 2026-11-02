// Copy beside the stable entry only after publication approval.
const target=new URL("releases/f3ab38493b7bc5c4af84728add913e54938d0db276143a7b765a7803f361bb44/atelier-preview.html",import.meta.url);
target.search=location.search;
if(!target.searchParams.has('quality'))target.searchParams.set('quality','studio');
target.hash=location.hash;
location.replace(target.href);
