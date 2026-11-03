'use strict';
const entry=new URL('./preview-b/releases/003bf94f0360f595747e993b3d36f36b04a32e92c83386e4ac8076ecf528f5b9/atelier-preview.html',window.location.href);
entry.search=window.location.search;entry.hash=window.location.hash;document.getElementById('watch-viewer').src=entry.href;

