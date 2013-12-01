#!/usr/bin/env python
# coding=utf8

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
import matplotlib.pyplot as plt
import getopt
import sys
import os
import logging
import json
import datetime
import time
logger = logging.getLogger('root')

class GraphResource:
    def __init__(self, cache_dir='reports'):

        self.cache_dir = cache_dir
        self.checkDir()
    def checkDir(self):
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            
    def fetch(self, oid, format="graphml", max_age=0):
        # If the file was already fetched check the timestamp and overwrite
        graphml = os.path.join(self.cache_dir, oid+ ".graphml")
        graphpng = os.path.join(self.cache_dir, oid+ ".png")
        graphgexf  = os.path.join(self.cache_dir, oid+ ".gexf")
        logger.debug("Fetching "+graphml)
        if os.path.exists(graphml):
            ## cache hit was old and we have to refresh it
            if int(time.time()) - os.path.getmtime(graphml ) > max_age:
                DG=nx.read_graphml(graphml)
                labels=dict((n,d['label']) for n,d in DG.nodes(data=True))
                nx.draw_networkx(DG,labels=labels)
                logger.debug("Generated graph "+graphpng);
                plt.savefig(graphpng)
                nx.write_gexf(DG, graphgexf )
        else: 
            logger.debug("Cache miss");
            ## cache miss we have to generate the graph, this will take time!
            return None
        if format=="graphml": 
            return json.dumps(['URL', graphml])
        elif format=="png": 
            return json.dumps(['URL', graphpng])
        elif format=="png": 
            return json.dumps(['URL', graphgexf ])
    
if __name__ == "__main__":
    main()
