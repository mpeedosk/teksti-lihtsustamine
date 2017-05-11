import estnltk
from estnltk.wordnet import wn
import dictionaries

allowed_tags = ['A', 'C', 'U', 'D', 'S', 'V', 'I', 'K']


# Kas sõnaliik on lihtsustamiseks sobiv
def is_tag_allowed(analysed_word):
    for tags in analysed_word.postags:
        for tag in tags.split("|"):
            if tag in allowed_tags:
                return True
    return False


# Kas sõnaliigil leidub vajalik sünohulk
def has_relations(synsets):
    for synset in synsets:
        if len(synset.lemmas()) > 1:
            return True
        hyperonym = synset.hypernyms()
        if len(hyperonym) > 0:
            return True
        hyponym = synset.hyponyms()
        if len(hyponym) > 0:
            return True
        near_syn = synset.get_related_synsets("near_synonym")
        if len(near_syn) > 0:
            return True
    return False


# Sagedusloendi töötlemine
def process_frequency_list():
    freq_dict = {}
    print("Töötlen sagedusloendit")
    with open("freq_list_raw.txt", "r", encoding="UTF-8-SIG") as file:
        count = 0
        for line in file:
            if "?" in line:
                continue
            count += 1
            print(count)
            parts = line.strip().split(" ")
            freq = int(parts[0])
            lemma = parts[1]
            word_analysis = estnltk.Text(lemma).tag_analysis()

            synsets = wn.synsets(lemma)
            if is_tag_allowed(word_analysis) and len(synsets) > 0 and has_relations(synsets):
                freq_dict[lemma] = freq

    print("Koostan töödeldud sagedusloendit")
    with open("freq_list_processed.txt", "w", encoding="UTF-8") as file:
        for word in sorted(freq_dict, key=freq_dict.get, reverse=True):
            file.write(word + " " + str(freq_dict[word]) + "\n")
    freq_dict.clear()
    print("Sagedusloend töödeldud")


# Põhisõnavara loendi töötlemine
def process_basic_list():
    basic_list = []
    print("Töötlen põhisõnavara loendit")
    count = 0
    with open("basic_raw.txt", "r", encoding="UTF-8") as file:
        for line in file:
            print(count)
            count += 1
            word = line.strip()
            word_analysis = estnltk.Text(word).tag_analysis()
            synsets = wn.synsets(word)

            if is_tag_allowed(word_analysis) and len(synsets) > 0 and has_relations(synsets):
                basic_list.append(word)

    print("Koostan töödeldud põhisõnavara loendit")
    with open("basic_processed.txt", "w", encoding="UTF-8") as file:
        for word in basic_list:
            file.write(word + "\n")

    basic_list.clear()
    print("Põhisõnavara loend töödeldud")


# Võõrsõnade loendi töötlemine
def process_foreign_list():
    basic = dictionaries.get_basic_list("basic_processed.txt")
    foreign_words = {}

    count = 0
    print("Töötlen selgitustega võõrsõnade loendit")
    with open("foreign_meaning.txt", "r", encoding="UTF-8") as file:
        for line in file:
            print(count)
            count += 1
            parts = line.strip().split("\t")
            word = parts[0]

            if len(parts) > 1:
                definition = parts[1].split("(")[0]
                foreign_words[word] = definition
            else:
                foreign_words[word] = None

    print("Töötlen märksõnadega võõrsõnade loendit")
    with open("foreign_keywords.txt", "r", encoding="UTF-8") as file:
        count = 0
        for word in file:
            print(count)
            count += 1
            word = word.strip()
            if word[0] == "-" or word[-1] == "-":
                continue
            word_analysis = estnltk.Text(word).tag_analysis()
            synsets = wn.synsets(word)

            # filtreerime välja kõik ebavajalikud sõnad
            if is_tag_allowed(word_analysis) and word not in basic and word not in foreign_words and has_relations(
                    synsets):
                foreign_words[word] = None

    print("Koostan töödeldud võõrsõnade loendit")
    with open("foreign_processed.txt", "w", encoding="UTF-8") as file:
        for word in foreign_words:
            if len(word.split(" ")) <= 1:
                if foreign_words[word] is None:
                    file.write(word + "\n")
                else:
                    file.write(word + " " + foreign_words[word] + "\n")

    foreign_words.clear()
    print("Võõrsõnade loend töödeldud")


if __name__ == '__main__':
    # Hoiatus!
    # Kogu töötlemine võib võtta paar tundi.

    print("Laadin kõik sünohulgad mällu...")
    wn.all_synsets()
    print("Laaditud")

    process_frequency_list()
    process_basic_list()
    process_foreign_list()
