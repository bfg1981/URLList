#!/usr/bin/python3

import requests
import sys
import json

from joblib import Memory
location="cachedir"
#memory = Memory(location, verbose=0)
memory = Memory(location)

def cache_validation_cb(metadata):
    print('Validate')
    print(metadata)
    return True
    # Only retrieve cached results for calls that take more than 1s
    return metadata['duration'] > 1

@memory.cache(cache_validation_callback=cache_validation_cb)
def httpStat1(url):
    return requests.get(url, headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

def httpStat(urls):
    return [httpStat1(url) for url in urls]

from html.parser import HTMLParser

class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__() 
        self.OG={'og:title':'', 'og:image':'', 'og:description':''}
        self.OG_Alt={'og:title':'', 'og:image':'', 'og:description':''}
        self.isTitle=False
        self.isHead=False
    
    def handle_starttag(self, tag, attrs):
        if (tag=='head'):
            self.isHead=True
            return
        if (tag=='img'):
            #print (attrs)
            pass
        if self.isHead:
            if (tag=='title'):
                self.isTitle=True
#                print('Start')
        if (tag=='meta'):
#            print("Encountered a start tag:", tag)
#            print(attrs)
            isOG=False
            P=''
#            print(attrs)
            for attr in attrs:
                if 'property' in attr:
                    if attr[1].startswith('og:'):
                        isOG=True
                        P=attr[1]
                        break
            if isOG:
                for attr in attrs:
                    if 'content' in attr:
                        C=attr[1]
                        break
                self.OG[P]=C

    def handle_endtag(self, tag):
        if (tag=='head'):
            self.isHead=False
            return
        if self.isHead and (tag=='title'):
            self.isTitle=False
        #print("Encountered an end tag :", tag)
        pass
    
    def handle_data(self, data):
        if self.isTitle:
            self.OG_Alt['og:title']=data
        #print("Encountered some data  :", data)


def imgOrEmpty(url):
    if url:
        return '<img src="%s" width="400" height="200" >' % (url)
    else:
        return ''

def genPreview(hStat):
    t=hStat.text
    parser = MyHTMLParser()
    parser.feed(t)
    print(hStat.url)
    OG=None
    if parser.OG and 'og:title' in parser.OG:
        OG=parser.OG
    else:
        OG=parser.OG_Alt

    if not OG['og:title']:
        OG['og:title']=hStat.url

    print(OG)
    #return ('<td><a href="%s">%s</a></td><td>%s</td><td>%s</td>'% (hStat.url, OG['og:title'], imgOrEmpty(OG['og:image']), OG['og:description']))
    return ('<td class="outer"><a href="%s"><table><tr><th colspan="2">%s</th></tr><tr><td>%s</td><td>%s</td></tr></table></a></td>'% (hStat.url, OG['og:title'], imgOrEmpty(OG['og:image']), OG['og:description']))

txtfile=sys.argv[1]
if len(sys.argv)<3:
    s=txtfile.split('.')
    if s[-1]=='txt':
        htmlfile=str.join('.', s[0:-1]) + '.html'
        print(htmlfile)
    else:
        sys.exit(1)
else:
    htmlfile=sys.argv[2]

with open(txtfile) as file:
    urls = [line.rstrip() for line in file]

#remove duplicates
urls = list(dict.fromkeys(urls))

hStat = httpStat(urls)
for h2 in hStat:
    h=h2.headers
    #if 'last-modified' in h:
    #    print(h['last-modified'])
    #print(h['date'])

html='''
<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML//EN">
<html> <head>
<style>
img {
    object-fit: cover;
}
table, th, td {
  border: 0px solid black;
}
table.outer, td.outer {
  border: 1px solid black;
}
</style>
<title>URL List</title>
</head>
<h1>URL List</h1>
<p>
<table>
%s
</table>
</p>
</body>
</html>
'''

tStr=''
for h2 in hStat:
    #for property, value in vars(h2).items():
    #    print(property, ":", value)
    #sys.exit(0)
    #print(h2.headers)
    tStr+='<tr>'
    tStr+=genPreview(h2)
    tStr+='</tr>'


with open(htmlfile, "w") as html_file:
    html_file.write(html % (tStr))