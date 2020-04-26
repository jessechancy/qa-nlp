#!/usr/bin/env python3
import os
import sys
import nltk
import numpy as np
import string
from nltk.parse import CoreNLPParser, CoreNLPDependencyParser
from nltk.corpus import stopwords
from nltk.corpus import wordnet as wn
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.stem.snowball import SnowballStemmer
from nltk.tree import Tree, ParentedTree
from pycorenlp import StanfordCoreNLP
from collections import defaultdict

class QuestionPreprocess():
    def __init__(self, filepath):

        self.quesF = open(filepath, "r")
        text = self.quesF.read()
        self.questions = text.split("\n")
        self.quesF.close()

    def getQuestions(self):
        return self.questions

class AnswerPreprocess():

    def __init__(self, filepath):
        self.fileText = open(filepath, "r").read()

        self.parser = CoreNLPParser(url='http://localhost:9000')
        self.sw = stopwords.words("english")

        # handle new lines - FIXME: Ask Sojeong about this note, might be related to an issue I had as well
        self.sentences = []
        for lines in self.fileText.split("\n"):
            for sent in nltk.sent_tokenize(lines):
                if "." in sent or "!" in sent:
                    self.sentences.append(sent)

        # train word embeddings
        self.embeddings_dict = defaultdict(int)
        with open("glove.6B.50d.txt", "r", encoding="utf-8") as f:
            for line in f:
                values = line.split()
                word = values[0]
                vector = np.asarray(values[1:], "float32")
                self.embeddings_dict[word] = sum(vector)/len(vector) # take average


    def cosineSimilarity(self, v1, v2):
        if sum(v1) == 0 or sum(v2) == 0:
            return 0
        a = np.array(v1)
        b = np.array(v2)
        dot = np.dot(a, b)
        norma = np.linalg.norm(a)
        normb = np.linalg.norm(b)
        cos = dot / (norma * normb)
        return cos

    # use cos similarity of word embedding vectors to identify sentence
    # similar to the question
    def getSimilarSentences(self, question):
        qWords = nltk.word_tokenize(question)
        qWords[0] = qWords[0].lower() # convert question word to lowercase
        qSet = {w.lower() for w in qWords if w not in self.sw}

        embeddings = []
        for sentence in self.sentences:
            words = nltk.word_tokenize(sentence)
            wordSet = {w.lower() for w in words if w not in self.sw}
            combined = wordSet.union(qSet)
            sentenceEmbedding = []
            qEmbedding = []
            for w in combined:
                if w in wordSet:
                    sentenceEmbedding.append(self.embeddings_dict[w])
                else:
                    sentenceEmbedding.append(0)
                if w in qSet:
                    qEmbedding.append(self.embeddings_dict[w])
                else:
                    qEmbedding.append(0)
            embeddings.append((sentenceEmbedding, qEmbedding))

        # calculate and sort by cosine similarity
        similarity = {}
        for i in range(len(embeddings)):
            v1, v2 = embeddings[i]
            similarity[i] = self.cosineSimilarity(v1, v2)
        sortedSim = [k for k, v in sorted(similarity.items(), key=lambda item: -item[1])]

        # if sortedSim[0] != 0:
        #     self.prevSentence = self.sentences[sortedSim[0]-1]

        return self.sentences[sortedSim[0]]

    #getDeclarativeAndWhWord Auxiliary functions

    #from question generation
    def list_to_string(self, word_list):
        return ' '.join(word_list)

    #from question generation
    def tree_to_string(self, parsed_tree):
        return self.list_to_string(parsed_tree.leaves())

    #Recurse until string of the wh word is found
    def find_wh_word(self, question):

        #print(question)
        if isinstance(question, str):
            return ""

        if question.label() in {"WP", "WDT", "WP$", "WRB"}:
            return question[0]

        else:
            for i in range(len(question)):
                result = self.find_wh_word(question[i])

                if result != "":
                    return result

        return ""

    #Return string of wh word
    def get_wh_word(self, question):

        wh_word = self.find_wh_word(question)
        new_sentence = self.tree_to_string(question)

        return [wh_word, new_sentence]

    #Take question tree and place verb in location after first NP with a following phrase
    #If no following phrase, place verb at end of sentence
    def recurse_make_binary_declarative(self, question, verb, lvl):
        if (lvl == 1 and len(question) >= 3) or (lvl > 1 and len(question) >= 2): #eg VBZ, NP, VP for lvl 1
            if (lvl == 1):
                ind = 1
            else:
                ind = 0
            if question[ind].label().startswith("N"):
                n = question[ind]
                full_list = [self.tree_to_string(n), verb]

                remaining = []
                for i in range(ind+1, len(question)):
                    remaining.append(self.tree_to_string(question[i]))

                full_list.extend(remaining)
                full = self.list_to_string(full_list)
                return full

            #Cannot handle this form if the next thing after
            # verb isnt a noun phrase/noun
            else:
                #print("ERROR: COULD NOT DETERMINE WHERE TO PLACE VERB. NO NOUN PHRASE.")
                return ""

        else:
            if (lvl == 1):
                result = self.recurse_make_binary_declarative(question[1], verb, 2)
                return result
            elif (lvl > 1):
                result = self.recurse_make_binary_declarative(question[0], verb, lvl+1)
                return result

    #Return string form of reformed question as a declarative statement
    def make_binary_declarative(self, question):
            verb = question[0]
            result = self.recurse_make_binary_declarative(question, verb[0], 1)

            if result == "":
                #print("ERROR: COULD NOT RECONFIGURE")
                return self.tree_to_string(question)

            return result

    #Return a list of [question_word, was_declarative, new_sentence]
    # question_word: if question was in wh form, returns the corresponding
    #  wh word
    # was_declarative: if question was parsed as a declarative statement,
    #  or was unparsable this is True
    # new_sentence: new parsed form of question, if binary question
    #  then rearranged, else simply uniform spacing (question mark may still
    #  be attached)
    def getDeclarativeAndWhWord(self, question):
        split_question = question.split()

        #Make only first word lowercase to best preserve proper nouns
        split_question[0] = split_question[0].lower()
        result = self.parser.parse(split_question)
        listResult = list(result)
        parsed_tree = listResult[0]
        #print(parsed_tree)

        was_declarative = False #Mark if question was parsed declarativef
        question_word = ""
        question = parsed_tree[0] #Indexing the ROOT

        if question.label() == "SBARQ":
            #Check to make sure "SQ" doesnt follow in case it was just misclassified
            if question[0].label() == "SQ":
                #Gets rid of random previous "SBARQ"
                question = question[0]
                new_sentence = self.make_binary_declarative(question)
            else:
                [question_word, new_sentence] = self.get_wh_word(question)
        elif question.label() == "SQ":
            new_sentence = self.make_binary_declarative(question)

        else:
            [question_word, new_sentence] = self.get_wh_word(question)
            if question_word == "": # Last check in case wh-question was missed
                was_declarative = True
                new_sentence = self.tree_to_string(question)
                #NOTE: May not want to use this new sentence as some tokens may be altered,
                # example "(" and ")" become "-LRB-" and "-RRB-" respectively

        return [question_word, was_declarative, new_sentence]

