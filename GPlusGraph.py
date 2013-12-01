# ABOUT:
# A script that grabs a list of the friends or followers of a user on Google+,
# grabs a sample of their friends, and generates the resulting social graph

    #friends
    #https://plus.google.com/u/0/_/socialgraph/lookup/visible/?o=%5Bnull%2Cnull%2C%22GOOGLEPLUSUSERID%22%5D&rt=j

    #followers
    #https://plus.google.com/u/0/_/socialgraph/lookup/incoming/?o=%5Bnull%2Cnull%2C%22GOOGLEPLUSUSERID%22%5D&n=1000&rt=j

# DEPENDENCIES
# The script makes use of the networkx library; you should only need to install it once.
# To install networkx, from the command line type: easy_install networkx
# If that doesn't work, follow the instructions on http://networkx.lanl.gov/install.html
# In short: a) download and unzip http://networkx.lanl.gov/download/networkx/networkx-1.5.zip
# b) cd to the networkx-1.5 directory, c) type: python setup.py install 
# END DEPENDENCIES

# Author: Paolo Di Prodi
# email: paolo@robomotic.com
# Copyright 2013 Robomotic ltd

#
#This file is part of Google Plus Social Graph.
#
#Google Plus Social Graph is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Google Plus Social Graph is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with Foobar. If not, see <http://www.gnu.org/licenses/>.


## This is the only dependency to be installed
import networkx as nx

## Classical imports
import urllib2,re
import md5,urllib,os,tempfile,time
import random
import datetime
## Shutil is necessary for encrypted home folder's operations
import shutil
## This is useful to buffer big files into strings
import StringIO
import getopt
import sys
import matplotlib.pyplot as plt
import json

class FolderUtils:
    @staticmethod
    def checkDir(dirpath):
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
    @staticmethod
    def check():
        FolderUtils.checkDir('reports')
        FolderUtils.checkDir('cache')

class UserID:
    """
    Contains the user settings for the originator of the Graph
    """
    _rootID='102196889921439282573'
    """The ID used by Google Plus to identify the user"""
    _name='Paolo Di Prodi'
    """The username associated to that ID"""
    _addUserFriendships=0
    _user=''
    def __init__(self):
        """
        Build a simple pair with ID and Username
        """
        self._rootID= json.loads(open('client_cookie.json', 'r').read())['Cookie']['root_id']
        self._oidRootNamePairs={self._rootID:self._name}

class GraphOptions:
    """
    Options for exploring and building the graph
    """
    _defCache=360000
    """How many seconds we keep the cache for"""
    _mindegree=None
    """Minimum degree"""
    _indegree=20
    """Minimum input degree"""
    _outdegree=25
    """Output degree"""
    _outdegreemax=None
    """Output maximum degree """
    _indegreemax=None
    """Maximum input degree allowed"""
    _projname='reports/'
    def __init__(self):
        pass
    
class Patterns:
    """
    Regular expression for parsing the messy junky google response
    """
    reobj = re.compile(r'.*([0-9]{21}).*')
    reobj2 = re.compile(r',\["([^"]*)".*')
    reobj3=re.compile(r'.*[0-9]{21}"\]\n,\[\]\n,\["[^"]*')
    #oids = reobj3.findall(data)
    #for oid in oids:
    #,[[,,"112696985248193005986"]\n,[]\n,["Dawn Wicks-Sutton
    reobj4=re.compile(r',\[+,,"([0-9]{21})"]\n,\[\]\n,\["(.*)$')
    #ascii(reobj4.match(oid).group(2)) is name, tho check not '' if so 'U N Owen", reobj4.match(oid).group(1) is ID 
    def __init__(self):
        pass
        
class Def:
    typ='fo'
    typ2='fr'    
    def __init__(self):
        pass
        
