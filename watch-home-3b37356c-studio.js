'use strict';
// Keep asset resolution inside the immutable release and the public base URL
// in the top-level address bar. Forward caller options without rewriting them.
const releasePath='./preview-b/releases/3b37356cf003bfd57149ba6e480bbca9385033ca5c07084486c5a063b5285397/atelier-preview.html';
const entry=new URL(releasePath,window.location.href);
entry.search=window.location.search;
if(!entry.searchParams.has('quality'))entry.searchParams.set('quality','studio');
entry.hash=window.location.hash;
document.getElementById('watch-viewer').src=entry.href;
