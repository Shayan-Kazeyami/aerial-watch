'use strict';
const entry=new URL('./preview-b/releases/60152a1445cc224eb39002dc5548b272ce3c00d41ab56464869d215331ab8b87/atelier-preview.html',window.location.href);
entry.search=window.location.search;entry.hash=window.location.hash;document.getElementById('watch-viewer').src=entry.href;

