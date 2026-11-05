'use strict';
const entry=new URL('./preview-b/releases/2d60c4f0016d8b421366ff1a6c21b0c50510cf3dd57e3ba32c9a9aff18d3ea07/atelier-preview.html',window.location.href);
entry.search=window.location.search;entry.hash=window.location.hash;document.getElementById('watch-viewer').src=entry.href;

