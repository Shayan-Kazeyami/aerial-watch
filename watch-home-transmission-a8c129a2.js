'use strict';
const entry=new URL('./preview-b/releases/a8c129a21c1ba3529f372d00bf94e0edcadc295931cae5dee0770f5c92c31473/atelier-preview.html',window.location.href);
entry.search=window.location.search;entry.hash=window.location.hash;document.getElementById('watch-viewer').src=entry.href;
