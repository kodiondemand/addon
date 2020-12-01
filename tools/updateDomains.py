import json, os, sys
import socket

path = os.getcwd()
sys.path.insert(0, path)
if sys.version_info[0] >= 3:
    from lib.httplib2 import py3 as httplib2
else:
    from lib.httplib2 import py2 as httplib2


def http_Resp(lst_urls):
    rslt = {}
    for sito in lst_urls:
        try:
            s = httplib2.Http()
            code, resp = s.request(sito, body=None)
            if code.previous:
                print("r1 http_Resp: %s %s %s %s" %
                            (code.status, code.reason, code.previous['status'],
                             code.previous['-x-permanent-redirect-url']))
                rslt['code'] = code.previous['status']
                rslt['redirect'] = code.previous['-x-permanent-redirect-url']
                rslt['status'] = code.status
            else:
                rslt['code'] = code.status
        except httplib2.ServerNotFoundError as msg:
            # both for lack of ADSL and for non-existent sites
            rslt['code'] = -2
        except socket.error as msg:
            # for unreachable sites without correct DNS
            # [Errno 111] Connection refused
            rslt['code'] = 111
        except:
            rslt['code'] = 'Connection error'
    return rslt


if __name__ == '__main__':
    fileJson = 'channels.json'

    with open(fileJson) as f:
        data = json.load(f)

    result = data['direct']

    for chann, host in sorted(data['direct'].items()):
        # to get an idea of the timing
        # useful only if you control all channels
        # for channels with error 522 about 40 seconds are lost ...
        print("check #### INIZIO #### channel - host :%s - %s " % (chann, host))

        rslt = http_Resp([host])

        # all right
        if rslt['code'] == 200:
            result[chann] = host
        # redirect
        elif str(rslt['code']).startswith('3'):
            # result[chann] = str(rslt['code']) +' - '+ rslt['redirect'][:-1]
            if rslt['redirect'].endswith('/'):
                rslt['redirect'] = rslt['redirect'][:-1]
            result[chann] = rslt['redirect']
        # non-existent site
        elif rslt['code'] == -2:
            print('Host Sconosciuto - '+ str(rslt['code']) +' - '+ host)
        # site not reachable
        elif rslt['code'] == 111:
            print('Host non raggiungibile - '+ str(rslt['code']) +' - ' + host)
        else:
            # other types of errors
            print('Errore Sconosciuto - '+str(rslt['code']) +' - '+ host)

        print("check #### FINE #### rslt :%s  " % (rslt))

    result = {'findhost': data['findhost'], 'direct': result}
    # I write the updated file
    with open(fileJson, 'w') as f:
        json.dump(result, f, sort_keys=True, indent=4)
