# Stage 2 comparison: fixes vs original `out/` and the stage 1 baseline

Stage 1 is a **baseline**, not a target. The original pipeline's
scripts were lost; this is a reconstruction from the README's
description, and the README turned out to be wrong in at least one
place (see Tokenizer below). Divergence is reported, not tuned away.

- Lemmatizer backend: `gated`
- Enclitic splitting: `True`
- simplemma: `2.0.0`
- Corpus: `data/pt.txt.gz` (sample: first 500,000 lines)

## Tokenizer fingerprint

The original README published three totals. They are the only
independent check on the reconstructed tokenizer.

| metric | original | this run | delta | delta % |
|---|---:|---:|---:|---:|
| `lines` | 118,469,705 | 500,000 | -117,969,705 | -99.578% |
| `tokens` | 623,920,347 | 2,657,250 | -621,263,097 | -99.574% |
| `types` | 955,446 | 51,049 | -904,397 | -94.657% |
| `tokens_per_line` | 5.2665 | 5.3145 | +0.048 | +0.911% |

> The original README's step 1 claims *enclitic-cluster splitting*.
> It did not happen: splitting overshoots the published token total
> by 2.04%, while not splitting matches it to 0.0014%, and `out/`
> itself contains unsplit clusters (`vai-te embora`, `vou-me
> embora`, `levem-no` at rank 3492, `hei-de`, `há-de`). The baseline
> therefore does not split; the splitter ships behind a stage 2 flag.

## Reconstructed threshold: collocation share

The README says MWEs were kept at *collocation share >= 5%* without
saying share of what. The denominator changes the outcome by an
order of magnitude, so it was settled against the original's own MWE
counts (179 in the top 5000, 290 in the top 10000), G^2 >= 2500 fixed:

| denominator | share | MWEs kept | in top 5000 | in top 10000 |
|---|---:|---:|---:|---:|
| `min(left, right)` | 0.05 | 36,540 | 3,695 | 8,433 |
| `left` | 0.05 | 11,587 | 1,290 | 2,675 |
| `right` | 0.05 | 26,864 | 2,578 | 5,991 |
| **`max(left, right)`** | **0.05** | **1,911** | **173** | **233** |
| `max(left, right)` | 0.10 | 1,003 | 51 | 75 |

`max` at 5% is the only reading close to the original, and it
recovers all 179 of the original's top-5000 MWEs. The other three are
off by 10-40x. Set in config as
`bigrams.collocation_share_denominator: max`.

## Band: ranks 1-5000

- Entries: original 5,000, rebuild 5,000
- **Shared lemmas: 3,565 (71.3% of the original)**
- Jaccard: 0.554
- **Spearman rho on shared lemmas: 0.8273**
- pos_guess agreement: 97.1% over 3,565 shared lemmas
- MWEs: original 179, rebuild 52, shared 41

> pos_guess rules were fitted to `out/` (see scripts/fit_postag.py),
> so this agreement figure is partly circular and is not evidence
> that the tagger is good -- only that it reproduces the original,
> mistakes included.

### Largest rank movements (shared lemmas)

| lemma | original | rebuild | move |
|---|---:|---:|---:|
| `pedido` | 4851 | 1130 | -3,721 |
| `ator` | 4666 | 952 | -3,714 |
| `hospedeiro` | 4737 | 1062 | -3,675 |
| `entrega` | 4710 | 1074 | -3,636 |
| `acusado` | 4629 | 1057 | -3,572 |
| `exato` | 4754 | 1271 | -3,483 |
| `soro` | 4493 | 1013 | -3,480 |
| `saída` | 4557 | 1095 | -3,462 |
| `liso` | 1509 | 4918 | +3,409 |
| `peste` | 4955 | 1570 | -3,385 |
| `maravilha` | 4828 | 1511 | -3,317 |
| `largo` | 4101 | 843 | -3,258 |
| `sentido` | 3865 | 630 | -3,235 |
| `acabado` | 4254 | 1084 | -3,170 |
| `fixar` | 4048 | 893 | -3,155 |
| `vista` | 3864 | 709 | -3,155 |
| `exceto` | 4514 | 1372 | -3,142 |
| `direto` | 4490 | 1357 | -3,133 |
| `esposo` | 602 | 3678 | +3,076 |
| `ato` | 4313 | 1253 | -3,060 |
| `bebido` | 831 | 3891 | +3,060 |
| `cofre` | 1554 | 4593 | +3,039 |
| `compor` | 4480 | 1481 | -2,999 |
| `cuidado` | 3253 | 325 | -2,928 |
| `errar` | 3435 | 554 | -2,881 |

### In the original, missing from the rebuild

`me`, `te`, `mas`, `lhe`, `nós`, `mim`, `dois`, `quer`, `deus`, `ti`, `tinha`, `sr`, `preciso`, `vão`, `apenas`, `vá`, `vê`, `fez`, `vos`, `acha`, `se passa`, `óptimo`, `gosto`, `feito`, `os meus`, `dr`, `lamento`, `visto`, `amo`, `sai`, `vai ser`, `na verdade`, `john`, `pais`, `penso`, `exactamente`, `estivar`, `fazer isto`, `certa`, `toma`, `sam`, `mr`, `dê`, `à procura`, `deve`, `esteve`, `és tu`, `olhe`, `trouxe`, `te preocupes`, `maldito`, `michael`, `fixe`, `lá fora`, `tom`, `alguma vez`, `deve ter`, `simples`, `jesus`, `tira`

_1,435 total._

### New in the rebuild, absent from the original

`a`, `o que`, `no`, `na`, `nos`, `é que`, `eles`, `que é`, `é o`, `nó`, `é um`, `tua`, `doi`, `é uma`, `pelo`, `pela`, `num`, `fora`, `apena`, `disso`, `por isso`, `nas`, `numa`, `parte`, `deles`, `contigo`, `todos os`, `desta`, `cara`, `sozinho`, `disto`, `da minha`, `senhora`, `nisso`, `menina`, `todas as`, `neste`, `deste`, `filha`, `sim senhor`, `pelos`, `ei`, `dizem`, `nesta`, `esposa`, `irmã`, `simple`, `amiga`, `miúda`, `surpresa`, `connosco`, `escuta`, `maldizer`, `inspetor`, `mente`, `pelas`, `esquerda`, `dessa`, `pra`, `dum`

_1,435 total._

## Band: ranks 5001-10000

- Entries: original 5,000, rebuild 5,000
- **Shared lemmas: 1,979 (39.6% of the original)**
- Jaccard: 0.247
- **Spearman rho on shared lemmas: 0.2330**
- pos_guess agreement: 98.5% over 1,979 shared lemmas
- MWEs: original 111, rebuild 0, shared 0

> pos_guess rules were fitted to `out/` (see scripts/fit_postag.py),
> so this agreement figure is partly circular and is not evidence
> that the tagger is good -- only that it reproduces the original,
> mistakes included.

### Largest rank movements (shared lemmas)

| lemma | original | rebuild | move |
|---|---:|---:|---:|
| `histeria` | 9960 | 5039 | -4,921 |
| `socialmente` | 9966 | 5247 | -4,719 |
| `inestimável` | 9894 | 5185 | -4,709 |
| `pedinte` | 9910 | 5203 | -4,707 |
| `remexer` | 9935 | 5235 | -4,700 |
| `claque` | 5239 | 9803 | +4,564 |
| `xixi` | 5069 | 9574 | +4,505 |
| `dedução` | 9949 | 5482 | -4,467 |
| `bendizer` | 9588 | 5140 | -4,448 |
| `lagarta` | 9453 | 5053 | -4,400 |
| `composto` | 5456 | 9831 | +4,375 |
| `louvor` | 9423 | 5059 | -4,364 |
| `robot` | 5125 | 9441 | +4,316 |
| `pulha` | 9383 | 5085 | -4,298 |
| `florestal` | 9607 | 5351 | -4,256 |
| `encriptação` | 9750 | 5499 | -4,251 |
| `contornar` | 5625 | 9855 | +4,230 |
| `caloiro` | 5537 | 9752 | +4,215 |
| `distração` | 9354 | 5164 | -4,190 |
| `ninhar` | 9384 | 5196 | -4,188 |
| `berma` | 9307 | 5141 | -4,166 |
| `içar` | 5079 | 9223 | +4,144 |
| `puxo` | 9921 | 5796 | -4,125 |
| `montante` | 9473 | 5387 | -4,086 |
| `ganharia` | 9426 | 5357 | -4,069 |

