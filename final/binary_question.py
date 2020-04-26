from tree_operations import *
from sentence_processing import pre_clean, post_clean
from nltk import pos_tag

invertible_aux_verb = {'am', 'are', 'is', 'was', 'were', 'can', 'could', 'may', 'might',
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
        doc = self.sp(npWord)

        for ent in doc.ents:
            # print(f'ent text : {ent.text}\n')
            # print(f'ent label : {ent.label}\n')
            text = ent.text
            label = ent.label
            if label == 383 or label == 380: #"PERSON":
                question.append(f"What {vpWord}?")
                break
            elif label == 381: # "PEOPLE":
                question.append(f"Who {vpWord} ?")
                break
            # elif label == 380: # "object":
            #     question.append(f"What {vpWord} ?")
        innerNPtype = np[0].label()

        # if innerNPtype == "CD":
        #     question.append(f"How many {npWord} ?")
        # if innerNPtype == "NNS":
        #     #question.append(f"Who are {npWord} ?")
        #     question.append(f"What are {npWord} ?")
        #     question.append(f"What {npWord} {vpWord} ?")
        #     question.append(f"Why do {npWord} {vpWord} ?")
        assert (np.label() == 'NP')
        assert (vp.label() == 'VP')
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
                print(e)
                failed += 1
        return parsed_list, (total, matched, failed)
            
