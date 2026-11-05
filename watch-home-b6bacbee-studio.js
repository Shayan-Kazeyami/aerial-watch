'use strict';
const entry=new URL('./preview-b/releases/b6bacbee9cc1020ec191a9180b1b50c7b1ba6c830926a1e27af9650ab9d5b912/atelier-preview.html',window.location.href);
entry.search=window.location.search;entry.hash=window.location.hash;document.getElementById('watch-viewer').src=entry.href;

