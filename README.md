# Raspored Bot

Raspored Bot prati promjene u dnevnim izmjenama rasporeda sati, na stranicama TSRB-a.
Ovo je stara verzija raspored bota **2.4.1**, te više neće biti održavana.

**U ovoj verziji bota postoje greške koje mogu dovesti zaustavljanja rada.**

Predpostavljam da se radi o činjenici da 4. razredi imaju drugačija slova, na što nisam mislio pri dizajnu.

## Komande iz komandne linije

`list`
- izlistava sve servere u kojima je bot trenutno

`dlist`
- izlistava sve servere iz baze podataka

`debug on`
- uključuje debug mode, odnosno ispisuje kada povlači podatke

`debug off`
- isključuje debug mode

`notify a`
- šalje zadnju izmjenu svim konfiguriranim serverima iz A smjene

`notify b`
- šalje zadnju izmjenu svim konfiguriranim serverima iz B smjene

`help`
- izlistava listu svih komandi


## Komande na discordu

`.raspored`
- ispisuje posljednje izmjene za konfigurirani razred

`.raspored <ime razreda>`
- ispisuje posljednje izmjene za navedeni razred

`.ver`
- ispisuje verziju bota

`.help`
- ispisuje listu komandi

`.conf kanal`
- postavlja kanal u kojem je poruka poslana u bazu

`.conf raz <ime razreda>`
- postavlja navedeni razred u bazu

`.conf status`
- ispisuje trenutnu konfiguraciju

`.conf obrisi`
- izbriši sve vrijednosti iz baze

**Napomena:** ukoliko razred i kanal nisu odabrani bot neće sam slati izmjene


