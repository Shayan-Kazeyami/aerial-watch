'use strict';
const entry=new URL('./preview-b/releases/ca6cf8cd536204e18ba347d1853f33c6dbbef6a9a69492b79a02ef78984fd3fe/atelier-preview.html',window.location.href);
entry.search=window.location.search;entry.hash=window.location.hash;document.getElementById('watch-viewer').src=entry.href;

