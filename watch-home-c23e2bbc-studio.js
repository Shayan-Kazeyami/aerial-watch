'use strict';
// Keep asset resolution inside the immutable release and the public base URL
// in the top-level address bar. Forward caller options without rewriting them.
const releasePath='./preview-b/releases/c23e2bbc8a64658f2c7f29431cb144cf584e96d0eeac9a1e22c73697acb7b3bc/atelier-preview.html';
const entry=new URL(releasePath,window.location.href);
entry.search=window.location.search;
entry.hash=window.location.hash;
document.getElementById('watch-viewer').src=entry.href;
