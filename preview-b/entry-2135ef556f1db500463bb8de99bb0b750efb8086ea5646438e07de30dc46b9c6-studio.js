// Copy beside the stable entry only after publication approval.
const target=new URL("releases/2135ef556f1db500463bb8de99bb0b750efb8086ea5646438e07de30dc46b9c6/atelier-preview.html",import.meta.url);
target.search=location.search;
if(!target.searchParams.has('quality'))target.searchParams.set('quality','studio');
target.hash=location.hash;
location.replace(target.href);