class Utils:
    @staticmethod
    def ascii(s): return "".join(i for i in s if ord(i)<128)
    @staticmethod
    def getGenericCachedData(url, cachetime=GraphOptions._defCache):
      fetcher=DiskCacheFetcherfname('cache')
      fn=fetcher.fetch(url, cachetime)
      f=open(fn)
      data=f.read()
      f.close()

      return data
    @staticmethod
    def getoidName(i,currIDs,oidNames):
        l=i.next()
        #print l
        oid = Patterns.reobj.match(l)
        if oid==None:
            Utils.report("Friends list scanned")
            return i,currIDs,oidNames,-1
        else: oid=oid.group(1)
        #if we don't get an ID, then return oidNames, i, -1
        if oid not in currIDs:
            #print 'toploop'
            i.next()
            n=i.next()
            n=Utils.ascii(Patterns.reobj2.match(n).group(1))
            if oid not in oidNames:
                oidNames[oid]=n
            currIDs.append(oid)
            Utils.report("Friend ID %s and name %s"%(oid, n))
            #print oid,n

            while True:
                next=''
                hops=0
                while next!=',[]\n':
                    next=i.next()
                    hops=1

                next=''
                while next!=']\n':
                    next=i.next()
                    hops+=1
                if(hops)==2: break
        else:
            print 'bottomloop'
            next=''
            while next!=']\n':
                next=i.next()
        return i,currIDs,oidNames,1
    @staticmethod
    def getoidNames(oidNames,oid='',typ='fr'):
        #oidNames = {}
        if oid=='': return oidNames,[]
        currIDs=[]
        #???I suspect this only does one page of up to 1000(?) users? Need to check?
        if typ=='fr':
            url='https://plus.google.com/u/0/_/socialgraph/lookup/visible/?o=%5Bnull%2Cnull%2C%22'+oid+'%22%5D&rt=j'
        elif typ=='fo':
            url='https://plus.google.com/u/0/_/socialgraph/lookup/incoming/?o=%5Bnull%2Cnull%2C%22'+oid+'%22%5D&n=1000&rt=j'
        else:
            exit(-1)
        print url
        #data = urllib.urlopen(url).read()
        data=Utils.getGenericCachedData(url)
        i=StringIO.StringIO(data)
        i.next()
        i.next()
        i.next()
        i.next()
        #if flag returns <0, we're done
        flag=1
        while flag>0:
            i,currIDs,oidNames,flag=Utils.getoidName(i,currIDs,oidNames)
        #print currIDs,oidNames
        return oidNames,currIDs
    #----------------------------------------------------------------
    #Yield successive n-sized chunks from l
    @staticmethod
    def chunks(l, n):   
        for i in xrange(0, len(l), n):
            yield l[i:i+n]
    @staticmethod
    def report(m, verbose=True):
      if verbose is True:
        print m


class DiskCacheFetcherfname:
    def __init__(self, cache_dir=None):
        # If no cache directory specified, use system temp directory
        if cache_dir is None:
            cache_dir = tempfile.gettempdir()
        self.cache_dir = cache_dir

        self.cookie = json.loads(open('client_cookie.json', 'r').read())['Cookie']['client_secret']

    def fetch(self, url, max_age=0):
        # Use MD5 hash of the URL as the filename
        filename = md5.new(url).hexdigest()
        # Build the path to the destination report folder
        filepath = os.path.join(self.cache_dir, filename)
        # If the file was already fetched check the timestamp and overwrite
        if os.path.exists(filepath):
            if int(time.time()) - os.path.getmtime(filepath) < max_age:
                #return open(filepath).read()
                Utils.report("using "+filename+", cached copy of fetched url: "+url)
                return filepath
        Utils.report("fetching fresh copy of fetched url: "+url)
        # Retrieve over HTTP and cache, using rename to avoid collisions
        opener = urllib2.build_opener()
        opener.addheaders.append(('Cookie', self.cookie))
        
        data = opener.open(url).read()
        fd, temppath = tempfile.mkstemp()
        fp = os.fdopen(fd, 'w')
        fp.write(data)
        fp.close()
        shutil.move(temppath, filepath)
        return filepath
      

