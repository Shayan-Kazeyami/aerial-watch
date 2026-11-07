'use strict';
const entry=new URL('./preview-b/releases/cb5b426319babe1f263ddec44156a56eac0bf8b3020c979cc5f3c22884524695/atelier-preview.html',window.location.href);
entry.search=window.location.search;entry.hash=window.location.hash;document.getElementById('watch-viewer').src=entry.href;