### In the original, missing from the rebuild

`fulano`, `dificil`, `broche`, `riso`, `solidão`, `mamilo`, `atormentar`, `nadia`, `refúgio`, `complicação`, `presta atenção`, `riscar`, `cubo`, `encanto`, `phoenix`, `bónus`, `naval`, `embrulhar`, `hambúrguer`, `molhado`, `pierce`, `orientar`, `daniels`, `tirado`, `mills`, `andrea`, `técnica`, `garrett`, `beneficiar`, `hans`, `vermelhas`, `stevens`, `river`, `contabilista`, `jeitoso`, `jurisdição`, `impressionado`, `inocência`, `magoado`, `paula`, `douglas`, `fatiar`, `passarinhar`, `hastings`, `jerusalém`, `administrar`, `cruzado`, `improvável`, `modesto`, `ofendido`, `ranger`, `jr`, `robinson`, `aberta`, `ellis`, `cunhar`, `devorar`, `carroçar`, `atlanta`, `dixon`

_3,021 total._

### New in the rebuild, absent from the original

`burlar`, `castanha`, `colegial`, `criancice`, `cálculo`, `céaro`, `descaramento`, `destacar`, `diet`, `dios`, `erógena`, `esgotar`, `evacuação`, `faceta`, `faéar`, `guarda-roupa`, `horripilante`, `imparcial`, `incendiar`, `intercetar`, `knox`, `lavandaria`, `lisongeado`, `literal`, `ln-and-out`, `mandea`, `mariquinha`, `meias-finais`, `mero`, `metal`, `metemorfoseie`, `mirtilo`, `murro`, `neblina`, `ninfomania`, `parlar`, `património`, `pneu`, `pornógrafo`, `quinta-feira`, `quinteto`, `recibo`, `renunciar`, `repúblico`, `rotar`, `salsaparrilha`, `satiríase`, `semifinal`, `signore`, `subespacial`, `suplicar`, `tinir`, `tinto`, `totó`, `trave`, `troféu`, `troque`, `uivar`, `usted`, `vaginal`

_3,021 total._

## Against the stage 1 baseline

Stage 1 reproduced the original pipeline including its flaws.
These figures isolate what the stage 2 fixes actually changed.

### Band: ranks 1-5000

- Shared with baseline: 3,751 (75.0%)
- Spearman rho vs baseline: 0.8344

**Dropped by the fixes** (in stage 1, gone in stage 2):

`uma`, `mas`, `me`, `te`, `que não`, `o meu`, `pelar`, `nós`, `mim`, `sua`, `dois`, `quer`, `deus`, `ti`, `sr`, `lhe`, `preciso`, `apenas`, `acha`, `se passa`, `gosto`, `com ele`, `feito`, `os meus`, `óptimo`, `dr`, `lamento`, `primeira`, `distar`, `nossos`, `calmar`, `umas`, `vai ser`, `na verdade`, `na minha`, `dá-me`, `jack`, `tuas`, `john`, `vos`, `pais`, `exactamente`, `fazer isto`, `diz-me`, `certa`, `sam`, `à procura`, `deve`, `tinha`, `vê`, `visto`, `és tu`, `te preocupes`, `michael`, `fixe`, `lá fora`, `vale`, `tom`, `alguma vez`, `frank`

_1,249 total._

**Promoted by the fixes** (new in stage 2):

`a`, `da`, `no`, `na`, `nos`, `eles`, `que é`, `nó`, `dos`, `doi`, `das`, `pela`, `fora`, `apena`, `às`, `nas`, `numa`, `aos`, `contigo`, `calma`, `cara`, `causa`, `sozinho`, `disto`, `menina`, `sim senhor`, `pelos`, `ei`, `dizem`, `nesta`, `falta`, `esposa`, `irmã`, `simple`, `amiga`, `miúda`, `connosco`, `escuta`, `inspetor`, `mente`, `pelas`, `pra`, `mostra`, `rio`, `nessa`, `noiva`, `graças`, `ator`, `destes`, `papá`, `direita`, `destas`, `avó`, `capitã`, `naquela`, `tia`, `daquela`, `breaker`, `aspeto`, `daqueles`

_1,249 total._

### Band: ranks 5001-10000

- Shared with baseline: 1,996 (39.9%)
- Spearman rho vs baseline: 0.2451

**Dropped by the fixes** (in stage 1, gone in stage 2):

`definição`, `chef`, `cigano`, `indefeso`, `gaiola`, `desfeito`, `reconsiderar`, `ponto final`, `cultivar`, `furar`, `thor`, `esplêndido`, `deu-te`, `bébé`, `hudson`, `terramoto`, `política`, `rodado`, `flechar`, `formal`, `insecto`, `restrito`, `isolado`, `enervar`, `cortina`, `nasa`, `artilharia`, `marijuana`, `cenoura`, `congelado`, `manda`, `morango`, `dvd`, `irlanda`, `facebook`, `húmido`, `precipitar`, `pontaria`, `bernard`, `moore`, `frankenstein`, `amo-a`, `corrido`, `urinar`, `asneira`, `interruptor`, `sandra`, `trégua`, `marcel`, `telegrama`, `tóquio`, `fiz-te`, `corrupção`, `sonda`, `confirmado`, `táctica`, `ir-me`, `iludir`, `causado`, `milionário`

_3,004 total._

**Promoted by the fixes** (new in stage 2):

`burlar`, `castanha`, `colegial`, `criancice`, `cálculo`, `céaro`, `descaramento`, `destacar`, `diet`, `dios`, `elite`, `erógena`, `esgotar`, `evacuação`, `faceta`, `faéar`, `fr`, `histeria`, `horripilante`, `imparcial`, `incendiar`, `intercetar`, `knox`, `lavandaria`, `lisongeado`, `literal`, `ln-and-out`, `mandea`, `mariquinha`, `meias-finais`, `mero`, `metal`, `metemorfoseie`, `mirtilo`, `murro`, `neblina`, `ninfomania`, `parlar`, `património`, `pneu`, `pornógrafo`, `quinta-feira`, `quinteto`, `recibo`, `renunciar`, `repúblico`, `rotar`, `salsaparrilha`, `satiríase`, `semifinal`, `signore`, `subespacial`, `suplicar`, `tinir`, `tinto`, `trave`, `troféu`, `troque`, `uivar`, `usted`

_3,004 total._

## Lemmatization conventions (eval/conventions.md)

Each convention remaps surfaces from one headword to another. Below:
the published entries each one created, grew or protected, and the
former headwords it merged away that were big enough to have been
published on their own (>= 4 tokens, the rank-10000 count).

| convention | surfaces remapped | tokens moved |
|---|---:|---:|
| Clitic l-forms are the pronoun o/a (lo -> o) | 4 | 8,344 |
| 1. Contractions are their own entries | 17 | 8,216 |
| 2. Gendered nouns fold into the masculine | 4 | 11 |
| 2. (exception) Feminines with their own meaning kept separate | 122 | 88,294 |
| 3. Diminutives stay separate | 251 | 1,219 |
| 4. Comparatives are their own lemmas | 2 | 245 |
| 5. Spelling-reform variants merge under the post-1990 spelling | 393 | 6,298 |

### Clitic l-forms are the pronoun o/a (lo -> o)

| entry | rank | tokens gained | from surfaces |
|---|---:|---:|---|
| `o` | 1 | 4,474 | `lo` |
| `a` | 4 | 2,230 | `la` |

Former headwords merged away: `las` (514)

### 1. Contractions are their own entries

| entry | rank | tokens gained | from surfaces |
|---|---:|---:|---|
| `nos` | 49 | 7,435 | `nos` |
| `daquelas` | 1402 | 140 | `daquelas` |
| `nela` | 1512 | 127 | `nela` |
| `convosco` | 1714 | 106 | `convosco` |
| `neles` | 2171 | 73 | `neles` |
| `nestas` | 2395 | 62 | `nestas` |
| `nessas` | 2570 | 56 | `nessas` |
| `naquelas` | 3276 | 38 | `naquelas` |
| `nesses` | 3327 | 37 | `nesses` |
| `nestes` | 3384 | 36 | `nestes` |
| `naqueles` | 3445 | 35 | `naqueles` |
| `noutros` | 3853 | 29 | `noutros` |
| `àquela` | 4824 | 20 | `àquela` |
| `àqueles` | 6073 | 13 | `àqueles` |
| `nuns` | 9312 | 5 | `nuns` |

