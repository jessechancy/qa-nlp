#!/usr/bin/env python3

import nltk
import sys, os
from nltk.parse.corenlp import CoreNLPServer
from nltk.parse.corenlp import CoreNLPParser
from nltk.parse.corenlp import CoreNLPDependencyParser
import os
from nltk.tree import Tree

import subprocess



class SST():
    def __init__(self, label, children):
        self.label = label
        self.children = children


# Sentence Structure Leaf
class SSL():
    def __init__(self, label):
        self.label = label


simple_predicate = SST('ROOT', [SST('S', [SSL('NP'), SSL('VP'), SSL('.')])])


def satisfies_structure(parsed_tree, structure):
    if isinstance(structure, SSL):
        return parsed_tree.label() == structure.label
    else:
        if parsed_tree.label() != structure.label or len(parsed_tree) != len(structure.children): return False
        for i in range(len(parsed_tree)):
            if satisfies_structure(parsed_tree[i], structure.children[i]) == False:
                return False
        return True


def list_to_string(word_list):
    return ' '.join(word_list)


def tree_to_string(parsed_tree):
    #     if isinstance(parsed_tree, str):
    #         return parsed_tree
    #     words = []
    #     for subtree in parsed_tree:
    #         words.append(tree_to_string(subtree))
    return list_to_string(parsed_tree.leaves())


def binary_question_from_tree(parsed_tree):
    sentence = parsed_tree[0]
    assert (sentence.label() == 'S')
    np = sentence[0]
    vp = sentence[1]
    assert (np.label() == 'NP')
    assert (vp.label() == 'VP')
    if vp[0].label() == 'VBZ':
        return list_to_string([vp[0][0].capitalize(), tree_to_string(np), tree_to_string(vp[1])]) + '?'
    return vp[0]


def main():
    # Lexical Parser
    # parser = CoreNLPParser(url='http://localhost:9000')
    # s = 'What is the color of a swallow, a robin, and a cardinal?'
    # NOTE: 1) Make sentence lowercase
    # Removed for now to create dry run test
    '''
    s = s.lower()
    parsed_list = list(parser.parse(s.split()))
    print(parsed_list)

    for item in parsed_list:
        print(item)
        print(item == "(ROOT")
    '''

    # Check for inputs and assign paths to open files
    # print(len(sys.argv))
    bashCommand = "nohup java -mx4g -cp \"CoreNLP/*\" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -preload tokenize,ssplit,pos,lemma,ner,parse,depparse -status_port 9000 -port 9000 -timeout 15000 &"

    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()

    article_path = sys.argv[1]
    nquestions = (int)(sys.argv[2])

    STANFORD = os.path.join("CoreNLP")

    # Create the server
    # server = CoreNLPServer(
    #     os.path.join(STANFORD, "stanford-corenlp-3.9.2.jar"),
    #     os.path.join(STANFORD, "stanford-corenlp-3.9.2-models.jar"),
    # )
    # server.start()

    artF = open(article_path, "r", encoding='utf8')
    # quesF = open(questions_path, "r",encoding='utf8')
    content = artF.read()
    sentences = nltk.sent_tokenize(content)
    parser = CoreNLPParser()
    questions_made = 0
    parse_list = []
    for sentence in sentences:
        if len(sentence) < 180:
            parse = next(parser.raw_parse(sentence))
            if satisfies_structure(parse, simple_predicate):
                # print("=========================== Sentence ======================")
                # print(parse)
                # #             print(parse.label())
                # print(sentence)
                print(binary_question_from_tree(parse))
                parse_list.append(parse)
                questions_made+=1
        if questions_made == nquestions:
            break


    artF.close()
    # quesF.close()


# Main function
if __name__ == "__main__":
    main()
