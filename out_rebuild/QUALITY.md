# Quality report: suspect duplicate entries

Stage 1. Gate: warn only.

> Stage 1 reproduces the original pipeline including its known
> flaws, so a long list here is the expected result, not a
> regression. The gate is enforced from stage 2.

**1109 suspects**: diacritic 100, inflected 345, relemmatize 664

| kind | entry | rank | duplicate of | rank | detail |
|---|---|---:|---|---:|---|
| inflected | `coisa` | 44 | `coiso` | 9391 | coisa is a regular inflection of coiso |
| diacritic | `quê` | 109 | `que` | 3 | both fold to 'que' |
| diacritic | `porquê` | 227 | `porque` | 51 | both fold to 'porque' |
| relemmatize | `acha` | 244 | `achar` | 65 | acha lemmatizes to achar |
| relemmatize | `obrigado` | 247 | `obrigar` | 113 | obrigado lemmatizes to obrigar |
| inflected | `porta` | 282 | `porto` | 2149 | porta is a regular inflection of porto |
| diacritic | `pôr` | 294 | `por` | 22 | both fold to 'por' |
| inflected | `cima` | 316 | `cimo` | 5111 | cima is a regular inflection of cimo |
| inflected | `eis` | 347 | `el` | 2589 | eis is a regular inflection of el |
| inflected | `filha` | 360 | `filho` | 159 | filha is a regular inflection of filho |
| inflected | `umas` | 402 | `uma` | 15 | umas is a regular inflection of uma |
| inflected | `tuas` | 468 | `tua` | 86 | tuas is a regular inflection of tua |
| inflected | `pais` | 480 | `pai` | 104 | pais is a regular inflection of pai |
| diacritic | `país` | 533 | `pais` | 480 | both fold to 'pais' |
| relemmatize | `pelo` | 539 | `pelar` | 81 | pelo lemmatizes to pelar |
| inflected | `comida` | 554 | `comido` | 3733 | comida is a regular inflection of comido |
| inflected | `bola` | 557 | `bolo` | 1256 | bola is a regular inflection of bolo |
| inflected | `certa` | 580 | `certo` | 139 | certa is a regular inflection of certo |
| relemmatize | `deve` | 614 | `dever` | 57 | deve lemmatizes to dever |
| relemmatize | `tinha` | 616 | `ter` | 9 | tinha lemmatizes to ter |
| relemmatize | `vê` | 618 | `ver` | 38 | vê lemmatizes to ver |
| relemmatize | `visto` | 627 | `ver` | 38 | visto lemmatizes to ver |
| relemmatize | `chamado` | 659 | `chamar` | 153 | chamado lemmatizes to chamar |
| relemmatize | `pergunta` | 660 | `perguntar` | 205 | pergunta lemmatizes to perguntar |
| inflected | `escolha` | 666 | `escolho` | 4625 | escolha is a regular inflection of escolho |
| inflected | `mesa` | 707 | `mês` | 340 | mesa is a regular inflection of mês |
| diacritic | `á` | 736 | `à` | 45 | both fold to 'a' |
| diacritic | `ai` | 738 | `aí` | 173 | both fold to 'ai' |
| inflected | `tira` | 742 | `tiro` | 640 | tira is a regular inflection of tiro |
| inflected | `puta` | 751 | `puto` | 1811 | puta is a regular inflection of puto |
| relemmatize | `namorado` | 797 | `namorar` | 775 | namorado lemmatizes to namorar |
| relemmatize | `era` | 828 | `ser` | 2 | era lemmatizes to ser |
| inflected | `surpresa` | 852 | `surpreso` | 5234 | surpresa is a regular inflection of surpreso |
| inflected | `esquerda` | 890 | `esquerdo` | 2664 | esquerda is a regular inflection of esquerdo |
| inflected | `costas` | 906 | `costa` | 1725 | costas is a regular inflection of costa |
| inflected | `senhora` | 909 | `senhor` | 107 | senhora is a regular inflection of senhor |
| relemmatize | `senhora` | 909 | `senhor` | 107 | senhora lemmatizes to senhor |
| relemmatize | `dado` | 911 | `dar` | 68 | dado lemmatizes to dar |
| diacritic | `vós` | 925 | `vos` | 478 | both fold to 'vos' |
| relemmatize | `passado` | 956 | `passar` | 82 | passado lemmatizes to passar |
| relemmatize | `errado` | 960 | `errar` | 516 | errado lemmatizes to errar |
| inflected | `cerca` | 963 | `cerco` | 6355 | cerca is a regular inflection of cerco |
| inflected | `pedra` | 976 | `pedro` | 3680 | pedra is a regular inflection of pedro |
| inflected | `testemunha` | 1009 | `testemunho` | 3555 | testemunha is a regular inflection of testemunho |
| diacritic | `näo` | 1031 | `não` | 4 | both fold to 'nao' |
| relemmatize | `rapariga` | 1054 | `rapaz` | 171 | rapariga lemmatizes to rapaz |
| relemmatize | `percebe` | 1058 | `perceber` | 238 | percebe lemmatizes to perceber |
| relemmatize | `foda-se` | 1060 | `foda` | 2610 | foda-se lemmatizes to foda |
| relemmatize | `deste` | 1092 | `dar` | 68 | deste lemmatizes to dar |
| inflected | `conta` | 1107 | `conto` | 1638 | conta is a regular inflection of conto |
| relemmatize | `conta` | 1107 | `contar` | 161 | conta lemmatizes to contar |
| inflected | `carrinha` | 1151 | `carrinho` | 4073 | carrinha is a regular inflection of carrinho |
| inflected | `corrida` | 1180 | `corrido` | 5069 | corrida is a regular inflection of corrido |
| relemmatize | `ela` | 1207 | `ele` | 13 | ela lemmatizes to ele |
| relemmatize | `chama` | 1222 | `chamar` | 153 | chama lemmatizes to chamar |
| inflected | `troca` | 1243 | `troco` | 2750 | troca is a regular inflection of troco |
| relemmatize | `unido` | 1244 | `unir` | 2349 | unido lemmatizes to unir |
| inflected | `fala` | 1254 | `falo` | 1001 | fala is a regular inflection of falo |
| relemmatize | `fala` | 1254 | `falar` | 55 | fala lemmatizes to falar |
| relemmatize | `maldito` | 1268 | `maldizer` | 1192 | maldito lemmatizes to maldizer |
| inflected | `dessas` | 1273 | `dessa` | 833 | dessas is a regular inflection of dessa |
| relemmatize | `preocupado` | 1275 | `preocupar` | 253 | preocupado lemmatizes to preocupar |
| inflected | `calças` | 1298 | `calça` | 7052 | calças is a regular inflection of calça |
| relemmatize | `milhar` | 1328 | `mil` | 455 | milhar lemmatizes to mil |
| relemmatize | `má` | 1371 | `mau` | 281 | má lemmatizes to mau |
| inflected | `vê-la` | 1374 | `vê-lo` | 868 | vê-la is a regular inflection of vê-lo |
| inflected | `desses` | 1396 | `desse` | 875 | desses is a regular inflection of desse |
| inflected | `banda` | 1400 | `bando` | 2016 | banda is a regular inflection of bando |
| relemmatize | `estado` | 1409 | `estar` | 6 | estado lemmatizes to estar |
| inflected | `óptima` | 1413 | `óptimo` | 328 | óptima is a regular inflection of óptimo |
| relemmatize | `óptima` | 1413 | `óptimo` | 328 | óptima lemmatizes to óptimo |
| inflected | `partida` | 1442 | `partido` | 1329 | partida is a regular inflection of partido |
| relemmatize | `fechado` | 1444 | `fechar` | 486 | fechado lemmatizes to fechar |
| relemmatize | `preparado` | 1452 | `preparar` | 387 | preparado lemmatizes to preparar |
| relemmatize | `ferido` | 1453 | `ferir` | 1239 | ferido lemmatizes to ferir |
| relemmatize | `ouvido` | 1472 | `ouvir` | 84 | ouvido lemmatizes to ouvir |
| relemmatize | `casado` | 1530 | `casar` | 419 | casado lemmatizes to casar |
| relemmatize | `guarda` | 1551 | `guardar` | 454 | guarda lemmatizes to guardar |
| relemmatize | `empregado` | 1570 | `empregar` | 2284 | empregado lemmatizes to empregar |
| inflected | `merdas` | 1585 | `merda` | 199 | merdas is a regular inflection of merda |
| inflected | `bem-vindos` | 1613 | `bem-vindo` | 1149 | bem-vindos is a regular inflection of bem-vindo |
| relemmatize | `bem-vindos` | 1613 | `bem-vindo` | 1149 | bem-vindos lemmatizes to bem-vindo |
| relemmatize | `atrasado` | 1632 | `atrasar` | 921 | atrasado lemmatizes to atrasar |
| inflected | `tretas` | 1651 | `treta` | 1468 | tretas is a regular inflection of treta |
| relemmatize | `morado` | 1697 | `morar` | 1055 | morado lemmatizes to morar |
| diacritic | `ó` | 1702 | `o` | 1 | both fold to 'o' |
| inflected | `ás` | 1703 | `á` | 736 | ás is a regular inflection of á |
| inflected | `revista` | 1736 | `revisto` | 6389 | revista is a regular inflection of revisto |
| diacritic | `mama` | 1742 | `mamã` | 773 | both fold to 'mama' |
| inflected | `câmaras` | 1755 | `câmara` | 827 | câmaras is a regular inflection of câmara |
| inflected | `carga` | 1757 | `cargo` | 2492 | carga is a regular inflection of cargo |
| diacritic | `àquele` | 1771 | `aquele` | 148 | both fold to 'aquele' |
| relemmatize | `convidado` | 1773 | `convidar` | 721 | convidado lemmatizes to convidar |
| relemmatize | `nota` | 1780 | `notar` | 1130 | nota lemmatizes to notar |
| inflected | `bolsa` | 1789 | `bolso` | 1568 | bolsa is a regular inflection of bolso |
| relemmatize | `cansado` | 1798 | `cansar` | 1227 | cansado lemmatizes to cansar |
| inflected | `chamada` | 1799 | `chamado` | 659 | chamada is a regular inflection of chamado |
| relemmatize | `chamada` | 1799 | `chamado` | 659 | chamada lemmatizes to chamado |
| inflected | `fila` | 1812 | `filo` | 3599 | fila is a regular inflection of filo |
| inflected | `vira` | 1840 | `viro` | 8340 | vira is a regular inflection of viro |
| inflected | `ponha` | 1848 | `ponho` | 3727 | ponha is a regular inflection of ponho |
| relemmatize | `sentado` | 1868 | `sentar` | 290 | sentado lemmatizes to sentar |
| inflected | `ponta` | 1935 | `ponto` | 500 | ponta is a regular inflection of ponto |
| relemmatize | `peça` | 1950 | `pedir` | 160 | peça lemmatizes to pedir |
| relemmatize | `compra` | 1951 | `comprar` | 332 | compra lemmatizes to comprar |
| inflected | `queixa` | 1952 | `queixo` | 4184 | queixa is a regular inflection of queixo |
| inflected | `bebida` | 1961 | `bebido` | 859 | bebida is a regular inflection of bebido |
| relemmatize | `bebida` | 1961 | `bebido` | 859 | bebida lemmatizes to bebido |
| inflected | `carteira` | 1975 | `carteiro` | 6283 | carteira is a regular inflection of carteiro |
| relemmatize | `criado` | 1978 | `criar` | 494 | criado lemmatizes to criar |
| relemmatize | `deixa` | 1983 | `deixar` | 59 | deixa lemmatizes to deixar |
| relemmatize | `zangado` | 2027 | `zangar` | 1424 | zangado lemmatizes to zangar |
| relemmatize | `ligado` | 2030 | `ligar` | 195 | ligado lemmatizes to ligar |
| relemmatize | `for` | 2036 | `ser` | 2 | for lemmatizes to ser |
| relemmatize | `assustado` | 2039 | `assustar` | 689 | assustado lemmatizes to assustar |
| relemmatize | `proposto` | 2050 | `propor` | 2314 | proposto lemmatizes to propor |
| relemmatize | `engraçado` | 2067 | `engraçar` | 914 | engraçado lemmatizes to engraçar |
| inflected | `acções` | 2096 | `acção` | 1277 | acções is a regular inflection of acção |
| relemmatize | `acções` | 2096 | `acção` | 1277 | acções lemmatizes to acção |
| inflected | `marca` | 2107 | `marco` | 2540 | marca is a regular inflection of marco |
| relemmatize | `marca` | 2107 | `marcar` | 740 | marca lemmatizes to marcar |
| relemmatize | `armado` | 2124 | `armar` | 1295 | armado lemmatizes to armar |
| relemmatize | `interessado` | 2129 | `interessar` | 466 | interessado lemmatizes to interessar |
| relemmatize | `apaixonado` | 2164 | `apaixonar` | 1118 | apaixonado lemmatizes to apaixonar |
| relemmatize | `vestido` | 2166 | `vestir` | 559 | vestido lemmatizes to vestir |
| diacritic | `idéia` | 2223 | `ideia` | 234 | both fold to 'ideia' |
| inflected | `junta` | 2229 | `junto` | 318 | junta is a regular inflection of junto |
| relemmatize | `junta` | 2229 | `juntar` | 643 | junta lemmatizes to juntar |
| inflected | `traseira` | 2238 | `traseiro` | 2032 | traseira is a regular inflection of traseiro |
| relemmatize | `traseira` | 2238 | `traseiro` | 2032 | traseira lemmatizes to traseiro |
| inflected | `china` | 2239 | `chino` | 9156 | china is a regular inflection of chino |
| inflected | `memórias` | 2279 | `memória` | 1229 | memórias is a regular inflection of memória |
| relemmatize | `privado` | 2300 | `privar` | 1913 | privado lemmatizes to privar |
| inflected | `despedida` | 2330 | `despedido` | 9151 | despedida is a regular inflection of despedido |
| relemmatize | `seguido` | 2346 | `seguir` | 257 | seguido lemmatizes to seguir |
| inflected | `moda` | 2391 | `modo` | 749 | moda is a regular inflection of modo |
| relemmatize | `comprimido` | 2392 | `comprimir` | 4696 | comprimido lemmatizes to comprimir |
| inflected | `boneca` | 2417 | `boneco` | 3334 | boneca is a regular inflection of boneco |
| inflected | `bem-vinda` | 2432 | `bem-vindo` | 1149 | bem-vinda is a regular inflection of bem-vindo |
| relemmatize | `bem-vinda` | 2432 | `bem-vindo` | 1149 | bem-vinda lemmatizes to bem-vindo |
| relemmatize | `apanhado` | 2438 | `apanhar` | 223 | apanhado lemmatizes to apanhar |
| inflected | `noutra` | 2448 | `noutro` | 1962 | noutra is a regular inflection of noutro |
| relemmatize | `chateado` | 2493 | `chatear` | 1093 | chateado lemmatizes to chatear |
| inflected | `tê-la` | 2508 | `tê-lo` | 1552 | tê-la is a regular inflection of tê-lo |
| relemmatize | `leva` | 2532 | `levar` | 130 | leva lemmatizes to levar |
| relemmatize | `encontrado` | 2561 | `encontrar` | 101 | encontrado lemmatizes to encontrar |
| relemmatize | `usado` | 2578 | `usar` | 196 | usado lemmatizes to usar |
| relemmatize | `culpado` | 2583 | `culpar` | 844 | culpado lemmatizes to culpar |
| relemmatize | `bota` | 2592 | `botar` | 4630 | bota lemmatizes to botar |
| inflected | `chegada` | 2594 | `chegado` | 6021 | chegada is a regular inflection of chegado |
| relemmatize | `roubado` | 2596 | `roubar` | 382 | roubado lemmatizes to roubar |
| inflected | `gaja` | 2618 | `gajo` | 669 | gaja is a regular inflection of gajo |
| relemmatize | `vindo` | 2624 | `vir` | 61 | vindo lemmatizes to vir |
| relemmatize | `parado` | 2630 | `parar` | 158 | parado lemmatizes to parar |
| relemmatize | `destruído` | 2636 | `destruir` | 530 | destruído lemmatizes to destruir |
| inflected | `milha` | 2637 | `milho` | 3784 | milha is a regular inflection of milho |
| relemmatize | `milha` | 2637 | `milhar` | 1328 | milha lemmatizes to milhar |
| relemmatize | `asa` | 2638 | `asar` | 4314 | asa lemmatizes to asar |
| relemmatize | `enganado` | 2653 | `enganar` | 609 | enganado lemmatizes to enganar |
| inflected | `vê-los` | 2657 | `vê-lo` | 868 | vê-los is a regular inflection of vê-lo |
| inflected | `filhas` | 2670 | `filho` | 159 | filhas is a regular inflection of filho |
| relemmatize | `calado` | 2674 | `calar` | 416 | calado lemmatizes to calar |
| relemmatize | `divertido` | 2690 | `divertir` | 433 | divertido lemmatizes to divertir |
| inflected | `pasta` | 2694 | `pasto` | 9858 | pasta is a regular inflection of pasto |
| inflected | `caos` | 2708 | `cao` | 8967 | caos is a regular inflection of cao |
| relemmatize | `complicado` | 2709 | `complicar` | 1418 | complicado lemmatizes to complicar |
| inflected | `prata` | 2723 | `prato` | 1871 | prata is a regular inflection of prato |
| inflected | `feita` | 2731 | `feito` | 299 | feita is a regular inflection of feito |
| relemmatize | `feita` | 2731 | `feito` | 299 | feita lemmatizes to feito |
| inflected | `passa` | 2754 | `passo` | 741 | passa is a regular inflection of passo |
| relemmatize | `passa` | 2754 | `passar` | 82 | passa lemmatizes to passar |
| relemmatize | `separado` | 2787 | `separar` | 1159 | separado lemmatizes to separar |
| relemmatize | `preferido` | 2802 | `preferir` | 585 | preferido lemmatizes to preferir |
| relemmatize | `estai` | 2813 | `estar` | 6 | estai lemmatizes to estar |
| inflected | `munições` | 2818 | `munição` | 7295 | munições is a regular inflection of munição |
| relemmatize | `acordado` | 2820 | `acordar` | 456 | acordado lemmatizes to acordar |
| relemmatize | `sincronizado` | 2832 | `sincronizar` | 7556 | sincronizado lemmatizes to sincronizar |
| inflected | `diz-lhes` | 2837 | `diz-lhe` | 1183 | diz-lhes is a regular inflection of diz-lhe |
| relemmatize | `diz-lhes` | 2837 | `diz-lhe` | 1183 | diz-lhes lemmatizes to diz-lhe |
| inflected | `ha` | 2839 | `ho` | 4813 | ha is a regular inflection of ho |
| relemmatize | `assassinado` | 2848 | `assassinar` | 1209 | assassinado lemmatizes to assassinar |
| relemmatize | `roda` | 2876 | `rodar` | 2299 | roda lemmatizes to rodar |
| relemmatize | `volte` | 2881 | `voltar` | 134 | volte lemmatizes to voltar |
| relemmatize | `descoberto` | 2891 | `descobrir` | 258 | descoberto lemmatizes to descobrir |
| relemmatize | `pesado` | 2897 | `pesar` | 1766 | pesado lemmatizes to pesar |
| inflected | `imensa` | 2947 | `imenso` | 1088 | imensa is a regular inflection of imenso |
| relemmatize | `espera` | 2974 | `esperar` | 75 | espera lemmatizes to esperar |
| inflected | `fruta` | 2985 | `fruto` | 3987 | fruta is a regular inflection of fruto |
| relemmatize | `enviado` | 2997 | `enviar` | 422 | enviado lemmatizes to enviar |
| relemmatize | `aposta` | 2998 | `apostar` | 553 | aposta lemmatizes to apostar |
| inflected | `barata` | 3000 | `barato` | 2765 | barata is a regular inflection of barato |
| inflected | `esperta` | 3031 | `esperto` | 1190 | esperta is a regular inflection of esperto |
| diacritic | `ê` | 3048 | `e` | 7 | both fold to 'e' |
| diacritic | `hã` | 3065 | `ha` | 2839 | both fold to 'ha' |
| inflected | `jóias` | 3084 | `jóia` | 5537 | jóias is a regular inflection of jóia |
| relemmatize | `jóias` | 3084 | `jóia` | 5537 | jóias lemmatizes to jóia |
| relemmatize | `ocupado` | 3096 | `ocupar` | 753 | ocupado lemmatizes to ocupar |
| relemmatize | `conversa` | 3148 | `conversar` | 408 | conversa lemmatizes to conversar |
| relemmatize | `ajuda` | 3152 | `ajudar` | 103 | ajuda lemmatizes to ajudar |
| diacritic | `bebê` | 3174 | `bebé` | 442 | both fold to 'bebe' |

_909 further suspects omitted; see the TSV for the full list._
