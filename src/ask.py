import nltk
from nltk.parse.corenlp import CoreNLPServer
from nltk.parse.corenlp import CoreNLPParser
from nltk.parse.corenlp import CoreNLPDependencyParser
from nltk.tree import Tree
from question_generator import QuestionGenerator
from question_ranker import rank
import os
import requests
import spacy
import neuralcoref
from pytextrank import TextRank
from argparse import ArgumentParser

#function taken from neuralcoref source files and edited for our purposes
def get_resolved(doc, clusters):
    ''' Return a list of utterrances text where the coref are resolved to the most representative mention'''
    sentences = [sent.string.strip() for sent in doc.sents]
    token_labels = []
    for i in range(len(sentences)):
        for j in range(len(list(tok.text_with_ws for tok in sp(sentences[i])))):
            token_labels.append(i)
    resolved = list(tok.text_with_ws for tok in doc)
    if len(resolved) != len(token_labels):
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

#sentences picked should end with full stop and start with a capitalized letter
def prune_sentences(sentences):
    i = 0
    while i < len(sentences):
        if sentences[i][-1] != ".":
            sentences.pop(i)
            #pop the sentence after the one that doesn't end with a full stop
            if len(sentences) > i:
                sentences.pop(i)
        elif ord(sentences[i][0]) > 90 or ord(sentences[i][0]) < 65:
            sentences.pop(i)
        else:
            i += 1

if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument("--input", action='store', required=True)
    parser.add_argument("--output", action='store', required=True)
    args = parser.parse_args()

    # requests.post('http://[::]:9000/?properties={"annotators":"tokenize,ssplit,pos","outputFormat":"json"}', 
    #             data = {'data': "tmp"}).text

    sp = spacy.load('en_core_web_lg')

    # Add pipes for SpaCy
    neuralcoref.add_to_pipe(sp)
    #sp.add_pipe(coref, name='neuralcoref')
    tr = TextRank()
    sp.add_pipe(tr.PipelineComponent, name="textrank", last=True)

    with open(args.input, 'r') as f:
        content = f.read()
        sp_file = sp(content)

    phrase_ranks = sp_file._.phrases
    coref_resolved = get_resolved(sp_file, sp_file._.coref_clusters)
    sentences = [sent.string.strip() for sent in sp(coref_resolved).sents]
    prune_sentences(sentences)

    parser = CoreNLPParser(url='http://localhost:9000')
    generator = QuestionGenerator(sentences, parser, sp)
    print("Generating Questions...")
    questions, _ = generator.get_questions()
    print("Done.")
    print("Ranking Questions...")
    ranked_questions = rank(questions, phrase_ranks)
    print("Done.")
    with open(args.output, "w+") as f:
        f.write("\n".join(ranked_questions))
