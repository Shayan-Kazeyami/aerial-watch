'use strict';
const entry=new URL('./preview-b/releases/0c468cf914b608e0d67036aa0a25fe16bb6c2802b0e90a940677f43466e19ff1/atelier-preview.html',window.location.href);
entry.search=window.location.search;entry.hash=window.location.hash;document.getElementById('watch-viewer').src=entry.href;
