'use strict';
// Keep asset resolution inside the immutable release and the public base URL
// in the top-level address bar. Forward caller options without rewriting them.
const releasePath='./preview-b/releases/87a759964175034b479a36bd84035d0265cad0b6742306e1f7499ce4dca325e1/atelier-preview.html';
const entry=new URL(releasePath,window.location.href);
entry.search=window.location.search;
if(!entry.searchParams.has('quality'))entry.searchParams.set('quality','studio');
entry.hash=window.location.hash;
document.getElementById('watch-viewer').src=entry.href;
