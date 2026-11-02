// Copy beside the stable entry only after publication approval.
const target=new URL("releases/e052a16868ede74119c9e4f3e214a02276461511b23054b0886147a79d379380/atelier-preview.html",import.meta.url);
target.search=location.search;
if(!target.searchParams.has('quality'))target.searchParams.set('quality','studio');
target.hash=location.hash;
location.replace(target.href);
