#!/usr/bin/env python
# -*- coding: utf-8 -*-
import estnltk
import dictionaries
import sys
from estnltk.wordnet import wn
from estnltk import Disambiguator
from estnltk import synthesize
from estnltk.names import TEXT, ANALYSIS, ROOT, POSTAG, FORM, LEMMA, ROOT_TOKENS
import urllib.request
import urllib.parse
import math

# sageduse alampiirid
WORD_SIMILARITY = 0.45
MIN_SIMILARITY = 0.2

# Sõnaliigid, mille puhul sõna edasi analüüsitakse
wn_pos = {"A": wn.ADJ, "C": wn.ADJ, "U": wn.ADJ, "D": wn.ADV,
          "S": wn.NOUN, "V": wn.VERB, "I": wn.NOUN, "K": wn.ADV}

# lõpptulemus
final_result = []

# Sagedusloend
freq_dict = dictionaries.get_freq_dict("python/freq_list_processed.txt")
# Võõrsõnade leksikoni loend
foreign_dict = dictionaries.get_foreign_dict("python/foreign_processed.txt")
# Põhisõnavara loend
basic_dict = dictionaries.get_basic_list("python/basic_processed.txt")

# Sünteesitud lemmad, kus sõna muutevormile vastab tema lemma
synthesized_lemmas = {}

# Algse sõna lemmale vastab tema sünonüümide lemmad
word_lemma_dict = {}

# Sõna sarnasuste sõnastik, et samade sõnade puhul ei teeks korduvalt päringut
word_similarity_dict = {}


# Teeme Lemma objektide järjendist lemma sõnede järjendi
def lemmas_to_list(lemmas_list):
    if len(lemmas_list) > 0:
        if isinstance(lemmas_list[0], estnltk.wordnet.wn.Lemma):
            return [x.name for x in lemmas_list]
    return lemmas_list


# Leiame parima sünonüümi lemmade järjendi põhjal
def get_best_synonym(original_word, lemmas_list):
    lemmas_list = lemmas_to_list(lemmas_list)
    best_count = 0
    best_word = None
    for temp_word in lemmas_list:
        word_sim = get_word_similarity(original_word, temp_word)
        temp_count = estimate_correctness(word_sim, freq_dict.get(temp_word, 1))
        if temp_count > best_count:
            best_count = temp_count
            best_word = temp_word
    return best_word


# Leiame algsele sõnale eelneva sõna, kui see leidub
def get_prev_word(i, original):
    if i > 0:
        return original[i - 1][ANALYSIS][0]
    return None


# Leiame algsele sõnale järgneva sõna, kui see leidub
def get_next_word(i, original):
    if i + 1 < len(original):
        return original[i + 1][ANALYSIS][0]
    return None


# Sünohulkade järjestamine sarnasuse alusel
def get_best_syn_set_from_prev_and_next(prev_word, next_word, syn_sets):
    # Kui nii eelnev kui ka järgnev sõna puudub, tagastame algse väärtuse
    if prev_word is None and next_word is None:
        return syn_sets

    all_sets = {}
    for syn_set in syn_sets:
        # Iga sünohulga jaoks leiame keskmise sarnasuse algsõnale järgmise ja eelneva lemmapõhjal
        similarity_sum = 0
        for word_lemma in lemmas_to_list(syn_set.lemmas()):
            if prev_word is not None:
                similarity_sum += get_word_similarity(prev_word[LEMMA], word_lemma, default=0)
            if next_word is not None:
                similarity_sum += get_word_similarity(word_lemma, next_word[LEMMA], default=0)

        # Kui järgmine või eelnev sõna puudub, siis ei jaga kaheks keskmis sarnasust kahega
        if prev_word is not None and next_word is not None:
            current_avg = similarity_sum / (2 * len(syn_set.lemmas()))
        else:
            current_avg = similarity_sum / len(syn_set.lemmas())

        all_sets[syn_set] = current_avg
    # Sorteerime keskmise sarnasuse põhjal ja tagastame 3 parimat
    return sorted(all_sets, key=all_sets.get, reverse=True)[:3]


# Leiame asenduse sobivuse hinnangu
def estimate_correctness(similarity, frequency):
    # Kui sarnasus on 1, siis on tegemist sama sõnaga, seega tagastame 0
    if similarity == 1:
        return 0
    # Sarnasuse hindamiseks kasutame kuupjuur(sagedus)*sarnasus/ruutjuur(1-sarnasus)
    return (frequency ** (1. / 3.) * similarity) / math.sqrt(1 - similarity)


