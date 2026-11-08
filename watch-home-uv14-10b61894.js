'use strict';
const entry=new URL('./preview-b/releases/10b61894f0b62d232d212d617924b891481ab8aa2018c5931063742f5d4dfaed/atelier-preview.html',window.location.href);
entry.search=window.location.search;entry.hash=window.location.hash;document.getElementById('watch-viewer').src=entry.href;
