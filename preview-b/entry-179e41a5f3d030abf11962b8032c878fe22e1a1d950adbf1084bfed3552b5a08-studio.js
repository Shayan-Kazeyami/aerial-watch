// Copy beside the stable entry only after publication approval.
const target=new URL("releases/179e41a5f3d030abf11962b8032c878fe22e1a1d950adbf1084bfed3552b5a08/atelier-preview.html",import.meta.url);
target.search=location.search;
if(!target.searchParams.has('quality'))target.searchParams.set('quality','studio');
target.hash=location.hash;
location.replace(target.href);
