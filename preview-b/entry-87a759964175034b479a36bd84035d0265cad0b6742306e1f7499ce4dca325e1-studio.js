// Copy beside the stable entry only after publication approval.
const target=new URL("releases/87a759964175034b479a36bd84035d0265cad0b6742306e1f7499ce4dca325e1/atelier-preview.html",import.meta.url);
target.search=location.search;
if(!target.searchParams.has('quality'))target.searchParams.set('quality','studio');
target.hash=location.hash;
location.replace(target.href);
