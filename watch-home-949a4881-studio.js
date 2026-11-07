'use strict';
const entry=new URL('./preview-b/releases/949a4881d119910ca28bdf5ef4d67dfdebc59df579e02a6de946db48668510c8/atelier-preview.html',window.location.href);
entry.search=window.location.search;entry.hash=window.location.hash;document.getElementById('watch-viewer').src=entry.href;
