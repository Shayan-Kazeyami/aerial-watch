// Copy beside the stable entry only after publication approval.
const target=new URL("releases/ce999541279128d79e7da5e2d775519d21492b9fdf0ca1343efa9a7cae4dc3af/atelier-preview.html",import.meta.url);
target.search=location.search;
if(!target.searchParams.has('quality'))target.searchParams.set('quality','studio');
target.hash=location.hash;
location.replace(target.href);
