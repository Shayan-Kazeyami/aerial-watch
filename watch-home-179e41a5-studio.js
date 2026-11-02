'use strict';
// Keep asset resolution inside the immutable release and the public base URL
// in the top-level address bar. Forward caller options without rewriting them.
const releasePath='./preview-b/releases/179e41a5f3d030abf11962b8032c878fe22e1a1d950adbf1084bfed3552b5a08/atelier-preview.html';
const entry=new URL(releasePath,window.location.href);
entry.search=window.location.search;
entry.hash=window.location.hash;
document.getElementById('watch-viewer').src=entry.href;