class WhAnswer():

    def __init__(self):
        self.nlp = StanfordCoreNLP("http://localhost:9000")

        self.stemmer = SnowballStemmer("english")

        self.qw = {"What", "Who", "When", "Where", "Why", "Which", "How"}

        self.sw = stopwords.words("english")

    def getNounPhrases(self, sentence):
        # convert tree str to a list of noun phrases
        trees = self.getParseTree(sentence)
        parented = ParentedTree.convert(trees)
        nounPhrases = []
        inQuote = False # do not split noun phrases in a quote or parenthesis
        for tree in parented:
            for subtree in tree.subtrees():
                if subtree.label() == '-LRB-':
                    inQuote = True
                if subtree.label() == 'NP' and not inQuote:
                    t = subtree
                    t = ' '.join(t.leaves())
                    if t not in self.sw:
                        nounPhrases.append(t)
                if subtree.left_sibling() and subtree.left_sibling().label() == '``':
                    inQuote = True
                if subtree.label() == '\'\'' or subtree.label() == '-RRB-':
                    inQuote = False
        return nounPhrases


    def getVerbPhrases(self, sentence):
        # convert tree str to a list of noun phrases
        trees = self.getParseTree(sentence)
        parented = ParentedTree.convert(trees)
        nounPhrases = []
        inQuote = False # do not split noun phrases in a quote
        for tree in parented:
            for subtree in tree.subtrees():
                if subtree.label() == 'VP' and not inQuote:
                    t = subtree
                    t = ' '.join(t.leaves())
                    nounPhrases.append(t)
                if subtree.left_sibling() and subtree.left_sibling().label() == '``':
                    inQuote = True
                if subtree.label() == '\'\'':
                    inQuote = False
        return nounPhrases


    def getParseTree(self, sentence):
        output = self.nlp.annotate(sentence, properties={
            'annotators': 'ner,parse',
            'outputFormat': 'json'
        })
        return Tree.fromstring(output['sentences'][0]['parse'])


    def getDependencyParse(self, sentence):
        output = self.nlp.annotate(sentence, properties={
            'annotators': 'depparse',
            'outputFormat': 'json'
        })
        return output['sentences'][0]['basicDependencies']


    def getPosTags(self, sentence):
        output = self.nlp.annotate(sentence, properties={
            'annotators': 'pos',
            'outputFormat': 'json'
        })
        return output['sentences'][0]['tokens']


    def corefResolution(self, sentence):
        output = self.nlp.annotate(sentence, properties= {
            'annotators': 'coref',
            'outputFormat': 'json'
        })
        return output['corefs']


    def getNerTags(self, sentence):
        output = self.nlp.annotate(sentence, properties={
            'annotators': 'ner',
            'outputFormat': 'json'
        })
        return output['sentences'][0]['entitymentions']


    def whoAnswer(self, question, sentence):
        nerTags = self.getNerTags(sentence)
        candidates = []
        for token in nerTags:
            if token['text'] not in question and token['ner'] == 'PERSON':
                tag = nltk.pos_tag(token['text'])
                if tag[0][1] == 'NNP':
                    candidates.append(token['text'])
        # return the word with PERSON tag if only one exists
        if len(candidates) == 1:
            return candidates[0]

        return self.generalAnswer(question, sentence)


    def whereAnswer(self, question, sentence):
        # print(sentence)
        nerTags = self.getNerTags(sentence)
        candidates = []
        for token in nerTags:
            ner = token['ner']
            text = token['text']
            if (text not in question and
                (ner == 'LOCATION' or ner == 'CITY' or ner == 'COUNTRY')):
                # tag = nltk.pos_tag(token['text'])
                # if tag[0][1] == 'NNP':
                candidates.append(text)

        if len(candidates) == 1:
            return candidates[0][0].upper() + candidates[0][1:]

        qWords = {w.lower() for w in nltk.word_tokenize(question) if w not in self.sw}
        trees = self.getParseTree(sentence)
        for tree in trees:
            for subtree in tree.subtrees():
                if subtree.label() == 'PP':
                    t = subtree
                    if not self.inQuestion(t.leaves(), qWords):
                        t = ' '.join(t.leaves())
                        return t[0].upper() + t[1:]

        return self.generalAnswer(question, sentence)


    def inQuestion(self, words, qWords):
        for w in words:
            if w.lower() in qWords:
                return True
        return False


    def whenAnswer(self, question, sentence):
        qWords = {w.lower() for w in nltk.word_tokenize(question) if w not in self.sw}
        trees = self.getParseTree(sentence)
        parented = ParentedTree.convert(trees)
        clauses = []
        for tree in parented:
            for subtree in tree.subtrees():
                t = subtree
                if t.parent().label() == 'SBAR' and t.label() == 'S' and self.inQuestion(t.leaves(), qWords):
                    return ' '.join(subtree.leaves()).capitalize() + '.'

        return sentence


    def whatAnswer(self, question, sentence):
        # print(sentence)
        # return verb phrase if the main clause of the question contains VP
        qWords = {w.lower() for w in nltk.word_tokenize(question) if w not in self.sw}
        verbPhrases = self.getVerbPhrases(sentence)
        qParse = self.getParseTree(question)
        parented = ParentedTree.convert(qParse)
        for tree in parented:
            for subtree in tree.subtrees():
                label = subtree.label()
                parent = subtree.parent().label()
                if (label == 'VP' and ((parent == 'SQ' and not subtree.left_sibling() and not subtree.right_sibling()) or
                    (subtree.left_sibling() and 'What' in subtree.left_sibling().leaves()))):
                    for vp in verbPhrases:
                        if not self.inQuestion(vp.split(), qWords):
                            return vp[0].upper() + vp[1:]

        return self.generalAnswer(question, sentence)

    def generalAnswer(self, question, sentence):
        qWords = {w.lower() for w in nltk.word_tokenize(question) if w not in self.sw}
        verbPhrases = self.getVerbPhrases(sentence)
        qVerbs = {self.stemmer.stem(w) for w in qWords if nltk.pos_tag([w])[0][1][0] == 'V'}
        # remove noun phrases that contain words in the question
        nounPhrases = [c for c in self.getNounPhrases(sentence) if not self.inQuestion(nltk.word_tokenize(c), qWords)]
        # if there is a verb phrase that contains a verb from the question,
        # return the noun phrase in the verb phrase
        res = None
        for vp in verbPhrases:
            tag = nltk.pos_tag(vp.split())[0]
            if tag[1][0] == 'V':
                stemmed = self.stemmer.stem(tag[0].lower())
                if stemmed in qVerbs:
                    for np in nounPhrases:
                        if np in vp:
                            if res == None or len(res) > len(np):
                                res = np
                else:
                    for synset in wn.synsets(tag[0]):
                        for lemma in synset.lemmas():
                            if lemma.name() in qVerbs:
                                for np in nounPhrases:
                                    if np in vp:
                                        if res == None or len(res) > len(np):
                                            res = np
                                    break
        if res != None:
            return res[0].upper() + res[1:]

        # use dependency tree to check if there are words in NP that
        # are dpendent to the words in the question
        res = None
        dependency = self.getDependencyParse(sentence)
        for np in nounPhrases:
            for d in dependency:
                dep = d['dependentGloss']
                gov = d['governorGloss']
                if ((gov in np and gov.lower() not in qWords and dep.lower() in qWords) or
                    (dep in np and dep.lower() not in qWords and gov.lower() in qWords)):
                    if res == None:
                        res = np
                    elif len(np) < len(res):
                        res = np

        return (res[0].upper() + res[1:]) if res else sentence


    def whyAnswer(self, question, sentence):
        dependency = self.getDependencyParse(sentence)
        res = ""
        prev = None
        for dep in dependency:
            if dep['dep'] == 'mark':
                res += dep['dependentGloss']
                res = res[0].upper() + res[1:]
            elif len(res) > 0:
                if dep['dep'] == 'punct':
                    if dep['dependentGloss'] == '-LRB-':
                        res += " ("
                    elif dep['dependentGloss'] == '-RRB-':
                        res += ")"
                    else:
                        res += dep['dependentGloss']
                else:
                    if prev == '-LRB-':
                        res += dep['dependentGloss']
                    else:
                        res += ' ' + dep['dependentGloss']
            prev = dep['dependentGloss']

        if len(res) == 0:
            return sentence

        return res


    def isDep(self, phrase, subj):
        npDep = self.getDependencyParse(phrase)
        for dep in npDep:
            if dep['dep'] == 'ROOT' and dep['dependentGloss'] != subj:
                return False
            if dep['dep'] != 'ROOT' and dep['governorGloss'] != subj:
                return False
        return True


    def howAnswer(self, question, sentence):
        if 'How many' in question or 'How much' in question:
            dependency = self.getDependencyParse(question)
            subj = None
            for dep in  dependency:
                if dep['dependentGloss'] == 'many':
                    subj = dep['governorGloss']
                    break
            if subj != None:
                nounPhrases = self.getNounPhrases(sentence)
                for np in nounPhrases:
                    if self.isDep(np, subj):
                        return np[0].upper() + np[1:]

        return sentence

