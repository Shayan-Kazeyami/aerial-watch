'use strict';
// Keep asset resolution inside the immutable release and the public base URL
// in the top-level address bar. Forward caller options without rewriting them.
const releasePath='./preview-b/releases/619f0903150b70215e9b2e5ff6b472337b60f05ae9c9ba09368e35955dd7a760/atelier-preview.html';
const entry=new URL(releasePath,window.location.href);
entry.search=window.location.search;
if(!entry.searchParams.has('quality'))entry.searchParams.set('quality','studio');
entry.hash=window.location.hash;
document.getElementById('watch-viewer').src=entry.href;
