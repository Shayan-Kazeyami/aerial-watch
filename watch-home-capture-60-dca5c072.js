'use strict';
const entry=new URL('./preview-b/releases/dca5c072be394554f4ae293b0324e61a38f5b548cbab721f99f8cf80e13298bc/atelier-preview.html',window.location.href);
entry.search=window.location.search;entry.hash=window.location.hash;document.getElementById('watch-viewer').src=entry.href;
