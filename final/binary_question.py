from tree_operations import *
from sentence_processing import pre_clean, post_clean
from nltk import pos_tag

invertible_aux_verb = {'am', 'are', 'is', 'was', 'were', 'can', 'could',
                       'must', 'shall', 'should', 'will', 'would'}
invertible_special = {'does', 'did', 'has', 'had', 'have'}

purge_tree = {"PRN", "ADVP", "RB"} #WHNP with parent SBAR #JJ, JJR, ADJP, S with parent NP

proper_nouns = {"NNP", "NNPS"}
nouns = {"NNP", "NNPS"}
valid_determiners = {"the", "a"}
unclear_referral = {'this', 'that', 'these', 'those', 'it', 'their', 'they'}

class Questions():
    def __init__(self, sentences, parser, sp):
        self.sentences = sentences
        self.parser = parser #CoreNLPParser()
        self.sp = sp #spacy.load('en_core_web_sm')

    def is_invertible(self, s, next_phrase):
        if isinstance(s, str):
            return (s.lower() in invertible_aux_verb or 
                    s.lower() in invertible_special and next_phrase == "VP")
        return False

    def binary_question_from_tree(self, parsed_tree):
        sentence = parsed_tree[0]
        assert(sentence.label() == "S")
        np = sentence[0]
        vp = sentence[1]
        assert(np.label() == 'NP')
        assert(vp.label() == 'VP')
        if (has_label(np, {'VP'})):
            return None
        
        np_first, np_ancs = first(np)
        noun_label = np_first.label()

        if (not has_string(np, unclear_referral) and has_label(np_ancs[-1], nouns)):
            subject = tree_to_string(np, noun_label not in proper_nouns)
            remain = vp.leaves()[1:]
            vp_first, vp_ancs = first(vp)
            second = second_from_first(vp_ancs)
            if self.is_invertible(val(vp_first), second.label()):
                return list_to_string([val(vp_first).capitalize(), subject] + remain) + "?"
            else:
                #Add Do
                verb_label = vp_first.label()
                lemma = self.sp(val(vp_first))[0].lemma_
                if verb_label in ["VBP", "VBZ", "VBG"]:
                    return list_to_string(["Does", subject, lemma] + remain) + " ?"
                elif verb_label in ["VBD", "VBN"]: #past tense
                    return list_to_string(["Did", subject, lemma] + remain) + " ?"
        return None
    
    def wh_questions_from_tree(self, parsed_tree):
        question = []
        sentence = parsed_tree[0]
        assert(sentence.label() == 'S')
        np = sentence[0]
        vp = sentence[1]

        vpWord = " ".join(vp.leaves())
        npWord = " ".join(np.leaves())
        plural = False
        if (has_label(np, {'NNS', 'NNPS'})):
            plural = True
        doc = self.sp(npWord)
        prev = None
        for ent in doc.ents:
            text = ent.text
            label = ent.label_
            if prev != None and label != prev:
                return None
            prev = label
            if label == 'ORG':
                question.append(f"What {vpWord} ?")
            elif label == 'PERSON':
                question.append(f"Who {vpWord} ?")
            elif label == 'NORP':
                question.append(f"Which {'groups' if plural else 'group'} {vpWord} ?")
            elif label == 'TIME' or label == 'DATE':
                question.append(f"When {vpWord} ?")
            elif label == 'GPE':
                question.append(f"Which {'bodies' if plural else 'body'} {vpWord} ?")
            elif label == 'EVENT' or label == 'PRODUCT':
                question.append(f"What {vpWord} ?")
        return question

    def get_questions(self):
        parsed_list = []
        total = 0
        matched = 0
        failed = 0
        for i in range(len(self.sentences)): 
            sentence = self.sentences[i]
            try: 
                sentence = pre_clean(sentence)
                parse = next(self.parser.raw_parse(sentence))
                #print(parse)
                purge(parse, purge_tree)
                if satisfies_simple_pred(parse):
                    pp_count = count_pp(parse)
                    binary_question = self.binary_question_from_tree(parse)
                    wh_questions = self.wh_questions_from_tree(parse)
                    if binary_question != None:
                        matched += 1
                        parsed_list.append((post_clean(binary_question), i, pp_count))
                    for q in wh_questions:
                        parsed_list.append((post_clean(q), i, pp_count))
                    total += 1
            except Exception as e:
                failed += 1
        return parsed_list, (total, matched, failed)
            
