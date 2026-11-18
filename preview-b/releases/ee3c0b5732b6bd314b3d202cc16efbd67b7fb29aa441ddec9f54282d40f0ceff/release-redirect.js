// Build-only whitelisted historical navigation; never accepts a URL parameter.
const targets=Object.freeze({"assembly-review.html":"../../assembly-review.html","atelier-layout-study.html":"../../atelier-layout-study.html","index.html":"./atelier-preview.html","integrated-preview.html":"../../integrated-preview.html"});
const name=location.pathname.split('/').pop()||'index.html';
if(!Object.hasOwn(targets,name))throw new Error('Unknown release redirect');
const target=new URL(targets[name],import.meta.url);
target.search=location.search;target.hash=location.hash;location.replace(target.href);
