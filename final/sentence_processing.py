import re

def post_clean(sentence):
    sentence = sentence.replace('`` ', '\"')
    sentence = sentence.replace(' \'\'', '\"')
    sentence = sentence.replace('-RRB-', '')
    sentence = sentence.replace('-LRB-', '')
    sentence = sentence.replace(' -- ', '--')
    sentence = re.sub(';([.*? ^ \?]*) ?', '?', sentence)
    sentence = re.sub(' (?=[,:\.\?!\'%])', '', sentence)
    return sentence
        
def pre_clean(sentence):
    left_paren = 0
    remove = []
    sent_list = list(sentence)
    for i in range(len(sentence)):
        if left_paren > 0:
            remove.append(i)
        if sentence[i] == ')':
            left_paren -= 1
        if sentence[i] == '(':
            left_paren += 1
            if i > 0:
                remove.append(i-1)
            remove.append(i)
    for i in range(len(remove)-1, -1, -1):
        sent_list.pop(remove[i])
    return "".join(sent_list)