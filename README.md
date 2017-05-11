# Eestikeelse teksti lihtsustamise veebirakendus
Rakenduse kasutamiseks on vaja sagedusloendit, põhisõnavara sõnastiku märksõnaloendit ja võõrsõnade leksikoni märksõnaloendit kui ka tähendussõnastikku.

Töötlemata kujul on vaja loendid lisada "python" kasuta nimedega:
 * `freq_list_raw.txt` - sagedusloendi puhul;
 * `basic_raw.txt` - põhisõnavara sõnastiku märksõnaloendi puhul;
 * `foreign_meaning.txt` - võõrsõnade leksikoni tähendustega sõnastiku puhul;
 * `foreign_keywords.txt` - võõrsõnade leksikoni märksõnaloendi puhul.
 
 Töötlemata kujul on võimalik leida neid ressursse võimalik leida järgmistelt lehekülgedelt.
 * Sagedusloend - [Eesti Keeleressursside Keskus](https://keeleressursid.ee/et/keeleressursid-cl-ut/ressursid/83-article/clutee-lehed/256-sagedusloendid)
 * Põhisõnavara sõnastik - [Eesti keele instituut](https://www.eki.ee/litsents/)
 * Võõrsõnade leksikon - [Eesti keele instituut](https://www.eki.ee/litsents/)
 
 Lisaks on "python"-i kausta vaja lisada EstNLTK <i>word2vec</i>'i mudel nimega `lemmas.cbow.s200.w2v.bin`, mis on kättesaadav aadressil (EstNLTK word2vec-models)[https://github.com/estnltk/word2vec-models/blob/master/README.md] 
 
