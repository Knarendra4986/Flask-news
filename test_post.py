import requests
import sys
url = 'https://apnews.com/article/hurricane-melissa-farmers-jamaica-cuba-haiti-wfp-880f6182c6054f8b65a34872d9e211cc'
try:
    r = requests.post('http://127.0.0.1:3000/analyze', json={'url': url}, timeout=120)
    print('STATUS:', r.status_code)
    print('RESPONSE:', r.text)
except Exception as e:
    print('EXC:', e)
    sys.exit(1)
