'use strict';
// Keep asset resolution inside the immutable release and the public base URL
// in the top-level address bar. Forward caller options without rewriting them.
const releasePath='./preview-b/releases/a2ee1cff3c620530dfd63add3ab7111ba493bfff9173d7de00802e9a97f75054/atelier-preview.html';
const entry=new URL(releasePath,window.location.href);
entry.search=window.location.search;
if(!entry.searchParams.has('quality'))entry.searchParams.set('quality','studio');
entry.hash=window.location.hash;
document.getElementById('watch-viewer').src=entry.href;