# Leiame parima täissünonüümi
def get_best_full_synonym(lemmas_list):
    best_count = 0
    best_word = None
    # Vaatame kõik lemmad läbi
    for word_lemma in lemmas_list:
        word_sim = get_word_similarity(word[LEMMA], word_lemma)
        # esinemissageduse ja sarnasuse põhjal arvutame hinnangu valemiga sagsedus * sarnasus^2
        temp_count = freq_dict.get(word_lemma, 1) * word_sim ** 2
        if temp_count > best_count:
            best_count = temp_count
            best_word = word_lemma
    return best_word


# Teksti ühestamine
def explicit_disamb(text_input):
    disamb = Disambiguator()
    text_analysis = disamb.disambiguate([text_input])
    list_of_words = []
    for w in text_analysis:
        for word in w.words:
            list_of_words.append(word)
    # tagastame järjendi, kus on iga sõna jaoks ka tehtud morfoloogiline analüüs
    return list_of_words


# Kontroll, kas sõna vajab lihtsustamist
def needs_replacing(lookup_word):
    # Kui on tegemist võõrsõnaga, siis üritame lihtsustada
    if lookup_word in foreign_dict:
        return True
    # Kui esinemissagedus on väiksem, kui lävend, siis üritame lihtsustada
    return freq_dict.get(lookup_word, 1) < threshold


# Uuendame sõnastikku, et saaks
def update_word_lemma_dict(original_lemma, lemma_list):
    word_lemmas = []
    for word_lemma in lemma_list:
        # Algset sõna ei ole mõttet vaadata, sest iseendaga asendamine ei anna midagi
        if original_lemma != word_lemma.name:
            word_lemmas.append(word_lemma.name)
    # Algse sõna lemmale vastab tema sünonüümide lemmad
    word_lemma_dict[original_lemma] = word_lemmas


# Leiame parima ülemmõiste
def get_best_hypernym(syn_set, best_synonym):
    # Kontrollime eelnevalt, kas parim täissünonüüm vajab üldse lihtsustamist
    if needs_replacing(best_synonym):
        # Leiame kõik ülemmõiste sünohulgad ja järjestame need sarnasuse alusel
        hypernyms = get_best_syn_set_from_prev_and_next(prev_word, next_word, syn_set.hypernyms())
        hypernym_lemmas = []

        # Lisame kõik sünohulga lemmad ühisesse järjendisse
        for hypernym in hypernyms:
            hypernym_lemmas.extend(hypernym.lemmas())

        # Kui ülemmõistete seas leidus midagi, leiame parima ülemmõiste
        if len(hypernym_lemmas) > 0:
            lemma = get_best_synonym(word[LEMMA], hypernym_lemmas)
            return lemma

    # Kui ülemmõistet ei leidnud, tagastame täissünonüümi, kui see on sagedasem, kui algne lemma
    if is_more_frequent(best_synonym, word[LEMMA]):
        return best_synonym


# Väljundi koostamine, säilitame suured tähed nii nagu algses tekstis esinesid,
# kirjavahemärkide puhul lisatakse koma ainult pärast sõne
def format_output(word_list, original_text):
    output = ""
    for k in range(0, len(original_text)):
        if k + 1 < len(original_text):
            next_word_analysis = original_text[k + 1]["analysis"][0]
        else:
            next_word_analysis = None

        is_capital = original_text[k]["text"].istitle()
        output += get_word_for_result(word_list[k], is_capital)

        if not (next_word_analysis is None or next_word_analysis[POSTAG] == "Z"):
            output += " "
    return output


# Tagastame lõpptulemuse jaoks ühe konkreetse asenduse, kui leiti mitu asendust, siis ühendame nad üheks üksuseks
def get_word_for_result(word, is_capital):
    if isinstance(word, list):
        result = "${"
        if is_capital:
            result += ",".join(word).title()
        else:
            result += ",".join(word)
        result += "}$"
        return result
    else:
        if is_capital:
            return word.title()
        return word


