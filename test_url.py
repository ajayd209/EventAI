import urllib.request
import urllib.error

try:
    response = urllib.request.urlopen('http://127.0.0.1:8000/planner/')
    content = response.read().decode('utf-8')
    with open('test_output.html', 'w', encoding='utf-8') as f:
        f.write(content)
except urllib.error.HTTPError as e:
    content = e.read().decode('utf-8')
    with open('test_output.html', 'w', encoding='utf-8') as f:
        f.write(content)
