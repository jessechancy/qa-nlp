from nltk.parse.corenlp import CoreNLPServer
from  nltk.parse.corenlp import CoreNLPParser
import spacy
import os
import requests

STANFORD = os.path.join("models", "stanford-corenlp-full-2018-10-05")
server = CoreNLPServer(
   os.path.join(STANFORD, "stanford-corenlp-3.9.2.jar"),
   os.path.join(STANFORD, "stanford-corenlp-3.9.2-models.jar"),    
)

with open("test.txt") as f:
    datum = f.read()

#print(requests.post('http://[::]:9000/?properties={"annotators":"tokenize,ssplit,pos","outputFormat":"json"}', data = {'data': datum}).text)
#server.start()

nlp = spacy.load('en_core_web_sm')

doc = nlp(datum)

question = []
for ent in doc.ents:
    text = ent.text
    label = ent.label_
    if label =="GPE":
        question.append("Where is "+text+" ?")
    elif label == "PERSON":
        question.append("Who is "+text+" ?")
    elif label == "DATE":
        question.append("What happened in "+text+" ?")

#wh = ["What","Why","Where","Who","When"]

parser = CoreNLPParser()
parse = next(parser.raw_parse("I put the book in the box on the table."))
'''
import wikipedia
print(wikipedia.page(title="Book").content)
'''
print(question)
print(parse)
