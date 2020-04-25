import numpy as np
import nltk
from nltk.corpus import stopwords
from nltk.corpus import wordnet as wn
from nltk.tree import Tree, ParentedTree
from nltk.stem.snowball import SnowballStemmer
from pycorenlp import StanfordCoreNLP
from collections import defaultdict


def cosineSimilarity(v1, v2):
    if sum(v1) == 0 or sum(v2) == 0:
        return 0
    a = np.array(v1)
    b = np.array(v2)
    dot = np.dot(a, b)
    norma = np.linalg.norm(a)
    normb = np.linalg.norm(b)
    cos = dot / (norma * normb)
    return cos


class whAnswer():

    def __init__(self, filepath):
        self.file = open(filepath, "r").read()

        self.nlp = StanfordCoreNLP("http://localhost:9000")

        self.stemmer = SnowballStemmer("english")

        self.qw = {"What", "Who", "When", "Where", "Why", "Which", "How"}
        # handle new lines
        self.sentences = []
        for lines in self.file.split("\n"):
            for sent in nltk.sent_tokenize(lines):
                if "." in sent or "!" in sent:
                    self.sentences.append(sent)

        # train word embeddings
        self.embeddings_dict = defaultdict(int)
        with open("glove.6B/glove.6B.50d.txt", "r", encoding="utf-8") as f:
            for line in f:
                values = line.split()
                word = values[0]
                vector = np.asarray(values[1:], "float32")
                self.embeddings_dict[word] = sum(vector)/len(vector) # take average

        self.sw = stopwords.words("english")


    # use cos similarity of word embedding vectors to identify sentence
    # similar to the question
    def getSimilarSentences(self, question):
        qWords = nltk.word_tokenize(question)
        qSet = {w.lower() for w in qWords if w not in self.sw and w not in self.qw}
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

        # calculate and sort by cosine similarity of word embeddings
        similarity = {}
        for i in range(len(embeddings)):
            v1, v2 = embeddings[i]
            similarity[i] = cosineSimilarity(v1, v2)

        sortedSim = [k for k, v in sorted(similarity.items(), key=lambda item: -item[1])]
        return self.sentences[sortedSim[0]]


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
        verbPhrases = []
        inQuote = False # do not split noun phrases in a quote
        for tree in parented:
            for subtree in tree.subtrees():
                if subtree.label() == 'VP' and not inQuote:
                    t = subtree
                    t = ' '.join(t.leaves())
                    verbPhrases.append(t)
                if subtree.left_sibling() and subtree.left_sibling().label() == '``':
                    inQuote = True
                if subtree.label() == '\'\'':
                    inQuote = False
        return sorted(verbPhrases, key=len)


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
        nerTags = self.getNerTags(sentence)
        candidates = []
        for token in nerTags:
            ner = token['ner']
            text = token['text']
            if (text not in question and
                (ner == 'LOCATION' or ner == 'CITY' or ner == 'COUNTRY')):
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
            if dep['dep'] == 'ROOT' and dep['dependentGloss'].lower() != subj.lower():
                return False
            if dep['dep'] != 'ROOT' and dep['governorGloss'].lower() != subj.lower():
                return False
        return True


    def howAnswer(self, question, sentence):
        if 'How many' in question or 'How much' in question:
            dependency = self.getDependencyParse(question)
            subj = None
            for dep in dependency:
                if dep['dependentGloss'] == 'many':
                    subj = dep['governorGloss']
                    break
            if subj != None:
                nounPhrases = self.getNounPhrases(sentence)
                for np in nounPhrases:
                    if self.isDep(np, subj):
                        return np[0].upper() + np[1:]

        return sentence


if __name__ == '__main__':
    wa = whAnswer("./noun_counting_data/a1.txt")
    questions = [
    "What video game series did Gyarados first show up?",
    "What is a Gyarados?",
    "What is Gyarados known in the Pokemon world for?",
    "What was Gyarados's beta name?",
    "What happens when Gyarados Mega Evolves?",
    "Which anime did Gyarados first appear in?",
    "Which chapter of Pokemon Adventures does Gyarados appear in?",
    "Which flying type moves can Gyarados learn?",
    "Who voiced Gyarados in English media?",
    "Who owns a Gyarados?",
    "Who owns a red Gyarados?",
    "Where does Gyarados live?",
    "Why is Gyarados hard to obtain?",
    "Why is Gyarados naturally violent?",
    "How many fins does Gyarados have?",
    "How many Magikarp Candies are needed to evolve Gyarados?",
    "When can a carp evolve into a dragon?",
    ]
    for q in questions:
        print("Q: "+q)
        q = q[:-1]
        s = wa.getSimilarSentences(q)
        ### naive approach just for testing
        type = q.split(" ")[0]
        if type == "What" or type == "Which":
            print(wa.whatAnswer(q, s))
        elif type == "When":
            print(wa.whenAnswer(q, s))
        elif type == "Where":
            print(wa.whereAnswer(q, s))
        elif type == "Who":
            print(wa.whoAnswer(q, s))
        elif type == "Why":
            print(wa.whyAnswer(q, s))
        elif type == "How":
            print(wa.howAnswer(q, s))

    wa2 = whAnswer("./Development_data/set1/a1.txt")
    questions2 = [
    # "What is the Old Kingdom frequently referred to as?",
    # "What is the Old Kingdom also known as?",
    # "What is the Old Kingdom famous for?",
    # "What is the ancient Egyptian name for Memphis?",
    "What are independent Egyption states known as?",
    # "Who was the first king of the Old Kingdom?",
    # "Who was Sneferu succeeded by?",
    # "Who succeeded Sahure?",
    # "Who built the Great Pyramid of Giza?"
    # "Where was the royal capital of Egypt?",
    # "Where did a new era of building start?",
    # "Who built the Great Pyramid of Giza?",
    # "Who perfected the art of pyramid building?",
    # "Who ordered the construction of the Step Pyramid?",
    # "Who was King Djoser's architect?",
    # "Who succeeded Sneferu?",
    # "Who was Imhotep?",
    # "Who named the term Old Kingdom?",
    # "Who introduced the prenomen?",
    ]
    for q in questions2:
        print("Q: "+q)
        q = q[:-1] # remove question mark
        s = wa2.getSimilarSentences(q)
        type = q.split(" ")[0]
        if type == "What" or type == "Which":
            print(wa2.whatAnswer(q, s))
        elif type == "When":
            print(wa2.whenAnswer(q, s))
        elif type == "Where":
            print(wa2.whereAnswer(q, s))
        elif type == "Who":
            print(wa2.whoAnswer(q, s))
        elif type == "Why":
            print(wa2.whyAnswer(q, s))
        elif type == "How":
            print(wa2.howAnswer(q, s))

    # wa3 = whAnswer("./Development_data/set2/a1.txt")
    # questions3 = [
    # "What is Indus Valley Civilisation named after?",
    # "Where was Indus Valley Civilisation?",
    # ]
    # for q in questions3:
    #     q = q[:-1]
    #     s = wa3.getSimilarSentences(q)
    #     print(wa3.whereAnswer(q, s))
