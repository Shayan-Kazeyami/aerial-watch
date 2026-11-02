'use strict';
// Keep asset resolution inside the immutable release and the public base URL
// in the top-level address bar. Forward caller options without rewriting them.
const releasePath='./preview-b/releases/a5d6442fe1e1d7bc0582bf6024d125d184693b24f2e1f8e9d329bc3736052368/atelier-preview.html';
const entry=new URL(releasePath,window.location.href);
entry.search=window.location.search;
entry.hash=window.location.hash;
document.getElementById('watch-viewer').src=entry.href;
