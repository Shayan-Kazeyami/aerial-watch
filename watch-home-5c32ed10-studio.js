'use strict';
const entry=new URL('./preview-b/releases/5c32ed10f90818f697328e03331a1ef2e3c9d8f488a2af1873625d4580215347/atelier-preview.html',window.location.href);
entry.search=window.location.search;entry.hash=window.location.hash;document.getElementById('watch-viewer').src=entry.href;

