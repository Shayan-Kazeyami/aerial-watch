'use strict';
const entry=new URL('./preview-b/releases/9c055e4777a79c7987dd6cd5ccabf9f189121fd6c64e2f54853aa694827add06/atelier-preview.html',window.location.href);
entry.search=window.location.search;entry.hash=window.location.hash;document.getElementById('watch-viewer').src=entry.href;
