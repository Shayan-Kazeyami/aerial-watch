'use strict';
const entry=new URL('./preview-b/releases/43e516fa6ed3a4be7e8b308bc35c1955dc811b710042e38cdbaeaf868b7c8932/atelier-preview.html',window.location.href);
entry.search=window.location.search;entry.hash=window.location.hash;document.getElementById('watch-viewer').src=entry.href;
