import urllib.request,time
for i in range(30):
 s=urllib.request.urlopen('https://shayan-kazeyami.github.io/aerial-watch/').read().decode()
 if 'watch-home-registry-255ce38c.js' in s:break
 time.sleep(15)
else:raise RuntimeError('Expected loader not yet deployed')
print('Expected public root verified')
