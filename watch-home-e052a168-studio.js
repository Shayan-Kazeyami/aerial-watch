'use strict';
// Keep asset resolution inside the immutable release and the public base URL
// in the top-level address bar. Forward caller options without rewriting them.
const releasePath='./preview-b/releases/e052a16868ede74119c9e4f3e214a02276461511b23054b0886147a79d379380/atelier-preview.html';
const entry=new URL(releasePath,window.location.href);
entry.search=window.location.search;
entry.hash=window.location.hash;
document.getElementById('watch-viewer').src=entry.href;
