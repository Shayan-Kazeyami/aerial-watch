'use strict';
// Keep asset resolution inside the immutable release and the public base URL
// in the top-level address bar. Forward caller options without rewriting them.
const releasePath='./preview-b/releases/fcaad311973aff1e27395d6f87ce363210b2d9a4d28b545e8c569f22831a5a72/atelier-preview.html';
const entry=new URL(releasePath,window.location.href);
entry.search=window.location.search;
if(!entry.searchParams.has('quality'))entry.searchParams.set('quality','studio');
entry.hash=window.location.hash;
document.getElementById('watch-viewer').src=entry.href;
