'use strict';
const entry=new URL('./preview-b/releases/c0537caa7dfc8357f4a1b7292a6853c5d10ab54b6017a5f4b0b0adbde1daec47/atelier-preview.html',window.location.href);
entry.search=window.location.search;entry.hash=window.location.hash;document.getElementById('watch-viewer').src=entry.href;