# Leiame word2vec abil kahe sõna vahelise sarnasusse
def get_word_similarity(word1, word2, default=MIN_SIMILARITY):
    word_tuple = (word1, word2)
    # Kui sellisele paarile on varem juba sarnasus leitud, siis tagastame salvestatud väärtuse
    if word_tuple in word_similarity_dict:
        return word_similarity_dict[word_tuple]

    full_path = "http://" + hostname + "/similarity?word1=" + urllib.parse.quote(word1.encode('utf-8')) + \
                "&word2=" + urllib.parse.quote(word2.encode('utf-8'))
    response = urllib.request.urlopen(full_path)
    value = response.read().decode('utf-8')

    # Kui vähemalt ühte sõna word2vec'is ei leidu, tagastame vaikeväärtuse
    if value == "NaN":
        value = default
    else:
        value = float(value)
    # Salvestame leitud vaikeväärtuse sõnastikku, et korduvate arvutuste käigus ei tehaks päringut mitu korda
    word_similarity_dict[word_tuple] = value
    return value


# Leiame parima osa- või lähisünonüümi
def get_best_near_synonym(original_word, syn):
    near_synonyms = []
    for near_syn in syn.get_related_synsets("near_synonym"):
        near_lemmas = get_best_synonym(original_word, near_syn.lemmas())
        if near_lemmas is not None:
            near_synonyms.append(near_lemmas)
    best_word_lemma = get_best_synonym(original_word, near_synonyms)
    if best_word_lemma is not None:
        return best_word_lemma


def order_by_similarity(processed_list, original_word_lemma):
    if len(processed_list) < 2:
        return processed_list

    temp_dict = {}
    for temp_word in processed_list:
        temp_dict[temp_word] = get_word_similarity(original_word_lemma, estnltk.Text(temp_word).lemmas[0])
    return sorted(temp_dict, key=temp_dict.get, reverse=True)


def get_most_similar(word_list, original_lemma):
    if len(word_list) == 1:
        return word_list[0]
    # word2vec ei arvesta käändes olevaid sõnu, seega ei ole see optimaalne
    best_similarity = -1
    best_lemma = None
    for word in word_list:
        word_analysis = estnltk.Text(word).analysis[0][0]
        similarity = get_word_similarity(original_lemma, word_analysis[LEMMA], default=0)
        if similarity > best_similarity:
            best_lemma = word
            best_similarity = similarity
    return best_lemma


def synthesize_lemma(word_to_synthezise, original):
    synthesized = synthesize(word_to_synthezise, original[FORM])
    # milleks see vajalik oli
    # if synthesized is None:
    #     synthesized = word_to_synthezise

    if synthesized not in replacement_list and word_to_synthezise != original[LEMMA]:
        # veendume, et me ei asenda halvema variandiga
        return synthesized


def needs_further_simplification(replacement_list):
    if len(replacement_list) == 0:
        return True
    for synthesized_lemma in replacement_list:
        lemma = synthesized_lemmas[synthesized_lemma]
        if lemma in basic_dict and get_word_similarity(lemma, word[LEMMA]) > 0.75 * threshold:
            return False
    return True


def is_more_frequent(word1, word2):
    if word1 is None:
        return False
    if not is_foreign(word1) and is_foreign(word2):
        return True
    if is_foreign(word1) and not is_foreign(word2):
        return False

    freq1 = freq_dict.get(word1, 1)
    freq2 = freq_dict.get(word2, 1)

    if freq1 > 1 and freq2 == 1:
        return True

    return freq1 - freq2 > 10


def is_foreign(lookup_word):
    if lookup_word in foreign_dict:
        return True
    return False


def find_replacement(replace_syn_set, replacement_list):
    # Lisame täissünonüümide lemmad sõnastikku, et ei peaks mitu korda sama asja arvutama
    update_word_lemma_dict(word[LEMMA], replace_syn_set.lemmas())
    # Leiame parima täissünonüümi
    best_syn = get_best_full_synonym(word_lemma_dict[word[LEMMA]])
    # Leiame parima ülemmõiste
    replaced_word = get_best_hypernym(replace_syn_set, best_syn)
    # Kui nende seas ei olnud piisavalt lihtsat lemmat või oli sarnasus alampiirist väiksem, uurime osa- või lähisünonüümi
    if replaced_word is None or get_word_similarity(word[LEMMA], replaced_word) < WORD_SIMILARITY:
        # Leiame parima osa- ja lähisünonüümi
        best_near_synonym = get_best_near_synonym(word[LEMMA], replace_syn_set)
        # Kontrollime kas osa- või lähisünonüüm leidus ja kas selle esinemissagedus on suurem, kui algse sõna esinemissagedus
        if best_near_synonym is not None and is_more_frequent(best_near_synonym, word[LEMMA]):
            # Lisame osa- või lähisünonüümi lõpptulemusse
            add_lemma_to_result(best_near_synonym, replacement_list, similarity=WORD_SIMILARITY * 0.75)

    # Kontrollime, kas leitud ülemmõiste on suurema esinemissagedusega
    if is_more_frequent(replaced_word, word[LEMMA]):
        # Lisame sünonüümi lõpptulemusse
        add_lemma_to_result(replaced_word, replacement_list, similarity=WORD_SIMILARITY * 0.65)
    # Kontrollime, kas leitud täissünonüüm on suurema esinemissagedusega
    if is_more_frequent(best_syn, word[LEMMA]):
        add_lemma_to_result(best_syn, replacement_list)