Former headwords merged away: `nós` (7,435)

### 2. Gendered nouns fold into the masculine

| entry | rank | tokens gained | from surfaces |
|---|---:|---:|---|
| `parvo` | 915 | 6 | `parvas` |
| `tolo` | 1198 | 3 | `tolas` |

Former headwords merged away: `parva` (6)

### 2. (exception) Feminines with their own meaning kept separate

| entry | rank | tokens gained | from surfaces |
|---|---:|---:|---|
| `a` | 4 | 85,346 | `a` |
| `miúda` | 695 | 39 | `miúdas` |
| `tia` | 1158 | 12 | `tias` |
| `política` | 1388 | 132 | `política` |
| `namorada` | 1394 | 136 | `namorada` |
| `prostituta` | 1463 | 133 | `prostituta`, `prostitutas` |
| `ferida` | 1482 | 54 | `ferida` |
| `tinta` | 1564 | 47 | `tinta` |
| `marinha` | 1623 | 115 | `marinha` |
| `alternativa` | 1636 | 91 | `alternativa` |
| `enfermeira` | 1689 | 108 | `enfermeira`, `enfermeiras` |
| `traseira` | 1946 | 9 | `traseira` |
| `secretária` | 1968 | 83 | `secretária` |
| `moça` | 2076 | 78 | `moça`, `moças` |
| `pegada` | 2182 | 32 | `pegada` |
| `pata` | 2218 | 35 | `pata` |
| `prática` | 2400 | 48 | `prática` |
| `santa` | 2403 | 62 | `santa`, `santas` |
| `seca` | 2518 | 58 | `seca` |
| `solitária` | 2519 | 53 | `solitária` |
| `clínica` | 2552 | 54 | `clínica` |
| `técnica` | 2611 | 46 | `técnica` |
| `lógica` | 2658 | 52 | `lógica` |
| `parada` | 2680 | 35 | `parada` |
| `nata` | 2789 | 27 | `nata` |

_55 further published entries affected._

Former headwords merged away: `namorado` (136), `prostituto` (133), `alternativo` (91), `ferido` (54), `empregado` (47), `viúvo` (41), `parado` (35), `testo` (33), `culinário` (32), `pegado` (32), `penitenciário` (17), `ético` (17), `mono` (16), `cunhado` (15), `calçado` (11), `gasoso` (11), `florido` (9), `balístico` (7), `virado` (7), `chapado` (6), `roberto` (4)

### 3. Diminutives stay separate

| entry | rank | tokens gained | from surfaces |
|---|---:|---:|---|
| `bocadinho` | 2002 | 82 | `bocadinho`, `bocadinhos` |
| `engraçadinho` | 2776 | 49 | `engraçadinho` |
| `coisinha` | 2990 | 44 | `coisinha`, `coisinhas` |
| `coitadinho` | 3304 | 37 | `coitadinho` |
| `aleijadinho` | 3584 | 32 | `aleijadinho`, `aleijadinhos` |
| `trabalhinho` | 3650 | 32 | `trabalhinho`, `trabalhinhos` |
| `bolinho` | 3803 | 29 | `bolinho`, `bolinhos` |
| `irmãozinho` | 3843 | 28 | `irmãozinho` |
| `pombinho` | 3950 | 2 | `pombinho`, `pombinhos` |
| `certinho` | 4094 | 26 | `certinho`, `certinhos` |
| `amorzinho` | 4355 | 23 | `amorzinho` |
| `peixinho` | 4427 | 23 | `peixinho`, `peixinhos` |
| `paizinho` | 4543 | 22 | `paizinho`, `paizinhos` |
| `quentinho` | 4668 | 21 | `quentinho` |
| `mortinha` | 4775 | 20 | `mortinha`, `mortinhas` |
| `depressinha` | 4875 | 19 | `depressinha` |
| `cachorrinho` | 5143 | 17 | `cachorrinho` |
| `cheirinho` | 5299 | 16 | `cheirinho` |
| `cãozinho` | 5478 | 15 | `cãozinho` |
| `queridinho` | 5572 | 15 | `queridinho`, `queridinhos` |
| `calcinha` | 5636 | 4 | `calcinha` |
| `ursinho` | 5832 | 14 | `ursinho`, `ursinhos` |
| `adeusinho` | 5842 | 13 | `adeusinho` |
| `lindinho` | 5977 | 13 | `lindinho` |
| `devagarinho` | 6143 | 12 | `devagarinho` |

_48 further published entries affected._

Former headwords merged away: `coitado` (44), `aleijado` (32), `torrão` (12), `palmada` (8), `comportado` (6), `crescido` (5), `fala` (5), `quadrado` (4)

### 4. Comparatives are their own lemmas

| entry | rank | tokens gained | from surfaces |
|---|---:|---:|---|
| `melhor` | 107 | 160 | `melhores` |
| `pior` | 571 | 85 | `piores` |

### 5. Spelling-reform variants merge under the post-1990 spelling

| entry | rank | tokens gained | from surfaces |
|---|---:|---:|---|
| `estar` | 9 | 6 | `ptá` |
| `doutor` | 377 | 1 | `douctor` |
| `exatamente` | 460 | 454 | `exactamente` |
| `situação` | 491 | 1 | `situacção` |
| `licença` | 516 | 1 | `licencça` |
| `ação` | 731 | 251 | `acção`, `acções` |
| `inspetor` | 757 | 238 | `inspector`, `inspectores` |
| `detetive` | 880 | 174 | `detective` |
| `ator` | 952 | 219 | `actor`, `actores`, `actrizes` |
| `correto` | 983 | 152 | `correcta`, `correcto` |
| `direção` | 990 | 182 | `direcção`, `direcções` |
| `vítima` | 1101 | 1 | `víctima` |
| `diretor` | 1201 | 111 | `director`, `directora`, `directores` |
| `espetáculo` | 1213 | 115 | `espectáculo`, `espectáculos` |
| `ato` | 1253 | 129 | `acto`, `actos` |
| `exato` | 1271 | 123 | `exacto`, `exactos` |
| `aspeto` | 1275 | 117 | `aspecto` |
| `direto` | 1357 | 107 | `directa`, `directo`, `directos` |
| `exceto` | 1372 | 115 | `excepto` |
| `objetivo` | 1387 | 114 | `objectivo`, `objectivos` |
| `elétrico` | 1503 | 105 | `eléctrica`, `eléctrico`, `eléctricos` |
| `contratar` | 1516 | 1 | `contractado` |
| `reação` | 1597 | 93 | `reacção`, `reacções` |
| `ativar` | 1618 | 65 | `activa`, `activado`, `activar`, `activámos` |
| `objeto` | 1672 | 91 | `objecto`, `objectos` |

_126 further published entries affected._

Former headwords merged away: `óptimo` (536), `exactamente` (454), `inspector` (231), `acção` (200), `detective` (174), `direcção` (171), `actor` (154), `correcto` (122), `exacto` (121), `aspecto` (117), `excepto` (115), `acto` (105), `espectáculo` (103), `director` (102), `directo` (96), `óptima` (85), `objectivo` (83), `directamente` (81), `electricidade` (70), `eléctrica` (67), `actores` (64), `objecto` (64), `projecto` (62), `protecção` (62), `espectacular` (54)


## Gold-set lemmatizer accuracy

Gold set: `eval/lemma_gold.tsv` — 332 scored rows, 68 marked `drop` and excluded

| backend | accuracy | ranks 1-1000 | 1001-10000 | 10001+ |
|---|---:|---:|---:|---:|
| `pipeline, stage 2 (gated)` | **91.6%** | 100.0% | 92.6% | 77.6% |

<details><summary>pipeline, stage 2 (gated): 28 disagreements</summary>

