
def list_to_string(word_list):
    return ' '.join(word_list)

def tree_to_string(parsed_tree, lower=False):
    leaves = parsed_tree.leaves()
    if lower:
        leaves[0] = leaves[0].lower()
    return list_to_string(leaves)

#Returns traversal type
def first(parsed_tree):
    ancs = []
    while not isinstance(parsed_tree[0], str):
        ancs.append(parsed_tree)
        parsed_tree = parsed_tree[0]
    return (parsed_tree, ancs)

#gets the next thing that is not an anc of parsed_tree
def second_from_first(ancs):
    while len(ancs) > 0:
        anc = ancs.pop()
        if len(anc) > 1:
            return anc[1]
    return None

def val(parsed_tree):
    val = parsed_tree[0]
    if isinstance(val, str):
        return val
    return False

#Purges from the parsed tree the set of labels in purge_set
def purge(parsed_tree, purge_set):
    if isinstance(parsed_tree, str):
        return False
    if parsed_tree.label() in purge_set:
        return True
    length = len(parsed_tree)
    i = 0
    while i < length:
        res = purge(parsed_tree[i], purge_set)
        if res:
            del parsed_tree[i]
            length -= 1
        else:
            i += 1
    return False

#checks in a parsed_tree has a value in label-set
def has_label(parsed_tree, label_set):
    if isinstance(parsed_tree[0], str):
        return parsed_tree.label() in label_set
    contain = False
    for tree in parsed_tree:
        contain = contain or has_label(tree, label_set)
    return contain

#checks in a parsed_tree has a value in label-set
def has_string(parsed_tree, string_set):
    if isinstance(parsed_tree, str):
        return parsed_tree in string_set
    contain = False
    for tree in parsed_tree:
        contain = contain or has_string(tree, string_set)
    return contain


#Sentence Structure Tree
class SST():
    def __init__(self, label, children):
        self.label = label
        self.children = children

#Sentence Structure Leaf
class SSL():
    def __init__(self, label):
        self.label = label

simple_predicate = SST('ROOT', [SST('S', [SSL('NP'), SSL('VP'), SSL('.')])])

def satisfies_simple_pred(parse_tree):
    return satisfies_structure(parse_tree, simple_predicate)


def satisfies_structure(parsed_tree, structure):
    if isinstance(structure, SSL):
        return parsed_tree.label() == structure.label
    else:
        if parsed_tree.label() != structure.label or len(parsed_tree) != len(structure.children): return False
        for i in range(len(parsed_tree)):
            if satisfies_structure(parsed_tree[i], structure.children[i]) == False:
                return False
        return True

def count_pp(parsed_tree):
    if isinstance(parsed_tree, str):
        return 0
    else:
        sum = 1 if parsed_tree.label() == "PP" else 0
        for i in range(len(parsed_tree)):
            sum += count_pp(parsed_tree[i])
        return sum
            
