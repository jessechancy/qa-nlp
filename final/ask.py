import nltk
from nltk.parse.corenlp import CoreNLPServer
from nltk.parse.corenlp import CoreNLPParser
from nltk.parse.corenlp import CoreNLPDependencyParser
from nltk.tree import Tree
from binary_question import Questions
from rank import rank
import os
import requests
import spacy
import neuralcoref

requests.post('http://[::]:9000/?properties={"annotators":"tokenize,ssplit,pos","outputFormat":"json"}', 
              data = {'data': "tmp"}).text

parser = CoreNLPParser()
sp = spacy.load('en_core_web_lg')
neuralcoref.add_to_pipe(sp)

content = []
for i in range(1, 2):
    with open(f'./../Development_data/set2/a{i}.txt', 'r') as f:
        content.append(f.read())

def get_resolved(doc, clusters):
    ''' Return a list of utterrances text where the coref are resolved to the most representative mention'''
    sentences = [sent.string.strip() for sent in doc.sents]
    token_labels = []
    for i in range(len(sentences)):
        for j in range(len(list(tok.text_with_ws for tok in sp(sentences[i])))):
            token_labels.append(i)
    resolved = list(tok.text_with_ws for tok in doc)
    if len(resolved) != len(token_labels):
        print("FAILED COREF")
        return ''.join(resolved)
    for cluster in clusters:
        seen = set()
        for coref in cluster:
            if coref != cluster.main and token_labels[coref.start] not in seen:
                resolved[coref.start] = cluster.main.text + doc[coref.end-1].whitespace_
                for i in range(coref.start+1, coref.end):
                    resolved[i] = ""
            seen.add(token_labels[coref.start])
    return ''.join(resolved)

sentences = []
for file in content:
    tmp_file = sp(file)
    coref_text = get_resolved(tmp_file, tmp_file._.coref_clusters)
    new_sentences = [sent.string.strip() for sent in sp(coref_text).sents]
    sentences.extend(new_sentences)

i = 0
while i < len(sentences):
    if sentences[i][-1] != ".":
        sentences.pop(i)
        if len(sentences) > i:
            sentences.pop(i)
    elif ord(sentences[i][0]) > 90 or ord(sentences[i][0]) < 65:
        sentences.pop(i)
    else:
        i += 1

q = Questions(sentences, parser, sp)
indexed_questions, performance = q.get_questions()
questions = rank(indexed_questions)
for question in questions:
    print(question)
print(performance)