| surface | gold | predicted |
|---|---|---|
| `agulha` | `agulha` | `agulhar` |
| `cais` | `cais` | `cal` |
| `numero` | `número` | `numerar` |
| `apanhámo` | `apanhar` | `apanhámo` |
| `fenda` | `fenda` | `fender` |
| `vazias` | `vazio` | `vaziar` |
| `revolta` | `revolta` | `revoltar` |
| `pilhas` | `pilha` | `pilhar` |
| `encoste` | `encostar` | `encoste` |
| `crescemos` | `crescer` | `crescemos` |
| `quadrados` | `quadrado` | `quadrar` |
| `salgado` | `salgado` | `salgar` |
| `patinho` | `patinho` | `patinhar` |
| `borbulhas` | `borbulha` | `borbulhar` |
| `despeçam` | `despedir` | `despeçam` |
| `lavaste` | `lavar` | `lavaste` |
| `colabora` | `colaborar` | `colabora` |
| `cumprindo` | `cumprir` | `cumprindo` |
| `jure` | `jurar` | `jure` |
| `mascarada` | `mascarar|mascarado` | `mascarada` |
| `bodes` | `bode` | `bodes` |
| `cientifica` | `científico` | `cientifica` |
| `educadas` | `educar|educado` | `educadas` |
| `excitou` | `excitar` | `excitou` |
| `sâo` | `são` | `sâo` |
| `designadas` | `designar|designado` | `designadas` |
| `insistimos` | `insistir` | `insistimos` |
| `armazenados` | `armazenar|armazenado` | `armazenados` |

</details>


## Quality report

# Quality report: suspect duplicate entries

Stage 2. Gate: FAIL on suspects.

**85 suspects**: diacritic 84, inflected 1

| kind | entry | rank | duplicate of | rank | detail |
|---|---|---:|---|---:|---|
| diacritic | `idéia` | 1384 | `ideia` | 260 | both fold to 'ideia' |
| diacritic | `dói` | 2178 | `doi` | 112 | both fold to 'doi' |
| diacritic | `hà` | 2293 | `ha` | 1717 | both fold to 'ha' |
| diacritic | `hã` | 2447 | `ha` | 1717 | both fold to 'ha' |
| diacritic | `cú` | 2554 | `cu` | 807 | both fold to 'cu' |
| diacritic | `familia` | 2701 | `família` | 364 | both fold to 'familia' |
| diacritic | `demônio` | 3109 | `demónio` | 1644 | both fold to 'demonio' |
| diacritic | `sao` | 3395 | `säo` | 2721 | both fold to 'sao' |
| diacritic | `rã` | 3458 | `ra` | 1933 | both fold to 'ra' |
| diacritic | `estao` | 3618 | `estäo` | 3210 | both fold to 'estao' |
| diacritic | `cerimônia` | 4372 | `cerimónia` | 1775 | both fold to 'cerimonia' |
| diacritic | `freqüência` | 4516 | `frequência` | 2910 | both fold to 'frequencia' |
| inflected | `hs` | 4632 | `h` | 877 | hs is a regular inflection of h |
| diacritic | `joia` | 4644 | `jóia` | 2537 | both fold to 'joia' |
| diacritic | `obvio` | 4778 | `óbvio` | 1599 | both fold to 'obvio' |
| diacritic | `väo` | 4822 | `vao` | 4456 | both fold to 'vao' |
| diacritic | `provávelmente` | 4950 | `provavelmente` | 800 | both fold to 'provavelmente' |
| diacritic | `prêmio` | 5220 | `prémio` | 1885 | both fold to 'premio' |
| diacritic | `cha` | 5469 | `chá` | 982 | both fold to 'cha' |
| diacritic | `experiencia` | 5509 | `experiência` | 813 | both fold to 'experiencia' |
| diacritic | `figâdo` | 5513 | `fígado` | 3430 | both fold to 'figado' |
| diacritic | `mamae` | 5543 | `mamãe` | 1174 | both fold to 'mamae' |
| diacritic | `seqüência` | 5585 | `sequência` | 2158 | both fold to 'sequencia' |
| diacritic | `quilômetro` | 5797 | `quilómetro` | 2604 | both fold to 'quilometro' |
| diacritic | `batalhao` | 5864 | `batalhão` | 2987 | both fold to 'batalhao' |
| diacritic | `terrivel` | 6057 | `terrível` | 986 | both fold to 'terrivel' |
| diacritic | `indio` | 6194 | `índio` | 1298 | both fold to 'indio' |
| diacritic | `raínha` | 6246 | `rainha` | 1070 | both fold to 'rainha' |
| diacritic | `suíte` | 6272 | `suite` | 3463 | both fold to 'suite' |
| diacritic | `britanico` | 6326 | `britânico` | 1592 | both fold to 'britanico' |
| diacritic | `fenómeno` | 6406 | `fenômeno` | 5937 | both fold to 'fenomeno' |
| diacritic | `päo` | 6501 | `pão` | 2184 | both fold to 'pao' |
| diacritic | `saida` | 6521 | `saída` | 1095 | both fold to 'saida' |
| diacritic | `secretaria` | 6525 | `secretária` | 1968 | both fold to 'secretaria' |
| diacritic | `comitê` | 6622 | `comité` | 5306 | both fold to 'comite' |
| diacritic | `cupido` | 6645 | `cúpido` | 6359 | both fold to 'cupido' |
| diacritic | `delinqüente` | 6650 | `delinquente` | 4194 | both fold to 'delinquente' |
| diacritic | `porêm` | 6804 | `porém` | 1217 | both fold to 'porem' |
| diacritic | `pêra` | 6817 | `pera` | 4322 | both fold to 'pera' |
| diacritic | `taxi` | 6862 | `táxi` | 1211 | both fold to 'taxi' |
| diacritic | `vôo` | 6880 | `voo` | 1971 | both fold to 'voo' |
| diacritic | `audio` | 6918 | `áudio` | 5259 | both fold to 'audio' |
| diacritic | `diario` | 6997 | `diário` | 2620 | both fold to 'diario' |
| diacritic | `fácilmente` | 7047 | `facilmente` | 2267 | both fold to 'facilmente' |
| diacritic | `lingua` | 7096 | `língua` | 1238 | both fold to 'lingua' |
| diacritic | `matrimónio` | 7108 | `matrimônio` | 6759 | both fold to 'matrimonio' |
| diacritic | `mío` | 7126 | `mio` | 7117 | both fold to 'mio' |
| diacritic | `princípe` | 7156 | `príncipe` | 1695 | both fold to 'principe' |
| diacritic | `calcar` | 7318 | `calçar` | 6332 | both fold to 'calcar' |
| diacritic | `gênio` | 7447 | `génio` | 1693 | both fold to 'genio' |
| diacritic | `heroi` | 7453 | `herói` | 1418 | both fold to 'heroi' |
| diacritic | `moínho` | 7526 | `moinho` | 3632 | both fold to 'moinho' |
| diacritic | `tas` | 7651 | `tás` | 4253 | both fold to 'tas' |
| diacritic | `tranqüilo` | 7664 | `tranquilo` | 2427 | both fold to 'tranquilo' |
| diacritic | `voluntario` | 7689 | `voluntário` | 2262 | both fold to 'voluntario' |
| diacritic | `và` | 7690 | `va` | 4347 | both fold to 'va' |
| diacritic | `frequencia` | 7885 | `frequência` | 2910 | both fold to 'frequencia' |
| diacritic | `musculo` | 7984 | `músculo` | 3444 | both fold to 'musculo' |
| diacritic | `oxigênio` | 8010 | `oxigénio` | 4320 | both fold to 'oxigenio' |
| diacritic | `revoluçäo` | 8081 | `revolução` | 2543 | both fold to 'revolucao' |
| diacritic | `últimamente` | 8177 | `ultimamente` | 2520 | both fold to 'ultimamente' |
| diacritic | `anônimo` | 8210 | `anónimo` | 6307 | both fold to 'anonimo' |
| diacritic | `bla` | 8241 | `blá` | 4090 | both fold to 'bla' |
| diacritic | `bracal` | 8246 | `braçal` | 7310 | both fold to 'bracal' |
| diacritic | `ingênuo` | 8486 | `ingénuo` | 4757 | both fold to 'ingenuo' |
| diacritic | `milênio` | 8546 | `milénio` | 5761 | both fold to 'milenio' |
| diacritic | `senor` | 8700 | `señor` | 6848 | both fold to 'senor' |
| diacritic | `troçar` | 8751 | `trocar` | 944 | both fold to 'trocar' |
| diacritic | `troço` | 8752 | `troco` | 2160 | both fold to 'troco' |
| diacritic | `bla-bla-bla` | 8869 | `blá-blá-blá` | 7305 | both fold to 'bla-bla-bla' |
| diacritic | `caço` | 8907 | `caco` | 8257 | both fold to 'caco' |
| diacritic | `cinqüenta` | 8917 | `cinquenta` | 3417 | both fold to 'cinquenta' |
| diacritic | `dancarina` | 8968 | `dançarina` | 4723 | both fold to 'dancarina' |
| diacritic | `freqüentemente` | 9124 | `frequentemente` | 5354 | both fold to 'frequentemente' |
| diacritic | `frigorifico` | 9125 | `frigorífico` | 3319 | both fold to 'frigorifico' |
| diacritic | `irônico` | 9220 | `irónico` | 5049 | both fold to 'ironico' |
| diacritic | `pôquer` | 9404 | `póquer` | 3565 | both fold to 'poquer' |
| diacritic | `rosé` | 9445 | `rose` | 5240 | both fold to 'rose' |
| diacritic | `sensivel` | 9459 | `sensível` | 2015 | both fold to 'sensivel' |
| diacritic | `acadêmico` | 9587 | `académico` | 6572 | both fold to 'academico' |
| diacritic | `assassinio` | 9660 | `assassínio` | 3023 | both fold to 'assassinio' |
| diacritic | `camera` | 9753 | `câmera` | 4874 | both fold to 'camera' |
| diacritic | `coincidencia` | 9811 | `coincidência` | 2055 | both fold to 'coincidencia' |
| diacritic | `colônia` | 9819 | `colónia` | 7790 | both fold to 'colonia' |
| diacritic | `congénito` | 9841 | `congênito` | 8938 | both fold to 'congenito' |

