'use strict';
// Keep asset resolution inside the immutable release and the public base URL
// in the top-level address bar. Forward caller options without rewriting them.
const releasePath='./preview-b/releases/f3ab38493b7bc5c4af84728add913e54938d0db276143a7b765a7803f361bb44/atelier-preview.html';
const entry=new URL(releasePath,window.location.href);
entry.search=window.location.search;
entry.hash=window.location.hash;
document.getElementById('watch-viewer').src=entry.href;
