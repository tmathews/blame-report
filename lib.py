import os
import io
import re
import subprocess
from sendgrid.helpers.mail import *
from datetime import datetime
from glob import glob

TODOS = ['TODO', 'todo']

def find_upsetters (start_path, globs):
    arr = []
    for path in globs:
        full_path = os.path.join(start_path, path)
        paths = glob(full_path, recursive=True)
        for file_path in paths:
            if os.path.isdir(file_path): continue
            with io.open(file_path, "r", encoding='utf-8', errors='ignore') as open_file:
                i = 0
                for line in open_file:
                    i = i + 1
                    if any(x in line for x in TODOS):
                        arr.append({
                            "type": "TODO",
                            "file_path": file_path,
                            "local_file_path": file_path.replace(start_path, os.path.basename(start_path)),
                            "line_number": i,
                            "contents": line
                        })
                        #print('TODO: line %s of file "%s"\n%s' % (i, file_path, line))
    return arr

def find_blamers (start_path, arr):
    narr = []
    for dic in arr:
        narr.append({**dic, **blame(start_path, dic)})
    return narr

def blame (start_path, dic):
    line = dic['line_number']
    file_path = dic['file_path']
    res = subprocess.run(['git', '-C', start_path, 'blame', '--porcelain', '--show-email', '-L%s,%s' % (line,line), file_path], stdout=subprocess.PIPE)
    string = res.stdout.decode('UTF-8')
    return {
        'hash_num': re.search('^([\d\w]{40}) ', string, flags=re.M).group(1),
        'author': re.search('^author ([\w\s]+)$', string, flags=re.M).group(1),
        'email': re.search('^author-mail <([^>]*)>$', string, flags=re.M).group(1),
        'time': datetime.fromtimestamp(int(re.search('^author-time (\d+)$', string, flags=re.M).group(1))),
        'time_zone': re.search('^author-tz -?(\d+)$', string, flags=re.M).group(1)
    }

def email_blames (sg, arr, dry=False):
    emap = {}
    for dic in arr:
        sub_arr = emap.get(dic['email'], [])
        sub_arr.append(dic)
        emap[dic['email']] = sub_arr
    for sub_arr in emap.items():
        email_blame(sg, sub_arr[1], dry) 

def email_blame (sg, arr, dry):
    base = arr[0]
    message = """Hi {},
You have {} TODOs. Please see below and fix, thank you.
"""
    message = message.format(base['author'], str(len(arr)))

    for x in arr:
        message += """
line %s of %s  

```
%s
```
""" % (x['line_number'], x['local_file_path'], x['contents'])
    if dry: return print(message)

    from_email = Email('thomas@monstercat.com')
    to_email = Email('thomas+test@monstercat.com')#base['email'])
    subject = 'You have things TODO!'
    content = Content('text/plain', message)
    mail = Mail(from_email, subject, to_email, content)
    response = sg.client.mail.send.post(request_body=mail.get())
    #print(response.status_code)
    #print(response.body)
    #print(response.headers)

