// Copy beside the stable entry only after publication approval.
const target=new URL("releases/fcaad311973aff1e27395d6f87ce363210b2d9a4d28b545e8c569f22831a5a72/atelier-preview.html",import.meta.url);
target.search=location.search;
target.hash=location.hash;
location.replace(target.href);