# Lemma lõpptulemusse lisamine
def add_lemma_to_result(word_to_add, replacement_list, similarity=MIN_SIMILARITY):
    # Kui sarnasus on alampiiris väiksem jätame sõna lõpptulemusse lisamata
    if get_word_similarity(word_to_add, word[LEMMA], similarity) < similarity:
        return

    # Sünteesime lemmale vastava muutevormi(d)
    lemma_synthesized = synthesize(word_to_add, word[FORM])
    # Kui süntees tagastas mitu võimalikku muutevormi, lisame kõik lõpptulemusse
    for synthesized in lemma_synthesized:
        synthesized_lemmas[synthesized] = word_to_add
        print(synthesized_lemmas)
        replacement_list.append(synthesized)


if __name__ == '__main__':
    # Tekst mida hakkame lihtsustama
    user_input = sys.argv[1]
    # Aadres, kus saab teha word2vec päringuid
    hostname = sys.argv[2]
    # Lävend
    threshold = int(sys.argv[3])

    # Teksti ühesamine ning morfoloogiline analüüs
    original = explicit_disamb(user_input)

    # Vaatame kõik sisendi sõnad läbi
    for i in range(0, len(original)):
        # Uuritav sõna
        original_word = original[i]
        # Uuritavale sõna eelnev sõna
        prev_word = get_prev_word(i, original)
        # Uuritavale sõnale järgnev sõna
        next_word = get_next_word(i, original)

        # Analüüsime uuritavat sõna, analüüsi tulemusena võib saada mitu elementi
        word_analysis = original_word[ANALYSIS]
        # Järjend sobivate asenduste jaoks
        replacement_list = []

        # Uurime kõiki analüüsitud sõnu
        for word in word_analysis:
            # Kontrollime kas sõna on võõrsõna ja kas võõrsõnale leidub omasõna
            if is_foreign(word[LEMMA]) and foreign_dict[word[LEMMA]] is not None:
                # Lisame lemma tulemusse, sageduse alampiir on 0, sest tegemist on usaldusväärse asendusega
                add_lemma_to_result(foreign_dict[word[LEMMA]], replacement_list, similarity=0)

            # Sõnaliik
            tag = word[POSTAG]
            # Kontrollime, kas sõnaliik on sobiv
            if tag in wn_pos:
                # Kontrollime, kas sõna lemma vajab lihtsustamist
                if needs_replacing(word[LEMMA]):
                    # Leiame täissünonüümi hulga
                    syn_sets = wn.synsets(word[LEMMA], pos=wn_pos[tag])
                    # Kui täissünonüüme ei ole, pole ei saa ka neid analüüsida
                    if len(syn_sets) > 0:
                        # Järjestame sünohulgad sarnasuse alusel
                        ordered_synsets = get_best_syn_set_from_prev_and_next(prev_word, next_word, syn_sets)
                        # Vaatame kõik sünohulgad järjestatud sünohulkade seast läbi
                        for syn_set in ordered_synsets:
                            # Kontrollime, kas oleme leidnud juba sobiva asenduse, kui ei ole, üritame leida
                            if needs_further_simplification(replacement_list):
                                # Otsime lihtsamat lemmat
                                find_replacement(syn_set, replacement_list)
                # Kui oleme leidnud sobiva sõna, siis edasi enam ei analüüsi.
                else:
                    break

        # Kui asendusi leiti, lisame lõpptulemusse, kus asendused on järjestatud sarnasuse alusel
        if len(replacement_list) > 0:
            final_result.append(order_by_similarity(replacement_list, word_analysis[0][LEMMA]))

        # Kui asendusi ei leitud, lisame algse sõna muutmata kujul lõpptulemusse
        if len(final_result) <= i:
            final_result.append(original_word["text"])

    print(format_output(final_result, original))
