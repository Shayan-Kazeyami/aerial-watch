// Copy beside the stable entry only after publication approval.
const target=new URL("releases/c23e2bbc8a64658f2c7f29431cb144cf584e96d0eeac9a1e22c73697acb7b3bc/atelier-preview.html",import.meta.url);
target.search=location.search;
if(!target.searchParams.has('quality'))target.searchParams.set('quality','studio');
target.hash=location.hash;
location.replace(target.href);