## Diacritic folds

449 lemmas were folded into an accent variant at least 20x as frequent (218 unaccented, 231 wrong or Brazilian accent). Every fold is listed.

### Folds of a dictionary word (7) — review these

The source is a real PT word, merged on frequency alone. Most are missing-accent typos of a far commoner word; any that is a genuine second word should go on a keep-list.

| from | count | into | count | ratio |
|---|---:|---|---:|---:|
| `tao` | 56 | `tão` | 3,076 | 55x |
| `manha` | 16 | `manhã` | 675 | 42x |
| `ola` | 14 | `olá` | 2,236 | 160x |
| `mao` | 5 | `mão` | 1,587 | 317x |
| `avo` | 4 | `avô` | 375 | 94x |
| `capita` | 2 | `capitã` | 195 | 98x |
| `revolver` | 1 | `revólver` | 126 | 126x |

<details><summary>All other folds (442)</summary>

| from | count | into | count | kind |
|---|---:|---|---:|---|
| `näo` | 1,079 | `não` | 74,246 | accent_variant |
| `nao` | 780 | `não` | 74,246 | unaccented |
| `á` | 340 | `a` | 87,582 | accent_variant |
| `voce` | 190 | `você` | 10,982 | unaccented |
| `ã` | 95 | `a` | 87,582 | accent_variant |
| `so` | 85 | `só` | 7,169 | unaccented |
| `ja` | 76 | `já` | 8,429 | unaccented |
| `è` | 70 | `e` | 41,911 | accent_variant |
| `jà` | 62 | `já` | 8,429 | accent_variant |
| `entäo` | 58 | `então` | 4,619 | accent_variant |
| `tambem` | 50 | `também` | 3,561 | unaccented |
| `mae` | 46 | `mãe` | 2,132 | unaccented |
| `alguem` | 45 | `alguém` | 2,331 | unaccented |
| `ninguem` | 37 | `ninguém` | 2,250 | unaccented |
| `voçê` | 36 | `você` | 10,982 | accent_variant |
| `saír` | 33 | `sair` | 3,413 | accent_variant |
| `â` | 33 | `a` | 87,582 | accent_variant |
| `entao` | 32 | `então` | 4,619 | unaccented |
| `là` | 32 | `lá` | 6,641 | accent_variant |
| `mäo` | 31 | `mão` | 1,587 | accent_variant |
| `pêlo` | 27 | `pelo` | 2,234 | accent_variant |
| `aquí` | 26 | `aqui` | 9,410 | accent_variant |
| `vêr` | 26 | `ver` | 10,944 | accent_variant |
| `sózinho` | 25 | `sozinho` | 778 | accent_variant |
| `sô` | 24 | `só` | 7,169 | accent_variant |
| `mäe` | 21 | `mãe` | 2,132 | accent_variant |
| `dolar` | 19 | `dólar` | 934 | unaccented |
| `dà` | 19 | `da` | 13,889 | accent_variant |
| `täo` | 19 | `tão` | 3,076 | accent_variant |
| `dificil` | 18 | `difícil` | 579 | unaccented |
| `coracao` | 15 | `coração` | 646 | unaccented |
| `dancar` | 14 | `dançar` | 331 | unaccented |
| `possivel` | 14 | `possível` | 586 | unaccented |
| `ca` | 13 | `cá` | 1,895 | unaccented |
| `irmäo` | 13 | `irmão` | 926 | accent_variant |
| `atencao` | 12 | `atenção` | 395 | unaccented |
| `metrô` | 12 | `metro` | 423 | accent_variant |
| `razao` | 12 | `razão` | 1,250 | unaccented |
| `miudo` | 11 | `miúdo` | 827 | unaccented |
| `questao` | 11 | `questão` | 565 | unaccented |
| `ãs` | 11 | `às` | 1,603 | accent_variant |
| `amanhä` | 10 | `amanhã` | 910 | accent_variant |
| `cabeca` | 10 | `cabeça` | 1,077 | unaccented |
| `coraçäo` | 10 | `coração` | 646 | accent_variant |
| `espirito` | 10 | `espírito` | 300 | unaccented |
| `día` | 9 | `dia` | 4,004 | accent_variant |
| `especie` | 9 | `espécie` | 321 | unaccented |
| `impossivel` | 9 | `impossível` | 285 | unaccented |
| `maé` | 9 | `mãe` | 2,132 | accent_variant |
| `mêdo` | 9 | `medo` | 973 | accent_variant |
| `tambêm` | 9 | `também` | 3,561 | accent_variant |
| `õ` | 9 | `o` | 124,948 | accent_variant |
| `facil` | 8 | `fácil` | 463 | unaccented |
| `ninguêm` | 8 | `ninguém` | 2,250 | accent_variant |
| `voçe` | 8 | `você` | 10,982 | accent_variant |
| `ajudà` | 7 | `ajuda` | 987 | accent_variant |
| `capitäo` | 7 | `capitão` | 586 | accent_variant |
| `patrao` | 7 | `patrão` | 205 | unaccented |
| `rápidamente` | 7 | `rapidamente` | 165 | accent_variant |
| `video` | 7 | `vídeo` | 162 | unaccented |
| `virus` | 7 | `vírus` | 148 | unaccented |
| `agradavel` | 6 | `agradável` | 211 | unaccented |
| `alí` | 6 | `ali` | 1,230 | accent_variant |
| `codigo` | 6 | `código` | 167 | unaccented |
| `comissäo` | 6 | `comissão` | 178 | accent_variant |
| `hà-de` | 6 | `há-de` | 131 | accent_variant |
| `nivel` | 6 | `nível` | 126 | unaccented |
| `nôs` | 6 | `nos` | 7,435 | accent_variant |
| `olà` | 6 | `olá` | 2,236 | accent_variant |
| `proximo` | 6 | `próximo` | 742 | unaccented |
| `situaçäo` | 6 | `situação` | 507 | accent_variant |
| `tío` | 6 | `tio` | 367 | accent_variant |
| `àcerca` | 6 | `acerca` | 393 | accent_variant |
| `àgua` | 6 | `água` | 651 | accent_variant |
| `america` | 5 | `américa` | 190 | unaccented |
| `apos` | 5 | `após` | 285 | unaccented |
| `area` | 5 | `área` | 196 | unaccented |
| `atras` | 5 | `atrás` | 887 | unaccented |
| `braco` | 5 | `braço` | 366 | unaccented |
| `cafe` | 5 | `café` | 447 | unaccented |
| `camara` | 5 | `câmara` | 265 | unaccented |
| `caír` | 5 | `cair` | 658 | accent_variant |
| `danca` | 5 | `dança` | 233 | unaccented |
| `excelencia` | 5 | `excelência` | 136 | unaccented |
| `horrivel` | 5 | `horrível` | 276 | unaccented |
| `juri` | 5 | `júri` | 184 | unaccented |
| `mamä` | 5 | `mamã` | 190 | accent_variant |
| `manhä` | 5 | `manhã` | 675 | accent_variant |
| `mes` | 5 | `mês` | 650 | unaccented |
| `míudo` | 5 | `miúdo` | 827 | accent_variant |
| `pe` | 5 | `pé` | 658 | unaccented |
| `perdao` | 5 | `perdão` | 202 | unaccented |
| `rapido` | 5 | `rápido` | 680 | unaccented |
| `relogio` | 5 | `relógio` | 163 | unaccented |
| `saude` | 5 | `saúde` | 236 | unaccented |
| `servico` | 5 | `serviço` | 338 | unaccented |
| `agüentar` | 4 | `aguentar` | 475 | accent_variant |
| `alguêm` | 4 | `alguém` | 2,331 | accent_variant |
| `alêm` | 4 | `além` | 443 | accent_variant |
| `atençäo` | 4 | `atenção` | 395 | accent_variant |
| `atê` | 4 | `até` | 3,663 | accent_variant |
| `aviao` | 4 | `avião` | 226 | unaccented |
| `bébé` | 4 | `bebé` | 333 | accent_variant |
| `comecar` | 4 | `começar` | 1,802 | unaccented |
| `cà` | 4 | `cá` | 1,895 | accent_variant |
| `diferenca` | 4 | `diferença` | 270 | unaccented |
| `doenca` | 4 | `doença` | 136 | unaccented |
| `estacao` | 4 | `estação` | 275 | unaccented |
| `estaçäo` | 4 | `estação` | 275 | accent_variant |
| `fantastico` | 4 | `fantástico` | 285 | unaccented |
| `gênero` | 4 | `género` | 111 | accent_variant |
| `lider` | 4 | `líder` | 91 | unaccented |
| `missao` | 4 | `missão` | 315 | unaccented |
| `màximo` | 4 | `máximo` | 251 | accent_variant |
| `necessario` | 4 | `necessário` | 236 | unaccented |
| `pa` | 4 | `pá` | 700 | unaccented |
| `qué` | 4 | `que` | 93,293 | accent_variant |
| `razäo` | 4 | `razão` | 1,250 | accent_variant |
| `reputacao` | 4 | `reputação` | 85 | unaccented |
| `responsavel` | 4 | `responsável` | 258 | unaccented |
| `simpatico` | 4 | `simpático` | 257 | unaccented |
| `solucäo` | 4 | `solução` | 117 | accent_variant |
| `sì` | 4 | `si` | 1,376 | accent_variant |
| `tecnología` | 4 | `tecnologia` | 136 | accent_variant |
| `très` | 4 | `três` | 1,454 | accent_variant |
| `util` | 4 | `útil` | 145 | unaccented |
| `atômico` | 3 | `atómico` | 61 | accent_variant |
| `california` | 3 | `califórnia` | 97 | unaccented |
| `cardiaco` | 3 | `cardíaco` | 95 | unaccented |
| `consciencia` | 3 | `consciência` | 128 | unaccented |
| `cále` | 3 | `cale` | 171 | accent_variant |
| `côr` | 3 | `cor` | 145 | accent_variant |
| `daquí` | 3 | `daqui` | 1,659 | accent_variant |
| `dôr` | 3 | `dor` | 378 | accent_variant |
| `egoista` | 3 | `egoísta` | 60 | unaccented |
| `engracado` | 3 | `engraçado` | 289 | unaccented |
| `fe` | 3 | `fé` | 150 | unaccented |
| `importancia` | 3 | `importância` | 113 | unaccented |
| `inutil` | 3 | `inútil` | 160 | unaccented |
| `irmao` | 3 | `irmão` | 926 | unaccented |
| `juíz` | 3 | `juiz` | 147 | accent_variant |
| `ligaçäo` | 3 | `ligação` | 203 | accent_variant |
| `lêr` | 3 | `ler` | 543 | accent_variant |
| `mã` | 3 | `ma` | 15,059 | accent_variant |
| `náo` | 3 | `não` | 74,246 | accent_variant |
| `nú` | 3 | `nu` | 86 | accent_variant |
| `paciencia` | 3 | `paciência` | 86 | unaccented |
| `prisäo` | 3 | `prisão` | 270 | accent_variant |
| `prá` | 3 | `pra` | 290 | accent_variant |
| `relatorio` | 3 | `relatório` | 258 | unaccented |
| `ridiculo` | 3 | `ridículo` | 195 | unaccented |
| `senao` | 3 | `senão` | 289 | unaccented |
| `situacao` | 3 | `situação` | 507 | unaccented |
| `situacão` | 3 | `situação` | 507 | accent_variant |
| `sí` | 3 | `si` | 1,376 | accent_variant |
| `tú` | 3 | `tu` | 24,400 | accent_variant |
| `unico` | 3 | `único` | 1,072 | unaccented |
| `çada` | 3 | `cada` | 881 | accent_variant |
| `çomo` | 3 | `como` | 13,854 | accent_variant |
| `çá` | 3 | `cá` | 1,895 | accent_variant |
| `amêndoim` | 2 | `amendoim` | 42 | accent_variant |
| `açucar` | 2 | `açúcar` | 136 | accent_variant |
| `capitao` | 2 | `capitão` | 586 | unaccented |
| `chao` | 2 | `chão` | 384 | unaccented |
| `chäo` | 2 | `chão` | 384 | accent_variant |
| `civilizacao` | 2 | `civilização` | 46 | unaccented |
| `combóio` | 2 | `comboio` | 404 | accent_variant |
| `comissao` | 2 | `comissão` | 178 | unaccented |
| `crème` | 2 | `creme` | 55 | accent_variant |
| `cêrebro` | 2 | `cérebro` | 240 | accent_variant |
| `destruír` | 2 | `destruir` | 519 | accent_variant |
| `digressao` | 2 | `digressão` | 51 | unaccented |
| `disponivel` | 2 | `disponível` | 47 | unaccented |
| `doêr` | 2 | `doer` | 135 | accent_variant |
| `díficil` | 2 | `difícil` | 579 | accent_variant |
| `edificio` | 2 | `edifício` | 311 | unaccented |
| `emergencia` | 2 | `emergência` | 176 | unaccented |
| `emprestimo` | 2 | `empréstimo` | 43 | unaccented |
| `episodio` | 2 | `episódio` | 66 | unaccented |
| `essencia` | 2 | `essência` | 115 | unaccented |
| `estupido` | 2 | `estúpido` | 536 | unaccented |
| `faräo` | 2 | `faraó` | 69 | accent_variant |
| `fodê` | 2 | `fode` | 56 | accent_variant |
| `fraulein` | 2 | `fräulein` | 42 | unaccented |
| `frío` | 2 | `frio` | 344 | accent_variant |
| `galaxia` | 2 | `galáxia` | 49 | unaccented |
| `gas` | 2 | `gás` | 119 | unaccented |
| `genevieve` | 2 | `geneviève` | 50 | unaccented |
| `gracas` | 2 | `graças` | 254 | unaccented |
| `hipotese` | 2 | `hipótese` | 341 | unaccented |
| `impressâo` | 2 | `impressão` | 160 | accent_variant |
| `incrivel` | 2 | `incrível` | 163 | unaccented |
| `informaçäo` | 2 | `informação` | 437 | accent_variant |
| `intencao` | 2 | `intenção` | 83 | unaccented |
| `interrogatorio` | 2 | `interrogatório` | 48 | unaccented |
| `licenca` | 2 | `licença` | 489 | unaccented |
| `maría` | 2 | `maria` | 110 | accent_variant |
| `moisês` | 2 | `moisés` | 175 | accent_variant |
| `nâo` | 2 | `não` | 74,246 | accent_variant |
| `opiniao` | 2 | `opinião` | 239 | unaccented |
| `orgão` | 2 | `órgão` | 52 | accent_variant |
| `pao` | 2 | `pão` | 70 | unaccented |
| `paträo` | 2 | `patrão` | 205 | accent_variant |
| `pensäo` | 2 | `pensão` | 47 | accent_variant |
| `politica` | 2 | `política` | 141 | unaccented |
| `posicao` | 2 | `posição` | 343 | unaccented |
| `prisao` | 2 | `prisão` | 270 | unaccented |
| `profissäo` | 2 | `profissão` | 41 | accent_variant |
| `proposito` | 2 | `propósito` | 149 | unaccented |
| `razoavel` | 2 | `razoável` | 105 | unaccented |
| `refeicao` | 2 | `refeição` | 86 | unaccented |
| `reuniao` | 2 | `reunião` | 170 | unaccented |
| `ràpido` | 2 | `rápido` | 680 | accent_variant |
| `sabado` | 2 | `sábado` | 165 | unaccented |
| `saudavel` | 2 | `saudável` | 79 | unaccented |
| `socio` | 2 | `sócio` | 62 | unaccented |
| `solitaria` | 2 | `solitária` | 56 | unaccented |
| `venus` | 2 | `vénus` | 51 | unaccented |
| `çentro` | 2 | `centro` | 235 | accent_variant |
| `éxito` | 2 | `êxito` | 56 | accent_variant |
| `óbviamente` | 2 | `obviamente` | 90 | accent_variant |
| `admiravel` | 1 | `admirável` | 23 | unaccented |
| `agitaçäo` | 1 | `agitação` | 21 | accent_variant |
| `alemäo` | 1 | `alemão` | 196 | accent_variant |
| `algúm` | 1 | `algum` | 4,682 | accent_variant |
| `ambulancia` | 1 | `ambulância` | 77 | unaccented |
| `atmósfera` | 1 | `atmosfera` | 26 | accent_variant |
| `avanco` | 1 | `avanço` | 25 | unaccented |
| `bebâdo` | 1 | `bêbado` | 123 | accent_variant |
| `biblia` | 1 | `bíblia` | 48 | unaccented |
| `botanico` | 1 | `botânico` | 27 | unaccented |
| `botánico` | 1 | `botânico` | 27 | accent_variant |
| `británico` | 1 | `britânico` | 116 | accent_variant |
| `brônco` | 1 | `bronco` | 28 | accent_variant |
| `calíbre` | 1 | `calibre` | 23 | accent_variant |
| `camâra` | 1 | `câmara` | 265 | accent_variant |
| `cançäo` | 1 | `canção` | 170 | accent_variant |
| `cemiterio` | 1 | `cemitério` | 77 | unaccented |
| `centimetro` | 1 | `centímetro` | 60 | unaccented |
| `chapeu` | 1 | `chapéu` | 214 | unaccented |
| `ciencia` | 1 | `ciência` | 103 | unaccented |
| `classico` | 1 | `clássico` | 53 | unaccented |
| `cocô` | 1 | `coco` | 28 | accent_variant |
| `comentario` | 1 | `comentário` | 49 | unaccented |
| `competicao` | 1 | `competição` | 31 | unaccented |
| `confortavel` | 1 | `confortável` | 79 | unaccented |
| `confusao` | 1 | `confusão` | 98 | unaccented |
| `confusäo` | 1 | `confusão` | 98 | accent_variant |
| `consideracao` | 1 | `consideração` | 20 | unaccented |
| `construcao` | 1 | `construção` | 61 | unaccented |
| `construçäo` | 1 | `construção` | 61 | accent_variant |
| `construír` | 1 | `construir` | 294 | accent_variant |
| `criacao` | 1 | `criação` | 46 | unaccented |
| `crianca` | 1 | `criança` | 893 | unaccented |
| `cámara` | 1 | `câmara` | 265 | accent_variant |
| `cãmara` | 1 | `câmara` | 265 | accent_variant |
| `cäo` | 1 | `cão` | 600 | accent_variant |
| `cêdo` | 1 | `cedo` | 291 | accent_variant |
| `cómo` | 1 | `como` | 13,854 | accent_variant |
| `côco` | 1 | `coco` | 28 | accent_variant |
| `decisao` | 1 | `decisão` | 189 | unaccented |
| `decisäo` | 1 | `decisão` | 189 | accent_variant |
| `depôr` | 1 | `depor` | 49 | accent_variant |
| `des` | 1 | `dês` | 45 | unaccented |
| `desagradavel` | 1 | `desagradável` | 126 | unaccented |
| `descontraír` | 1 | `descontrair` | 42 | accent_variant |
| `destrocar` | 1 | `destroçar` | 34 | unaccented |
| `direcao` | 1 | `direção` | 220 | unaccented |
| `discussao` | 1 | `discussão` | 85 | unaccented |
| `disposiçäo` | 1 | `disposição` | 21 | accent_variant |
| `diúrno` | 1 | `diurno` | 120 | accent_variant |
| `duzia` | 1 | `dúzia` | 90 | unaccented |
| `dár` | 1 | `dar` | 8,060 | accent_variant |
| `dé` | 1 | `de` | 63,425 | accent_variant |
| `dónde` | 1 | `donde` | 28 | accent_variant |
| `energía` | 1 | `energia` | 178 | accent_variant |
| `epoca` | 1 | `época` | 96 | unaccented |
| `escritorio` | 1 | `escritório` | 316 | unaccented |
| `espaco` | 1 | `espaço` | 231 | unaccented |
| `esplendido` | 1 | `esplêndido` | 29 | unaccented |
| `esqueçer` | 1 | `esquecer` | 1,492 | accent_variant |
| `esquêmá` | 1 | `esquema` | 35 | accent_variant |
| `estavel` | 1 | `estável` | 26 | unaccented |
| `estomago` | 1 | `estômago` | 34 | unaccented |
| `estâo` | 1 | `estäo` | 38 | accent_variant |
| `estûpido` | 1 | `estúpido` | 536 | accent_variant |
| `execucäo` | 1 | `execução` | 26 | accent_variant |
| `explosao` | 1 | `explosão` | 76 | unaccented |
| `farao` | 1 | `faraó` | 69 | unaccented |
| `federacão` | 1 | `federação` | 38 | accent_variant |
| `ficcao` | 1 | `ficção` | 34 | unaccented |
| `figãdo` | 1 | `fígado` | 34 | accent_variant |
| `fiél` | 1 | `fiel` | 27 | accent_variant |
| `flôr` | 1 | `flor` | 206 | accent_variant |
| `fôda` | 1 | `foda` | 676 | accent_variant |
| `genero` | 1 | `género` | 111 | unaccented |
| `genio` | 1 | `génio` | 107 | unaccented |
| `ginàsio` | 1 | `ginásio` | 21 | accent_variant |
| `gratis` | 1 | `grátis` | 42 | unaccented |
| `guarniçäo` | 1 | `guarnição` | 61 | accent_variant |
| `habil` | 1 | `hábil` | 27 | unaccented |
| `helicoptero` | 1 | `helicóptero` | 49 | unaccented |
| `histôria` | 1 | `história` | 1,086 | accent_variant |
| `homicidio` | 1 | `homicídio` | 172 | unaccented |
| `häo-de` | 1 | `hão-de` | 20 | accent_variant |
| `imaginacao` | 1 | `imaginação` | 90 | unaccented |
| `inclusivé` | 1 | `inclusive` | 27 | accent_variant |
| `incrívelmente` | 1 | `incrivelmente` | 27 | accent_variant |
| `informacao` | 1 | `informação` | 437 | unaccented |
| `infracao` | 1 | `infração` | 26 | unaccented |
| `inocencia` | 1 | `inocência` | 63 | unaccented |
| `invencao` | 1 | `invenção` | 32 | unaccented |
| `irmaõzinho` | 1 | `irmãozinho` | 28 | accent_variant |
| `irmä` | 1 | `irmã` | 418 | accent_variant |
| `itém` | 1 | `item` | 44 | accent_variant |
| `juizo` | 1 | `juízo` | 101 | unaccented |
| `jã` | 1 | `já` | 8,429 | accent_variant |
| `libano` | 1 | `líbano` | 22 | unaccented |
| `licao` | 1 | `lição` | 98 | unaccented |
| `licôr` | 1 | `licor` | 31 | accent_variant |
| `limao` | 1 | `limão` | 25 | unaccented |
| `localizacao` | 1 | `localização` | 35 | unaccented |
| `maldiçäo` | 1 | `maldição` | 68 | accent_variant |
| `mamâ` | 1 | `mamã` | 190 | accent_variant |
| `mare` | 1 | `maré` | 25 | unaccented |
| `maximo` | 1 | `máximo` | 251 | unaccented |
| `mexico` | 1 | `méxico` | 51 | unaccented |
| `milhäo` | 1 | `milhão` | 796 | accent_variant |
| `misericordia` | 1 | `misericórdia` | 35 | unaccented |
| `misterio` | 1 | `mistério` | 41 | unaccented |
| `miuda` | 1 | `miúda` | 343 | unaccented |
| `mobilía` | 1 | `mobília` | 27 | accent_variant |
| `municao` | 1 | `munição` | 46 | unaccented |
| `mágia` | 1 | `magia` | 26 | accent_variant |
| `mãma` | 1 | `mamã` | 190 | accent_variant |
| `mãr` | 1 | `mar` | 160 | accent_variant |
| `mörder` | 1 | `morder` | 209 | accent_variant |
| `ne` | 1 | `né` | 26 | unaccented |
| `nã` | 1 | `na` | 9,725 | accent_variant |
| `nõ` | 1 | `no` | 11,671 | accent_variant |
| `observacao` | 1 | `observação` | 30 | unaccented |
| `ocasiao` | 1 | `ocasião` | 69 | unaccented |
| `ontém` | 1 | `ontem` | 538 | accent_variant |
| `opcao` | 1 | `opção` | 136 | unaccented |
| `opiniäo` | 1 | `opinião` | 239 | accent_variant |
| `organizacao` | 1 | `organização` | 86 | unaccented |
| `organizaçäo` | 1 | `organização` | 86 | accent_variant |
| `ovô` | 1 | `ovo` | 323 | accent_variant |
| `parabens` | 1 | `parabéns` | 263 | unaccented |
| `passaro` | 1 | `pássaro` | 58 | unaccented |
| `pedaco` | 1 | `pedaço` | 153 | unaccented |
| `pelotäo` | 1 | `pelotão` | 20 | accent_variant |
| `perdäo` | 1 | `perdão` | 202 | accent_variant |
| `perdõe` | 1 | `perdoe` | 96 | accent_variant |
| `perguntár` | 1 | `perguntar` | 988 | accent_variant |
| `periodo` | 1 | `período` | 88 | unaccented |
| `perjurio` | 1 | `perjúrio` | 33 | unaccented |
| `perú` | 1 | `peru` | 26 | accent_variant |
| `pesadêlo` | 1 | `pesadelo` | 99 | accent_variant |
| `politico` | 1 | `político` | 59 | unaccented |
| `polícial` | 1 | `policial` | 74 | accent_variant |
| `porqué` | 1 | `porque` | 5,364 | accent_variant |
| `posiçäo` | 1 | `posição` | 343 | accent_variant |
| `possívelmente` | 1 | `possivelmente` | 94 | accent_variant |
| `preco` | 1 | `preço` | 367 | unaccented |
| `predio` | 1 | `prédio` | 87 | unaccented |
| `preferivél` | 1 | `preferível` | 23 | accent_variant |
| `preocupaçäo` | 1 | `preocupação` | 94 | accent_variant |
| `presenca` | 1 | `presença` | 91 | unaccented |
| `pressao` | 1 | `pressão` | 92 | unaccented |
| `pressäo` | 1 | `pressão` | 92 | accent_variant |
| `provavel` | 1 | `provável` | 69 | unaccented |
| `própriamente` | 1 | `propriamente` | 103 | accent_variant |
| `prôximo` | 1 | `próximo` | 742 | accent_variant |
| `pánico` | 1 | `pânico` | 115 | accent_variant |
| `pésó` | 1 | `peso` | 109 | accent_variant |
| `põ` | 1 | `pó` | 55 | accent_variant |
| `põr` | 1 | `por` | 17,245 | accent_variant |
| `questäo` | 1 | `questão` | 565 | accent_variant |
| `reacao` | 1 | `reação` | 116 | unaccented |
| `realizaçao` | 1 | `realização` | 61 | accent_variant |
| `recordacao` | 1 | `recordação` | 235 | unaccented |
| `recordaçäo` | 1 | `recordação` | 235 | accent_variant |
| `refeiçäo` | 1 | `refeição` | 86 | accent_variant |
| `regiao` | 1 | `região` | 49 | unaccented |
| `relaçao` | 1 | `relação` | 371 | accent_variant |
| `reporter` | 1 | `repórter` | 26 | unaccented |
| `resistencia` | 1 | `resistência` | 49 | unaccented |
| `revoluçâo` | 1 | `revolução` | 56 | accent_variant |
| `romantico` | 1 | `romântico` | 66 | unaccented |
| `roupao` | 1 | `roupão` | 29 | unaccented |
| `russia` | 1 | `rússia` | 38 | unaccented |
| `río` | 1 | `rio` | 285 | accent_variant |
| `sabäo` | 1 | `sabão` | 157 | accent_variant |
| `sanduiche` | 1 | `sanduíche` | 37 | unaccented |
| `secçäo` | 1 | `secção` | 80 | accent_variant |
| `sentenca` | 1 | `sentença` | 42 | unaccented |
| `sessao` | 1 | `sessão` | 39 | unaccented |
| `solitario` | 1 | `solitário` | 39 | unaccented |
| `solucao` | 1 | `solução` | 117 | unaccented |
| `sotão` | 1 | `sótão` | 32 | accent_variant |
| `superficie` | 1 | `superfície` | 43 | unaccented |
| `súper` | 1 | `super` | 29 | accent_variant |
| `telemovel` | 1 | `telemóvel` | 78 | unaccented |
| `territôrio` | 1 | `território` | 48 | accent_variant |
| `titúlo` | 1 | `título` | 66 | accent_variant |
| `todavía` | 1 | `todavia` | 49 | accent_variant |
| `tostao` | 1 | `tostão` | 28 | unaccented |
| `traducao` | 1 | `tradução` | 149 | unaccented |
| `traducão` | 1 | `tradução` | 149 | accent_variant |
| `traduçao` | 1 | `tradução` | 149 | accent_variant |
| `tragedia` | 1 | `tragédia` | 35 | unaccented |
| `traicao` | 1 | `traição` | 53 | unaccented |
| `traiçäo` | 1 | `traição` | 53 | accent_variant |
| `traquéia` | 1 | `traqueia` | 21 | accent_variant |
| `trovao` | 1 | `trovão` | 29 | unaccented |
| `troväo` | 1 | `trovão` | 29 | accent_variant |
| `trêm` | 1 | `trem` | 40 | accent_variant |
| `técnologia` | 1 | `tecnologia` | 136 | accent_variant |
| `uisque` | 1 | `uísque` | 67 | unaccented |
| `vagao` | 1 | `vagão` | 75 | unaccented |
| `versao` | 1 | `versão` | 99 | unaccented |
| `vicío` | 1 | `vício` | 27 | accent_variant |
| `visao` | 1 | `visão` | 177 | unaccented |
| `vocé` | 1 | `você` | 10,982 | accent_variant |
| `vádio` | 1 | `vadio` | 158 | accent_variant |
| `vâo` | 1 | `vao` | 22 | accent_variant |
| `vóz` | 1 | `voz` | 279 | accent_variant |
| `àfrica` | 1 | `áfrica` | 39 | accent_variant |
| `àmen` | 1 | `ámen` | 25 | accent_variant |
| `ái` | 1 | `aí` | 2,608 | accent_variant |
| `álias` | 1 | `aliás` | 117 | accent_variant |
| `áquele` | 1 | `aquele` | 2,571 | accent_variant |
| `ão` | 1 | `ao` | 7,457 | accent_variant |
| `çapítulo` | 1 | `capítulo` | 72 | accent_variant |
| `çiência` | 1 | `ciência` | 103 | accent_variant |
| `çlaro` | 1 | `claro` | 2,713 | accent_variant |
| `çleveland` | 1 | `cleveland` | 21 | accent_variant |
| `éi` | 1 | `ei` | 475 | accent_variant |
| `ñão` | 1 | `não` | 74,246 | accent_variant |
| `ôca` | 1 | `oca` | 23 | accent_variant |
| `ú` | 1 | `u` | 60 | accent_variant |

</details>


