#!/usr/bin/env python3
"""Conservative discovery of public notice headlines from official sources only.
No automatic use of third-party editorial articles or inferred deadlines.
"""
import json,re,datetime,urllib.parse
from pathlib import Path
import requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parent
RECRUIT=re.compile(r'recruitment|vacanc(?:y|ies)|appointment|selection|advertisement|भरती|पदभरती|नियुक्ती|जाहिरात',re.I)
ADMISSION=re.compile(r'admission|counselling|counseling|seat allotment|cap round|प्रवेश|समुपदेशन|जागावाटप',re.I)
EXAM=re.compile(r'examination|exam date|exam schedule|hall ticket|admit card|answer key|result|परीक्षा|प्रवेशपत्र|उत्तरतालिका|निकाल|वेळापत्रक',re.I)
IGNORE=re.compile(r'^(home|more|read more|click here|login|contact|recruitment|advertisement|notification|भरती|जाहिरात|about us|view all|latest news)$',re.I)
def official(url):
 p=urllib.parse.urlparse(url);h=(p.hostname or '').lower()
 return p.scheme=='https' and not p.username and (h.endswith('.gov.in') or h.endswith('.nic.in') or h.endswith('.ac.in'))
def category(title):
 if ADMISSION.search(title):return 'प्रवेश'
 if EXAM.search(title):return 'परीक्षा'
 if RECRUIT.search(title):return 'भरती'
 return None
def scrape(session,source):
 try:
  r=session.get(source['url'],timeout=20);r.raise_for_status()
  if len(r.content)>2_000_000:return []
  soup=BeautifulSoup(r.content,'html.parser')
 except requests.RequestException as exc:
  print('Source unavailable:',source['name'],str(exc)[:120]);return []
 output=[]
 for a in soup.select('a[href]'):
  title=' '.join(a.get_text(' ',strip=True).split())
  if not 24<=len(title)<=180 or IGNORE.fullmatch(title):continue
  cat=category(title)
  if cat not in source['categories']:continue
  url=urllib.parse.urljoin(r.url,a.get('href',''))
  if not official(url):continue
  output.append({'category':cat,'title':title,'description':source['name']+' — अधिकृत संकेतस्थळावर आढळलेली सूचना. कृपया अंतिम तपशील पडताळा.','source':source['name'],'_key':url})
 return output[:35]
def main():
 session=requests.Session();session.headers.update({'User-Agent':'JadhavMultiServicesNoticeMonitor/1.1 (official public pages)'})
 items=[];seen=set()
 for source in json.loads((ROOT/'sources.json').read_text(encoding='utf-8')):
  if not official(source['url']):continue
  for item in scrape(session,source):
   key=item.pop('_key')
   if key in seen:continue
   seen.add(key);items.append(item)
 if items:
  (ROOT/'public'/'notifications.json').write_text(json.dumps(items[:90],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 else:print('No new official-source notices found; existing feed preserved')
 print('Official notice headlines:',len(items))
if __name__=='__main__':main()
