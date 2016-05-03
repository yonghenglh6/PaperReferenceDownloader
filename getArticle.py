# -*- coding: utf-8 -*-
import urllib2
import urllib
from bs4 import BeautifulSoup
import cPickle as pickle
import re
import os
import thread
import threading
BaseURL="http://xueshu.baidu.com";
BaseSearchURL="http://xueshu.baidu.com/s?wd=%s&tn=SE_baiduxueshu_c1gjeupa&cl=3&ie=utf-8&bs=%s&f=8&rsv_bp=1&rsv_sug2=1&sc_f_para=sc_tasktype%%3D%%7BfirstSimpleSearch%%7D&rsv_spt=3";
#IDENTITY= r"\[[0-9]+\]";
IDENTITY= r"[0-9]+\.";
SPLIT_FLAG="#";
def formatKeyWord(keyword):
#    keyword = "[15] Pierre Sermanet, David Eigen, Xiang Zhang, Michael Mathieu, Rob Fergus, and Yann LeCun.\r\nOverfeat: Integrated recognition, localization and detection using convolutional networks. In\r\nICLR’14.\r\n[16] Ilya Sutskever, Oriol Vinyals, and Quoc Le. Sequence to sequence learning with neural networks. In NIPS*2014.\r\n[12] B. Leibe, E. Seemann, and B. Schiele. Pedestrian detection in crowded scenes. In CVPR 2005.\r\n";
    str_result=re.sub(r'((\r*\n)|(^))(?P<index>' + IDENTITY + ')', lambda m: SPLIT_FLAG + m.group("index") + SPLIT_FLAG, keyword)
    str_result=str_result.replace('\r\n',' ').replace('\n',' ');

    str_result = re.sub(SPLIT_FLAG + IDENTITY + SPLIT_FLAG, lambda m: '\n' + m.group(0) + '', str_result)
    return str_result;

def _getWenxianList(str_result):
    result_list = [];
    for line in str_result.split('\n'):
        if line == '':
            continue;
        # print "ORIGIN:"+line
        pat = re.compile(
            SPLIT_FLAG + '(?P<identity>' + IDENTITY + ')' + SPLIT_FLAG + r'\s{,1}(((((\w\.)+|([-\w]+)) )*((\w\.)|(\w+))), )*(((((\w\.)+|([-\w]+)) )*((\w\.)|(\w+)))[.:] )(?P<article>[^.]+). ')
        mat = pat.match(line)
        if mat:
            print mat.group(0)
            return
            id = mat.group('identity');
            arti = mat.group('article');
            while id in result_list:
                id = id + '{retend}';
            oneItem={};
            oneItem['refId']=id;
            oneItem['article']=arti;
            result_list.append(oneItem);
        else:
            print "No"+line
            return
    return result_list;

def _getContent(keyword):
    keyword=urllib.quote(keyword);
    #print BaseSearchURL % (keyword,keyword)
    content=urllib2.urlopen(BaseSearchURL % (keyword,keyword))
    return content.read();

def _getURLs(content):
    doc= BeautifulSoup(content,"lxml");
    listbox= doc.find(id="bdxs_result_lists");
    rs_url=[];
    if listbox is None :
        con=doc.find(id="savelink_wr")
        if con is not None:
            oneUrls = [];
            for link1 in con.children:
                url=link1.contents[0]['href']
                oneUrls.append(url);
            rs_url.append(oneUrls);
    else:
        list=listbox.find_all("div",class_='result')
        for item in list:
            scDown=item.find(class_="sc_download")
            oneUrls=[];
            if scDown==None:
                pass
            elif scDown['href']!='javascript:;':
                url=scDown['href'];
                oneUrls.append(url);
            else:
                for link1 in item.find(class_="sc_savalink_content").children:
                    url=link1.find(class_='saveurl').get_text();
                    oneUrls.append(url)
            rs_url.append(oneUrls)
    for urls in rs_url:
        for index,url in enumerate(urls):
            if url.startswith('/s?'):
                urls[index]=BaseURL+url;
#    print rs_url

    return rs_url

threads=[]
class downloader(threading.Thread):
    def __init__(self, article):
        threading.Thread.__init__(self)
        self.article = article

    def run(self):
        flag=False;
        firstSize=-2;
        art=self.article;
        downLoadName=art['refId']+"_"+re.sub(r'[\/:*?"<>|]',' ',art['article']+".pdf");
        threadName=art['refId'];
        print "Begin to download:" + downLoadName;
        for urls in art['urls']:
            if flag:
                break;
            for url in urls:
                localFile = os.path.join('rs/',downLoadName)
                print threadName+"from:" + url;
                try:
                    urllib.urlretrieve(url, localFile)
                    print threadName+"%d" % os.path.getsize(localFile)
                    if os.path.exists(localFile):
                        tsize=os.path.getsize(localFile)
                        if tsize>200000:
                            flag = True
                            print threadName + "done.";
                            break;
                        elif tsize>50000:
                            if firstSize != -2 and firstSize==tsize:
                                flag = True
                                print threadName + "done.";
                                break;
                            else:
                                if tsize>firstSize:
                                    firstSize=tsize
                                print threadName + "try annother,change url.";
                                continue
                    print threadName+"fail,change url.";
                    os.remove(localFile);
                except:
                    print threadName+"fail,change url.";

def downloadFiles(mlist):
    for art in mlist:
        t = downloader(art)
        threads.append(t)
        t.start()



def getAllFromFile(listFile):
    with open(listFile) as mfile:
        listContent= mfile.read();
        listContent=formatKeyWord(listContent);
        wlist=_getWenxianList(listContent);
        print wlist
        return
        for arti in wlist:
            page=_getContent(arti['article']);
            urls=_getURLs(page);
            arti['urls']=urls;
            print ""+arti['refId']+"["+arti['article']+"] is done.";
    print wlist
    return wlist;
def main():
    step1=True;
    step2=False;
    if step1:
        with open('rs.list','w') as mfile:
           pickle.dump(getAllFromFile('list'),mfile)
    if step2:
        with open('rs.list') as mfile:
           mlist=pickle.load(mfile)
           downloadFiles(mlist)

if __name__ == '__main__':
    main()
    for t in threads:
        t.join()








