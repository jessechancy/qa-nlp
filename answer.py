import nltk
import os
from nltk.parse import CoreNLPParser
import subprocess
import signal
import psutil

#FIXME: This method does not properly stop the active process
#DO NOT USE WITHOUT UPDATING

'''
os.system("cd stanford-corenlp-full-2018-10-05; java -mx4g -cp '*' edu.stanford.nlp.pipeline.StanfordCoreNLPServer \
-preload tokenize,ssplit,pos,lemma,ner,parse,depparse \
-status_port 9000 -port 9000 -timeout 15000 &")
'''

test = subprocess.Popen("cd stanford-corenlp-full-2018-10-05; java -mx4g -cp '*' edu.stanford.nlp.pipeline.StanfordCoreNLPServer \
-preload tokenize,ssplit,pos,lemma,ner,parse,depparse \
-status_port 9000 -port 9000 -timeout 15000 &", shell=True)

test_pid = test.pid
p = psutil.Process(test_pid)
p_java = psutil.Process(test_pid+1)
parent_pid = p.ppid()
parent_java_pid = p_java.ppid()
print(test_pid)
print(parent_pid)
print(parent_java_pid)

#os.killpg(os.getpgid(test.pid), signal.SIGTERM)
os.system("kill %s" % (test_pid))
os.system("kill %s" % (parent_pid))