class BinAnswer():
    def __init__(self):
        self.dep_parser = CoreNLPDependencyParser(url='http://localhost:9000')
        self.lemmatizer = WordNetLemmatizer()

    def getDependencyParse(self, s):
        parses = self.dep_parser.parse(s.split())
        #print(s)
        result = [[(governor, dep, dependent) for governor, dep, dependent in p.triples()] for p in parses]
        return result

    def yes_no(self, ques_governors, sent_governors):

        #Check for existence of each governor in sentence
        # (with corresponding dependents when necessary)
        bool_yes = True
        #print(ques_governors.keys())
        for key in ques_governors.keys():

            #print(key)
            #If head is not in other parse, then it is false
            if key not in sent_governors.keys():
                return("NO: reason - question head not in sentence - ", key)
                bool_yes = False
                break

            #If subject and direct object are not present
            # (connected to this word), then it is false
            if ("nsubj" in ques_governors[key]):
                if ("nsubj" not in sent_governors[key]):
                    return("NO: reason - subject head not in sentence")
                    bool_yes = False
                    break
            if ("nsubjpass" in ques_governors[key]):
                if ("nsubjpass" not in sent_governors[key]):
                    return("NO: reason - subject head (pass) not in sentence")
                    bool_yes = False
                    break
            if ("dobj" in ques_governors[key]):
                if ("dobj" not in sent_governors[key]):
                    return("NO: reason - direct object head not in sentence")
                    bool_yes = False
                    break

            #If key is a verb in its lemmatized form or word
            # has an attached copula, check to see if one is
            # negated and the other is not
            #FIXME: Can make more complex check of verb tenses as well
            if "lem" in ques_governors[key] or "verb" in ques_governors[key]:
                n_neg = "neg" in ques_governors[key]
                s_neg = "neg" in sent_governors[key]

                if n_neg != s_neg:
                    return("NO: reason - negation of question in sentence")
                    bool_yes = False
                    break

        if bool_yes:
            return("YES")

    def answer(self, question, sentence):

        dep_ques = self.getDependencyParse(question)
        dep_sent = self.getDependencyParse(sentence)

        #Save governors and corresponding deps for comparison
        q_governors = dict() #NOTE: dependent are tuples while governors(keys) and dep are a string
        s_governors = dict()

        dependencies = [dep_ques[0], dep_sent[0]]
        governors = [q_governors, s_governors]

        for k in range(len(dependencies)):
            dpnd = dependencies[k]
            govs = governors[k]
            #print(dpnd)

            #build dictionary based on governors
            for item in dpnd:
                g_word = item[0][0].lower()
                #print(g_word)
                g_pos = item[0][1]
                #print(g_pos)
                dep = item[1]
                #print(dep)
                dependent = item[2]
                #print(dependent)

                #If the governor is a verb, store its base form as the key
                if g_pos.startswith("V"):
                    g_word = self.lemmatizer.lemmatize(g_word, pos="v")

                #Add new word to dictionary if not there
                if g_word not in govs:
                    govs[g_word] = dict()

                    #Check again if pos is a verb, add new field to dictionary
                    # for its pos before key base form dictionary
                    if g_pos.startswith("V"):
                        govs[g_word]["lem"] = g_pos

                if dep in ["cop", "aux", "auxpass", "neg"]: #Special case to handle verb conjugations
                    if "verb" not in govs[g_word]:
                        govs[g_word]["verb"] = set()
                    govs[g_word]["verb"].add(dependent)
                govs[g_word][dep] = dependent

        #Answer yes or no
        return(self.yes_no(q_governors, s_governors))


