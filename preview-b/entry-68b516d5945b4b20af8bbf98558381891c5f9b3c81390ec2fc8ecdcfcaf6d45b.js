const target = new URL('./releases/68b516d5945b4b20af8bbf98558381891c5f9b3c81390ec2fc8ecdcfcaf6d45b/atelier-preview.html', import.meta.url);
target.search = location.search;
target.hash = location.hash;
location.replace(target.href);
