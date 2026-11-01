// Copy beside the stable entry only after publication approval.
const target=new URL("releases/3b37356cf003bfd57149ba6e480bbca9385033ca5c07084486c5a063b5285397/atelier-preview.html",import.meta.url);
target.search=location.search;
if(!target.searchParams.has('quality'))target.searchParams.set('quality','studio');
target.hash=location.hash;
location.replace(target.href);