# Main function
if __name__ == "__main__":

    article_path = sys.argv[1]
    questions_path = sys.argv[2]

    print("START")
    print("Answer Preprocessing")
    # preProc = AnswerPreprocess("./noun_counting_data/a1.txt")
    preProc = AnswerPreprocess(article_path)
    print("Question Preprocessing")
    qProc = QuestionPreprocess(questions_path)
    wa = WhAnswer()
    ba = BinAnswer()

    questions = qProc.getQuestions()

    print("Questions")
    q_number = 0 #FIXME: Remove after testing
    for q in questions:
        print(q_number)
        q_number += 1
        print("Q: " + q)
        q_mark_removed = q[:-1]

        s = preProc.getSimilarSentences(q_mark_removed)
        [
            question_word,
            was_declarative,
            new_sentence
        ] = preProc.getDeclarativeAndWhWord(q)

        #print("Closest Sentence: " + s)
        #print("Question Word: " + question_word)
        #print("Was Declarative: " + str(was_declarative))
        #print("New Question Form: " + new_sentence)

        if new_sentence != "" and new_sentence[-1] == "?":
            new_sentence = new_sentence[:-1] #Remove question mark

        if was_declarative:
             print("A: ", wa.whatAnswer(q_mark_removed, s))

        if question_word == "what" or question_word == "which":
            print("A: ", wa.whatAnswer(q_mark_removed, s))
        elif question_word == "when":
            print("A: ", wa.whenAnswer(q_mark_removed, s))
        elif question_word == "where":
            print("A: ", wa.whereAnswer(q_mark_removed, s))
        elif question_word == "who":
            print("A: ", wa.whoAnswer(q_mark_removed, s))
        elif question_word == "why":
            print("A: ", wa.whyAnswer(q_mark_removed, s))
        elif question_word == "how":
            print("A: ", wa.howAnswer(q_mark_removed, s))
        else:
            print("A: ", ba.answer(new_sentence, s))