class GraphExplorer:
    def __init__(self, rootNode, directGraph):
        self.oidNamePairs={}
        self.oidRootNamePairs=rootNode._oidRootNamePairs;
        self.DG=directGraph

    def addDirectedEdges(self,fromNode,toSet,flip=False):
        for toNode in toSet:
            if flip==True:
                self.DG.add_edge(toNode,fromNode)
            else:
                self.DG.add_edge(fromNode,toNode)
        #print nx.info(DG)

    def labelNodes(self,names):
        for nodeID in self.DG.node:
            self.DG.node[nodeID]['label']=names[nodeID]
        
    def start(self):
        for id in self.oidRootNamePairs:
            self.oidNamePairs,currIDs=Utils.getoidNames(self.oidNamePairs,id,Def.typ)
            Utils.report('Processing current IDs: '+str(currIDs))
            flip=(Def.typ=='fr')
            self.addDirectedEdges(id, currIDs,flip=flip)
            n=len(currIDs)
            Utils.report('Total amount of IDs: '+str(n))
            c=1
            for cid in currIDs:
                Utils.report('\tSub-level run: getting '+Def.typ2,str(c)+'of'+str(n)+Def.typ+cid)
                self.oidNamePairs,ccurrIDs=Utils.getoidNames(self.oidNamePairs,cid,Def.typ2)
                self.addDirectedEdges( cid, ccurrIDs)
                c=c+1
        for id in self.oidRootNamePairs:
            if id not in self.oidNamePairs:
                self.oidNamePairs[id]=self.oidRootNamePairs[id]
        self.labelNodes(self.oidNamePairs)
        Utils.report(nx.info(self.DG))

        now = datetime.datetime.now()
        timestamp = now.strftime("_%Y-%m-%d-%H-%M-%S")

        fname=UserID._name.replace(' ','_')
        nx.write_graphml(self.DG, '/'.join(['reports',fname+'_google'+Def.typ+'Friends_'+timestamp+".graphml"]))
        nx.write_edgelist(self.DG, '/'.join(['reports',fname+'_google'+Def.typ+'Friends_'+timestamp+".txt"]),data=False)

    def filterNet(self, gopt,userID):
        #need to tweak this to allow filtering by in and out degree?
        if userID._addUserFriendships==1:
            self.DG=addFocus(self.DG,userID._user,Def.typ)
        #handle min,in,out degree
        filter=[]
        #filter=[n for n in DG if DG.degree(n)>=mindegree]
        for n in self.DG:
            if gopt._outdegreemax==None or self.DG.out_degree(n)<=gopt._outdegreemax:
                if gopt._mindegree!=None:
                    if self.DG.degree(n)>=gopt._mindegree:
                        filter.append(n)
                else:
                    if gopt._indegree!=None:
                        if self.DG.in_degree(n)>=gopt._indegree:
                            filter.append(n)
                    if gopt._outdegree!=None:
                        if self.DG.out_degree(n)>=gopt._outdegree:
                            filter.append(n)
        #the filter represents the intersect of the *degreesets
        #indegree and outdegree values are ignored if mindegree is set
        filter=set(filter)
        H=self.DG.subgraph(filter)
        #Superstitiously, perhaps, make sure we only grab nodes that project edges...
        filter= [n for n in H if H.degree(n)>0]
        L=H.subgraph(filter)
        #print "Filter set:",filter
        
        Utils.report("Order %d and Size %d"%(L.order(),L.size()))
        #L=labelGraph(L,filter)
        
        if gopt._mindegree==None: tm='X'
        else: tm=str(gopt._mindegree)
        if gopt._indegree==None: ti='X'
        else: ti=str(gopt._indegree)
        if gopt._outdegree==None: to='X'
        else: to=str(gopt._outdegree)
        if gopt._outdegreemax==None: tom='X'
        else: tom=str(gopt._outdegreemax)
        st='/'.join([gopt._projname,userID._name+'_google'+Def.typ+Def.typ2+'degree_'+tm+'_'+ti+'_'+to+'_'+tom+"_esp"])
        Utils.report(nx.info(L))
        nx.write_graphml(L, st+".graphml")
        nx.write_edgelist(L, st+".txt",data=False)
        #save it to a PNG
        nx.draw(L)
        plt.savefig("graph.png")

def main():
    # parse command line options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help"])
    except getopt.error, msg:
        print msg
        print "for help use --help"
        sys.exit(2)
    # process options
    for o, a in opts:
        if o in ("-h", "--help"):
            print __doc__
            sys.exit(0)
    # process arguments
    #for arg in args:
       # process(arg) # process() is defined elsewhere
    # Build or check folders for cache and output graph files
    FolderUtils.check()
    #Direct graph structure to hold the social graph
    directGraph=nx.DiGraph()
    rootNode=UserID()
    # The hard core job is here now!
    crawler=GraphExplorer(rootNode, directGraph)
    # Here we go must run in a Thread
    ## Do a DFS exploration of the google plus graph and cache the data
    crawler.start()
    graphOptions=GraphOptions()
    userID=UserID()
    crawler.filterNet(graphOptions, userID)
    sys.exit(0)
    
if __name__ == "__main__":
    main()
    
