import urllib.request,time
for i in range(40):
 try:
  s=urllib.request.urlopen('https://shayan-kazeyami.github.io/aerial-watch/?qa='+str(time.time())).read().decode()
  if 'watch-home-batched-ff188ba6.js' in s:break
 except Exception:pass
 time.sleep(15)
else:raise RuntimeError('Expected root loader not deployed')
print('Expected public root loader verified')
