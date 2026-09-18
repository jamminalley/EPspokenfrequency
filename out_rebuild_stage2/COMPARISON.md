# Stage 2 comparison: fixes vs original `out/` and the stage 1 baseline

Stage 1 is a **baseline**, not a target. The original pipeline's
scripts were lost; this is a reconstruction from the README's
description, and the README turned out to be wrong in at least one
place (see Tokenizer below). Divergence is reported, not tuned away.

- Lemmatizer backend: `gated`
- Enclitic splitting: `False`
- simplemma: `2.0.0`
- Corpus: `data/pt.txt.gz` (full)

## Tokenizer fingerprint

The original README published three totals. They are the only
independent check on the reconstructed tokenizer.

| metric | original | this run | delta | delta % |
|---|---:|---:|---:|---:|
| `lines` | 118,469,705 | 118,469,705 | +0 | +0.000% |
| `tokens` | 623,920,347 | 623,911,554 | -8,793 | -0.001% |
| `types` | 955,446 | 960,588 | +5,142 | +0.538% |
| `tokens_per_line` | 5.2665 | 5.2664 | -0.0001 | -0.001% |

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
- **Shared lemmas: 3,896 (77.9% of the original)**
- Jaccard: 0.638
- **Spearman rho on shared lemmas: 0.9490**
- pos_guess agreement: 97.2% over 3,896 shared lemmas
- MWEs: original 179, rebuild 189, shared 170

> pos_guess rules were fitted to `out/` (see scripts/fit_postag.py),
> so this agreement figure is partly circular and is not evidence
> that the tagger is good -- only that it reproduces the original,
> mistakes included.

### Largest rank movements (shared lemmas)

| lemma | original | rebuild | move |
|---|---:|---:|---:|
| `pedido` | 4851 | 1026 | -3,825 |
| `saída` | 4557 | 795 | -3,762 |
| `exato` | 4754 | 1146 | -3,608 |
| `complicar` | 1386 | 4918 | +3,532 |
| `entrevista` | 4996 | 1682 | -3,314 |
| `direto` | 4490 | 1177 | -3,313 |
| `sentido` | 3865 | 555 | -3,310 |
| `exceto` | 4514 | 1208 | -3,306 |
| `partida` | 4703 | 1416 | -3,287 |
| `vista` | 3864 | 638 | -3,226 |
| `unido` | 1209 | 4399 | +3,190 |
| `errar` | 3435 | 366 | -3,069 |
| `entrega` | 4710 | 1729 | -2,981 |
| `pilar` | 2042 | 4993 | +2,951 |
| `cuidado` | 3253 | 337 | -2,916 |
| `luta` | 3626 | 719 | -2,907 |
| `procura` | 3297 | 396 | -2,901 |
| `proteção` | 4219 | 1350 | -2,869 |
| `reserva` | 4564 | 1713 | -2,851 |
| `ajuda` | 3141 | 312 | -2,829 |
| `ato` | 4313 | 1485 | -2,828 |
| `espera` | 2949 | 168 | -2,781 |
| `projeto` | 4034 | 1259 | -2,775 |
| `presa` | 4255 | 1490 | -2,765 |
| `espetáculo` | 3729 | 1056 | -2,673 |

### In the original, missing from the rebuild

`me`, `te`, `lhe`, `mim`, `quer`, `deus`, `ti`, `tinha`, `sr`, `preciso`, `vão`, `desculpa`, `vá`, `vê`, `volta`, `fez`, `vos`, `acha`, `obrigado`, `óptimo`, `gosto`, `feito`, `dr`, `lamento`, `visto`, `errado`, `calma`, `amo`, `sai`, `john`, `pais`, `penso`, `exactamente`, `estivar`, `certa`, `toma`, `preso`, `sam`, `mr`, `dê`, `deve`, `esteve`, `esposo`, `olhe`, `trouxe`, `chamado`, `michael`, `natal`, `jesus`, `tira`, `vale`, `charlie`, `peter`, `perdido`, `fbi`, `miúdos`, `david`, `joe`, `vário`, `aberto`

_1,104 total._

### New in the rebuild, absent from the original

`a`, `o que`, `no`, `na`, `é que`, `é o`, `que não`, `o meu`, `eles`, `tua`, `nos`, `é um`, `é uma`, `pelo`, `por isso`, `pela`, `num`, `disso`, `fora`, `contigo`, `numa`, `todos os`, `parte`, `nas`, `deles`, `com ele`, `sozinho`, `todas as`, `cara`, `da minha`, `desta`, `filha`, `neste`, `disto`, `ei`, `deixa-me`, `nisso`, `deste`, `irmã`, `dá-me`, `nesta`, `na minha`, `tuas`, `pelos`, `diz-me`, `dizem`, `fazê-lo`, `amiga`, `connosco`, `h`, `esposa`, `cala-te`, `mente`, `lembras-te`, `pelas`, `vai-te`, `á`, `graças`, `amo-te`, `deixe-me`

_1,104 total._

## Band: ranks 5001-10000

- Entries: original 5,000, rebuild 5,000
- **Shared lemmas: 3,155 (63.1% of the original)**
- Jaccard: 0.461
- **Spearman rho on shared lemmas: 0.9312**
- pos_guess agreement: 98.2% over 3,155 shared lemmas
- MWEs: original 111, rebuild 89, shared 88

> pos_guess rules were fitted to `out/` (see scripts/fit_postag.py),
> so this agreement figure is partly circular and is not evidence
> that the tagger is good -- only that it reproduces the original,
> mistakes included.

### Largest rank movements (shared lemmas)

| lemma | original | rebuild | move |
|---|---:|---:|---:|
| `bordar` | 5475 | 9996 | +4,521 |
| `lisonjeado` | 9460 | 5630 | -3,830 |
| `disputar` | 5208 | 9031 | +3,823 |
| `marine` | 5613 | 9136 | +3,523 |
| `detalhar` | 9771 | 6359 | -3,412 |
| `destroçado` | 9185 | 5818 | -3,367 |
| `emocionado` | 9593 | 6282 | -3,311 |
| `ria` | 8772 | 5482 | -3,290 |
| `estratégico` | 6805 | 9939 | +3,134 |
| `postar` | 5458 | 8557 | +3,099 |
| `colorir` | 8436 | 5349 | -3,087 |
| `enjoado` | 8561 | 5479 | -3,082 |
| `farmacêutico` | 5743 | 8781 | +3,038 |
| `içar` | 5079 | 8115 | +3,036 |
| `empolgado` | 9802 | 6847 | -2,955 |
| `empenhado` | 9268 | 6366 | -2,902 |
| `derivar` | 5692 | 8517 | +2,825 |
| `desempregado` | 8693 | 5937 | -2,756 |
| `fiar` | 8698 | 5955 | -2,743 |
| `cilindro` | 7191 | 9922 | +2,731 |
| `codificar` | 8017 | 5332 | -2,685 |
| `absolver` | 9213 | 6565 | -2,648 |
| `costurar` | 6306 | 8939 | +2,633 |
| `marquês` | 7391 | 9979 | +2,588 |
| `minhoca` | 8855 | 6302 | -2,553 |

### In the original, missing from the rebuild

`fulano`, `dificil`, `broche`, `fundador`, `riso`, `solidão`, `mamilo`, `t-shirt`, `atormentar`, `nadia`, `refúgio`, `complicação`, `presta atenção`, `riscar`, `cubo`, `encanto`, `phoenix`, `bónus`, `extensão`, `naval`, `embrulhar`, `hambúrguer`, `molhado`, `vapor`, `pierce`, `drive`, `salvamento`, `percurso`, `orientar`, `daniels`, `tirado`, `elite`, `câmbio`, `mills`, `obrigatório`, `andrea`, `técnica`, `garrett`, `beneficiar`, `hans`, `vermelhas`, `stevens`, `river`, `contabilista`, `jeitoso`, `jurisdição`, `impressionado`, `bebes`, `invocar`, `inocência`, `intervir`, `magoado`, `perfurar`, `paula`, `douglas`, `fatiar`, `passarinhar`, `necessariamente`, `judicial`, `hastings`

_1,845 total._

### New in the rebuild, absent from the original

`disse-nos`, `vejo-o`, `all`, `doméstica`, `sacerdote`, `camponês`, `peço-lhe`, `atualizar`, `chamam-lhe`, `homenzinho`, `leve-me`, `perguntou-me`, `impedi-lo`, `lotaria`, `deixe-nos`, `divertir-me`, `arquiteto`, `del`, `deixei-o`, `divertir-te`, `girl`, `arranjar-te`, `embebedar`, `condicionado`, `vire-se`, `manter-me`, `recolha`, `intimidar`, `armadilhas`, `tornei-me`, `réu`, `apanhá-los`, `vitima`, `botar`, `anfitrião`, `ajoelhar`, `revolta`, `achado`, `alistar`, `pombo`, `surpreso`, `ajudou-me`, `bárbaro`, `despedir-me`, `solta-me`, `ã`, `deixe-a`, `overdose`, `ouviste-me`, `diga-nos`, `seleção`, `ensinar-te`, `emenda`, `atualização`, `devo-te`, `conte-me`, `pêlo`, `encontra-se`, `perdê-lo`, `vê-las`

_1,845 total._

## Against the stage 1 baseline

Stage 1 reproduced the original pipeline including its flaws.
These figures isolate what the stage 2 fixes actually changed.

### Band: ranks 1-5000

- Shared with baseline: 4,223 (84.5%)
- Spearman rho vs baseline: 0.9622

**Dropped by the fixes** (in stage 1, gone in stage 2):

`uma`, `me`, `te`, `pelar`, `mim`, `sua`, `quer`, `deus`, `ti`, `sr`, `lhe`, `preciso`, `desculpa`, `volta`, `acha`, `obrigado`, `gosto`, `feito`, `óptimo`, `dr`, `lamento`, `primeira`, `distar`, `nossos`, `calmar`, `umas`, `jack`, `john`, `vos`, `pais`, `exactamente`, `papar`, `certa`, `amigar`, `preso`, `sam`, `deve`, `tinha`, `vê`, `irar`, `visto`, `esposar`, `chamado`, `michael`, `natal`, `vale`, `frank`, `jesus`, `tira`, `perdido`, `fbi`, `david`, `amo`, `verter`, `aberto`, `era`, `leve`, `bebido`, `entendido`, `esquerda`

_777 total._

**Promoted by the fixes** (new in stage 2):

`a`, `da`, `no`, `na`, `eles`, `dos`, `nos`, `das`, `pela`, `fora`, `às`, `contigo`, `numa`, `nas`, `aos`, `sozinho`, `cara`, `causa`, `disto`, `ei`, `deixa-me`, `irmã`, `nesta`, `pelos`, `falta`, `dizem`, `fazê-lo`, `amiga`, `connosco`, `esposa`, `cala-te`, `papá`, `mente`, `lembras-te`, `pelas`, `graças`, `deixe-me`, `ver-te`, `nessa`, `disse-me`, `naquela`, `pra`, `sinto-me`, `direita`, `destes`, `sente-se`, `senta-te`, `disse-te`, `avó`, `rio`, `dizer-me`, `lembro-me`, `chama-se`, `dizer-te`, `destas`, `parece-me`, `ias`, `céus`, `diga-me`, `termos`

_777 total._

### Band: ranks 5001-10000

- Shared with baseline: 3,575 (71.5%)
- Spearman rho vs baseline: 0.9427

**Dropped by the fixes** (in stage 1, gone in stage 2):

`ingrediente`, `definição`, `porno`, `altar`, `concorrer`, `chef`, `cigano`, `deduzir`, `honestidade`, `indefeso`, `gaiola`, `desfeito`, `reconsiderar`, `ponto final`, `anual`, `recomendação`, `concreto`, `cultivar`, `furar`, `thor`, `monitorizar`, `válido`, `esplêndido`, `deu-te`, `bébé`, `hudson`, `terramoto`, `política`, `rodado`, `patente`, `flechar`, `formal`, `insecto`, `restrito`, `isolado`, `claque`, `feriado`, `escotilha`, `aleatório`, `cortina`, `nasa`, `artilharia`, `marijuana`, `desobedecer`, `ooh`, `congelado`, `manda`, `morango`, `dvd`, `irlanda`, `facebook`, `indicação`, `húmido`, `precipitar`, `pontaria`, `fêmeo`, `bernard`, `moore`, `poeira`, `frankenstein`

_1,425 total._

**Promoted by the fixes** (new in stage 2):

`disse-nos`, `vejo-o`, `doméstica`, `sacerdote`, `camponês`, `peço-lhe`, `atualizar`, `chamam-lhe`, `homenzinho`, `leve-me`, `perguntou-me`, `impedi-lo`, `deixe-nos`, `divertir-me`, `arquiteto`, `deixei-o`, `divertir-te`, `arranjar-te`, `embebedar`, `condicionado`, `vire-se`, `manter-me`, `intimidar`, `armadilhas`, `tornei-me`, `réu`, `apanhá-los`, `vitima`, `botar`, `anfitrião`, `ajoelhar`, `revolta`, `achado`, `alistar`, `pombo`, `ajudou-me`, `pecador`, `despedir-me`, `solta-me`, `deixe-a`, `fundar`, `ouviste-me`, `diga-nos`, `seleção`, `ensinar-te`, `emenda`, `atualização`, `devo-te`, `conte-me`, `encontra-se`, `perdê-lo`, `naqueles`, `arranja-me`, `apanhar-te`, `bicha`, `larga-a`, `meter-se`, `ética`, `disputa`, `refere-se`

_1,425 total._

## Lemmatization conventions (eval/conventions.md)

Each convention remaps surfaces from one headword to another. Below:
the published entries each one created, grew or protected, and the
former headwords it merged away that were big enough to have been
published on their own (>= 1,449 tokens, the rank-10000 count).

| convention | surfaces remapped | tokens moved |
|---|---:|---:|
| 1. Contractions are their own entries | 3 | 5,243 |
| 2. Gendered nouns fold into the masculine | 102 | 990,471 |
| 2. (exception) Feminines with their own meaning kept separate | 24 | 49,147 |
| 3. Diminutives stay separate | 1,349 | 49,742 |
| 4. Comparatives are their own lemmas | 4 | 123,094 |
| 5. Spelling-reform variants merge under the post-1990 spelling | 2,399 | 1,584,787 |

### 1. Contractions are their own entries

| entry | rank | tokens gained | from surfaces |
|---|---:|---:|---|
| `noutros` | 7004 | 2,714 | `noutros` |
| `nuns` | 9206 | 1,679 | `nuns` |

### 2. Gendered nouns fold into the masculine

| entry | rank | tokens gained | from surfaces |
|---|---:|---:|---|
| `senhor` | 101 | 237,388 | `se-nho-ras`, `senhora`, `senhoras` |
| `miúdo` | 244 | 126,718 | `miúda`, `miúdas` |
| `menino` | 291 | 153,418 | `menina`, `meninas` |
| `branco` | 520 | 39,434 | `branca` |
| `tio` | 521 | 37,794 | `tia`, `tias` |
| `namorado` | 524 | 61,619 | `namorada`, `namoradas` |
| `advogado` | 608 | 9,924 | `advogada`, `advogadas` |
| `inimigo` | 694 | 3,104 | `inimiga` |
| `parceiro` | 974 | 7,309 | `parceira`, `parceiras` |
| `santo` | 1035 | 18,333 | `santa` |
| `empregado` | 1126 | 17,616 | `empregada`, `empregadas` |
| `companheiro` | 1260 | 4,753 | `companheira`, `companheiras` |
| `prisioneiro` | 1266 | 3,857 | `prisioneira` |
| `vampiro` | 1313 | 3,098 | `vampira` |
| `parvo` | 1376 | 8,488 | `parva`, `parvas` |
| `enfermeiro` | 1452 | 26,853 | `enfermeira`, `enfermeiras` |
| `aluno` | 1502 | 6,176 | `aluna`, `alunas` |
| `liso` | 1522 | 27,045 | `lisa` |
| `senador` | 1523 | 5,134 | `senadora` |
| `escravo` | 1548 | 4,908 | `escrava`, `escravas` |
| `tolo` | 1672 | 5,541 | `tola` |
| `treinador` | 1690 | 1,546 | `treinadora` |
| `prostituto` | 1783 | 22,651 | `prostituta`, `prostitutas` |
| `caçador` | 1787 | 3,160 | `caçadora`, `caçadoras` |
| `sócio` | 1813 | 2,302 | `sócia`, `sócias` |

_41 further published entries affected._

Former headwords merged away: `senhora` (237,388), `menina` (153,418), `miúda` (126,718), `namorada` (61,619), `branca` (39,434), `tia` (37,794), `lisa` (27,045), `enfermeira` (26,853), `prostituta` (22,651), `santa` (18,333), `empregada` (17,616), `solta` (15,018), `viúva` (10,040), `advogada` (9,924), `culpada` (9,242), `serena` (8,596), `parva` (8,488), `sobrinha` (7,834), `moça` (7,577), `parceira` (7,309), `aluna` (6,176), `tola` (5,541), `senadora` (5,134), `escrava` (4,908), `companheira` (4,753)

### 2. (exception) Feminines with their own meaning kept separate

| entry | rank | tokens gained | from surfaces |
|---|---:|---:|---|
| `política` | 1371 | 5,020 | `políticas` |
| `ferida` | 1431 | 31,416 | `ferida`, `feridas` |
| `marinha` | 2189 | 1,163 | `marinhas` |
| `seca` | 2307 | 2,076 | `secas` |
| `matemática` | 2651 | 545 | `matemáticas` |
| `química` | 3005 | 1,873 | `químicas` |
| `lógica` | 3311 | 259 | `lógicas` |
| `solitária` | 3422 | 1,110 | `solitárias` |
| `secundária` | 4229 | 967 | `secundárias` |
| `indiana` | 4556 | 255 | `indianas` |
| `doméstica` | 5008 | 1,003 | `domésticas` |
| `mecânica` | 5813 | 420 | `mecânicas` |
| `brava` | 5863 | 215 | `bravas` |
| `pedrada` | 6614 | 301 | `pedradas` |
| `balística` | 6854 | 38 | `balísticas` |
| `farmacêutica` | 7395 | 661 | `farmacêuticas` |
| `dinâmica` | 8264 | 208 | `dinâmicas` |
| `vitela` | 9664 | 46 | `vitelas` |
| `salvadora` | 9671 | 20 | `salvadoras` |

### 3. Diminutives stay separate

| entry | rank | tokens gained | from surfaces |
|---|---:|---:|---|
| `paizinho` | 4536 | 79 | `paizinhos` |
| `irmãozinho` | 6027 | 87 | `irmãozinhos` |
| `ajudinha` | 6046 | 9 | `ajudinhas` |
| `engraçadinho` | 6185 | 267 | `engraçadinhos` |
| `espertinho` | 6190 | 320 | `espertinhos` |
| `amorzinho` | 6519 | 74 | `amorzinhos` |
| `avozinha` | 7297 | 98 | `avozinhas` |
| `irmãzinha` | 7489 | 57 | `irmãzinhas` |
| `voltinha` | 7953 | 307 | `voltinhas` |
| `carinha` | 8062 | 213 | `carinhas` |
| `calminha` | 8121 | 2,084 | `calminha`, `calminhas` |
| `certinho` | 8562 | 194 | `certinhos` |
| `queridinha` | 8952 | 31 | `queridinhas` |
| `maminha` | 9113 | 1,525 | `maminhas` |
| `pobrezinha` | 9499 | 61 | `pobrezinhas` |
| `filhinha` | 9653 | 41 | `filhinhas` |
| `trabalhinho` | 9706 | 205 | `trabalhinhos` |
| `rabinho` | 9825 | 131 | `rabinhos` |
| `coitadinha` | 9834 | 48 | `coitadinhas` |

Former headwords merged away: `calma` (2,084)

### 4. Comparatives are their own lemmas

| entry | rank | tokens gained | from surfaces |
|---|---:|---:|---|
| `melhor` | 108 | 73,970 | `melhores` |
| `maior` | 367 | 26,512 | `maiores` |
| `pior` | 497 | 15,844 | `piores` |
| `menor` | 1646 | 6,768 | `menores` |

### 5. Spelling-reform variants merge under the post-1990 spelling

| entry | rank | tokens gained | from surfaces |
|---|---:|---:|---|
| `estar` | 8 | 215 | `cta`, `cto`, `pta`, `pto`, `ptá` |
| `ter` | 11 | 49 | `ctem`, `ctemos`, `ptem`, `ptenho`, `pter` |
| `tu` | 24 | 4,821 | `ctu`, `ptu` |
| `gostar` | 97 | 2 | `gospta` |
| `até` | 98 | 23 | `acte`, `apte` |
| `ouvir` | 104 | 1 | `oucça` |
| `parecer` | 109 | 2 | `parecça`, `parecço` |
| `também` | 111 | 12 | `ctb`, `ptb` |
| `matar` | 146 | 2 | `macta` |
| `conhecer` | 150 | 9 | `conhecço` |
| `começar` | 154 | 2 | `comecça`, `comecçou` |
| `pedir` | 199 | 1 | `pecço` |
| `tratar` | 247 | 1 | `ctratará` |
| `desaparecer` | 348 | 2 | `desaparecçam` |
| `coração` | 405 | 4 | `coracção` |
| `exatamente` | 413 | 120,806 | `exactamente` |
| `bater` | 447 | 20 | `bacta` |
| `meter` | 492 | 4 | `mecter` |
| `mentir` | 504 | 2 | `mincto` |
| `informação` | 508 | 4 | `informacção`, `informacções` |
| `escutar` | 515 | 1 | `escuctam` |
| `tio` | 521 | 1 | `ctia` |
| `licença` | 532 | 2 | `licencça` |
| `atenção` | 538 | 6 | `atencção` |
| `relação` | 560 | 30 | `relacção`, `relacções` |

_312 further published entries affected._

Former headwords merged away: `óptimo` (210,265), `exactamente` (120,806), `detective` (53,039), `direcção` (43,880), `acção` (38,235), `espectáculo` (36,027), `excepto` (33,967), `correcto` (33,203), `director` (32,750), `exacto` (28,759), `aspecto` (26,984), `objectivo` (26,959), `projecto` (26,442), `protecção` (26,327), `directamente` (22,104), `directo` (20,818), `acções` (19,752), `acto` (15,507), `espectacular` (14,520), `reacção` (13,363), `inspector` (13,179), `actividade` (11,358), `actor` (10,164), `recepção` (9,995), `objecto` (9,641)


## Gold-set lemmatizer accuracy

Gold set: `eval/lemma_gold.tsv` — 332 scored rows, 68 marked `drop` and excluded

| backend | accuracy | ranks 1-1000 | 1001-10000 | 10001+ |
|---|---:|---:|---:|---:|
| `pipeline, stage 2 (gated)` | **94.6%** | 97.6% | 95.9% | 88.2% |

<details><summary>pipeline, stage 2 (gated): 18 disagreements</summary>

| surface | gold | predicted |
|---|---|---|
| `lo` | `o` | `ele` |
| `procura` | `procurar` | `procura` |
| `vejam` | `ver` | `vir` |
| `estados` | `estado` | `estados` |
| `mentes` | `mentir` | `mente` |
| `numero` | `número` | `numero` |
| `detector` | `detector` | `detetor` |
| `arruinado` | `arruinar` | `arruinado` |
| `quadrados` | `quadrado` | `quadrados` |
| `batidas` | `batida` | `bater` |
| `educados` | `educado` | `educar` |
| `honrados` | `honrado` | `honrar` |
| `sacas` | `sacar` | `saca` |
| `mascarada` | `mascarado` | `mascarar` |
| `bodes` | `bode` | `bodes` |
| `educadas` | `educado` | `educar` |
| `corrompido` | `corromper` | `corrompido` |
| `sâo` | `são` | `ser` |

</details>


## Quality report

# Quality report: suspect duplicate entries

Stage 2. Gate: FAIL on suspects.

**205 suspects**: diacritic 40, inflected 165

| kind | entry | rank | duplicate of | rank | detail |
|---|---|---:|---|---:|---|
| inflected | `tuas` | 462 | `tua` | 88 | tuas is a regular inflection of tua |
| diacritic | `á` | 716 | `a` | 4 | both fold to 'a' |
| inflected | `graças` | 737 | `graça` | 1131 | graças is a regular inflection of graça |
| diacritic | `näo` | 1008 | `não` | 5 | both fold to 'nao' |
| inflected | `céus` | 1076 | `céu` | 890 | céus is a regular inflection of céu |
| inflected | `termos` | 1102 | `termo` | 3162 | termos is a regular inflection of termo |
| inflected | `histórias` | 1320 | `história` | 310 | histórias is a regular inflection of história |
| inflected | `estados` | 1383 | `estado` | 423 | estados is a regular inflection of estado |
| inflected | `unidos` | 1384 | `unido` | 4399 | unidos is a regular inflection of unido |
| inflected | `bem-vindos` | 1590 | `bem-vindo` | 1120 | bem-vindos is a regular inflection of bem-vindo |
| inflected | `eis` | 1741 | `ei` | 371 | eis is a regular inflection of ei |
| inflected | `operações` | 2071 | `operação` | 1096 | operações is a regular inflection of operação |
| diacritic | `idéia` | 2165 | `ideia` | 228 | both fold to 'ideia' |
| inflected | `juntas` | 2227 | `junta` | 4490 | juntas is a regular inflection of junta |
| inflected | `secretos` | 2565 | `secreto` | 1080 | secretos is a regular inflection of secreto |
| inflected | `vê-los` | 2570 | `vê-lo` | 842 | vê-los is a regular inflection of vê-lo |
| inflected | `diz-lhes` | 2745 | `diz-lhe` | 1163 | diz-lhes is a regular inflection of diz-lhe |
| inflected | `certos` | 2773 | `certo` | 116 | certos is a regular inflection of certo |
| inflected | `anjos` | 2798 | `anjo` | 1925 | anjos is a regular inflection of anjo |
| inflected | `ondas` | 2835 | `onda` | 2569 | ondas is a regular inflection of onda |
| diacritic | `hã` | 2956 | `ha` | 2746 | both fold to 'ha' |
| inflected | `jóias` | 2976 | `jóia` | 5409 | jóias is a regular inflection of jóia |
| inflected | `sombras` | 3077 | `sombra` | 2136 | sombras is a regular inflection of sombra |
| inflected | `federais` | 3090 | `federal` | 1972 | federais is a regular inflection of federal |
| inflected | `sais` | 3156 | `sal` | 2437 | sais is a regular inflection of sal |
| inflected | `guerreiros` | 3196 | `guerreiro` | 2371 | guerreiros is a regular inflection of guerreiro |
| inflected | `deixá-los` | 3198 | `deixá-lo` | 1648 | deixá-los is a regular inflection of deixá-lo |
| inflected | `reis` | 3300 | `rei` | 489 | reis is a regular inflection of rei |
| inflected | `ajudá-los` | 3417 | `ajudá-lo` | 1235 | ajudá-los is a regular inflection of ajudá-lo |
| inflected | `dar-lhes` | 3464 | `dar-lhe` | 1128 | dar-lhes is a regular inflection of dar-lhe |
| inflected | `dizer-lhes` | 3526 | `dizer-lhe` | 1204 | dizer-lhes is a regular inflection of dizer-lhe |
| inflected | `matá-los` | 3649 | `matá-lo` | 1332 | matá-los is a regular inflection of matá-lo |
| inflected | `namorados` | 3670 | `namorado` | 524 | namorados is a regular inflection of namorado |
| inflected | `guerras` | 3716 | `guerra` | 377 | guerras is a regular inflection of guerra |
| inflected | `levá-los` | 3795 | `levá-lo` | 1533 | levá-los is a regular inflection of levá-lo |
| inflected | `disse-lhes` | 3881 | `disse-lhe` | 1151 | disse-lhes is a regular inflection of disse-lhe |
| inflected | `nações` | 3987 | `nação` | 2220 | nações is a regular inflection of nação |
| inflected | `putas` | 4061 | `puta` | 730 | putas is a regular inflection of puta |
| inflected | `santos` | 4098 | `santo` | 1035 | santos is a regular inflection of santo |
| inflected | `fuzileiros` | 4117 | `fuzileiro` | 5687 | fuzileiros is a regular inflection of fuzileiro |
| inflected | `encontrá-los` | 4347 | `encontrá-lo` | 1620 | encontrá-los is a regular inflection of encontrá-lo |
| diacritic | `nâo` | 4361 | `não` | 5 | both fold to 'nao' |
| diacritic | `vôo` | 4404 | `voo` | 1219 | both fold to 'voo' |
| inflected | `gajas` | 4416 | `gaja` | 3568 | gajas is a regular inflection of gaja |
| diacritic | `aquí` | 4446 | `aqui` | 39 | both fold to 'aqui' |
| inflected | `maravilhas` | 4547 | `maravilha` | 2401 | maravilhas is a regular inflection of maravilha |
| inflected | `galinhas` | 4551 | `galinha` | 2522 | galinhas is a regular inflection of galinha |
| inflected | `deixa-os` | 4564 | `deixa-o` | 1904 | deixa-os is a regular inflection of deixa-o |
| inflected | `tê-los` | 4574 | `tê-lo` | 1516 | tê-los is a regular inflection of tê-lo |
| inflected | `deixem-nos` | 4588 | `deixem-no` | 4189 | deixem-nos is a regular inflection of deixem-no |
| inflected | `diga-lhes` | 4665 | `diga-lhe` | 2419 | diga-lhes is a regular inflection of diga-lhe |
| inflected | `damas` | 4673 | `dama` | 2875 | damas is a regular inflection of dama |
| inflected | `fazê-los` | 4811 | `fazê-lo` | 562 | fazê-los is a regular inflection of fazê-lo |
| diacritic | `cú` | 4861 | `cu` | 1420 | both fold to 'cu' |
| inflected | `donuts` | 4868 | `donut` | 7232 | donuts is a regular inflection of donut |
| diacritic | `bébé` | 4908 | `bebé` | 441 | both fold to 'bebe' |
| inflected | `armadilhas` | 5081 | `armadilha` | 1909 | armadilhas is a regular inflection of armadilha |
| inflected | `apanhá-los` | 5094 | `apanhá-lo` | 2721 | apanhá-los is a regular inflection of apanhá-lo |
| diacritic | `ã` | 5129 | `a` | 4 | both fold to 'a' |
| diacritic | `pêlo` | 5198 | `pelo` | 144 | both fold to 'pelo' |
| inflected | `vê-las` | 5204 | `vê-la` | 1343 | vê-las is a regular inflection of vê-la |
| inflected | `zombies` | 5305 | `zombie` | 5313 | zombies is a regular inflection of zombie |
| inflected | `bonecas` | 5351 | `boneca` | 2965 | bonecas is a regular inflection of boneca |
| inflected | `dá-lhes` | 5394 | `dá-lhe` | 1496 | dá-lhes is a regular inflection of dá-lhe |
| inflected | `avós` | 5446 | `avó` | 1028 | avós is a regular inflection of avó |
| inflected | `buscá-los` | 5613 | `buscá-lo` | 2399 | buscá-los is a regular inflection of buscá-lo |
| inflected | `vi-os` | 5806 | `vi-o` | 2255 | vi-os is a regular inflection of vi-o |
| inflected | `gregos` | 5858 | `grego` | 3443 | gregos is a regular inflection of grego |
| inflected | `peles` | 5872 | `pele` | 1169 | peles is a regular inflection of pele |
| inflected | `conhecê-los` | 5890 | `conhecê-lo` | 1626 | conhecê-los is a regular inflection of conhecê-lo |
| inflected | `drones` | 5891 | `drone` | 6029 | drones is a regular inflection of drone |
| inflected | `espelhos` | 5900 | `espelho` | 2190 | espelhos is a regular inflection of espelho |
| inflected | `laboratórios` | 5919 | `laboratório` | 1189 | laboratórios is a regular inflection of laboratório |
| diacritic | `nã` | 6025 | `na` | 38 | both fold to 'na' |
| inflected | `mostrar-lhes` | 6154 | `mostrar-lhe` | 3185 | mostrar-lhes is a regular inflection of mostrar-lhe |
| diacritic | `pêlos` | 6196 | `pelos` | 526 | both fold to 'pelos' |
| inflected | `pêlos` | 6196 | `pêlo` | 5198 | pêlos is a regular inflection of pêlo |
| inflected | `chuis` | 6202 | `chui` | 6382 | chuis is a regular inflection of chui |
| inflected | `indústrias` | 6285 | `indústria` | 3470 | indústrias is a regular inflection of indústria |
| inflected | `mantê-los` | 6325 | `mantê-lo` | 3462 | mantê-los is a regular inflection of mantê-lo |
| inflected | `costumes` | 6336 | `costume` | 2610 | costumes is a regular inflection of costume |
| inflected | `amadores` | 6342 | `amador` | 4475 | amadores is a regular inflection of amador |
| inflected | `leva-os` | 6428 | `leva-o` | 3340 | leva-os is a regular inflection of leva-o |
| inflected | `futuros` | 6452 | `futuro` | 597 | futuros is a regular inflection of futuro |
| diacritic | `â` | 6471 | `a` | 4 | both fold to 'a' |
| inflected | `câmeras` | 6475 | `câmera` | 3854 | câmeras is a regular inflection of câmera |
| inflected | `elfos` | 6482 | `elfo` | 7696 | elfos is a regular inflection of elfo |
| inflected | `escuros` | 6532 | `escuro` | 1246 | escuros is a regular inflection of escuro |
| inflected | `gangues` | 6710 | `gangue` | 4818 | gangues is a regular inflection of gangue |
| inflected | `tirá-los` | 6747 | `tirá-lo` | 3061 | tirá-los is a regular inflection of tirá-lo |
| inflected | `les` | 6776 | `le` | 4449 | les is a regular inflection of le |
| diacritic | `sózinho` | 6795 | `sozinho` | 308 | both fold to 'sozinho' |
| diacritic | `demônio` | 6892 | `demónio` | 1400 | both fold to 'demonio' |
| inflected | `pô-los` | 6930 | `pô-lo` | 3186 | pô-los is a regular inflection of pô-lo |
| inflected | `trazê-los` | 6936 | `trazê-lo` | 3485 | trazê-los is a regular inflection of trazê-lo |
| inflected | `usá-los` | 6951 | `usá-lo` | 3032 | usá-los is a regular inflection of usá-lo |
| inflected | `demônios` | 7007 | `demônio` | 6892 | demônios is a regular inflection of demônio |
| inflected | `marines` | 7030 | `marine` | 9136 | marines is a regular inflection of marine |
| inflected | `matem-nos` | 7041 | `matem-no` | 5626 | matem-nos is a regular inflection of matem-no |
| inflected | `dróides` | 7061 | `dróide` | 8322 | dróides is a regular inflection of dróide |
| diacritic | `jà` | 7089 | `já` | 47 | both fold to 'ja' |
| inflected | `tigres` | 7093 | `tigre` | 3192 | tigres is a regular inflection of tigre |
| inflected | `ouvi-los` | 7106 | `ouvi-lo` | 3626 | ouvi-los is a regular inflection of ouvi-lo |
| inflected | `shots` | 7140 | `shot` | 8284 | shots is a regular inflection of shot |
| diacritic | `joia` | 7278 | `jóia` | 5409 | both fold to 'joia' |
| inflected | `digo-lhes` | 7308 | `digo-lhe` | 2559 | digo-lhes is a regular inflection of digo-lhe |
| inflected | `gangs` | 7373 | `gang` | 4580 | gangs is a regular inflection of gang |
| inflected | `boys` | 7506 | `boy` | 4684 | boys is a regular inflection of boy |
| inflected | `levem-nos` | 7507 | `levem-no` | 3372 | levem-nos is a regular inflection of levem-no |
| inflected | `quadrados` | 7514 | `quadrado` | 5429 | quadrados is a regular inflection of quadrado |
| inflected | `servos` | 7517 | `servo` | 4375 | servos is a regular inflection of servo |
| diacritic | `entäo` | 7565 | `então` | 69 | both fold to 'entao' |
| inflected | `robots` | 7615 | `robot` | 4815 | robots is a regular inflection of robot |
| inflected | `quero-os` | 7621 | `quero-o` | 4109 | quero-os is a regular inflection of quero-o |
| inflected | `mostra-lhes` | 7638 | `mostra-lhe` | 5435 | mostra-lhes is a regular inflection of mostra-lhe |
| inflected | `mata-os` | 7655 | `mata-o` | 3264 | mata-os is a regular inflection of mata-o |
| diacritic | `polo` | 7666 | `pólo` | 5969 | both fold to 'polo' |
| inflected | `deixe-os` | 7680 | `deixe-o` | 3911 | deixe-os is a regular inflection of deixe-o |
| inflected | `metanfetaminas` | 7712 | `metanfetamina` | 9521 | metanfetaminas is a regular inflection of metanfetamina |
| inflected | `usá-las` | 7772 | `usá-la` | 3599 | usá-las is a regular inflection of usá-la |
| inflected | `fodidos` | 7779 | `fodido` | 3718 | fodidos is a regular inflection of fodido |
| inflected | `idéias` | 7796 | `idéia` | 2165 | idéias is a regular inflection of idéia |
| inflected | `camisolas` | 7798 | `camisola` | 2831 | camisolas is a regular inflection of camisola |
| inflected | `ofensas` | 7830 | `ofensa` | 3261 | ofensas is a regular inflection of ofensa |
| inflected | `apanhem-nos` | 7841 | `apanhem-no` | 4648 | apanhem-nos is a regular inflection of apanhem-no |
| diacritic | `alí` | 7847 | `ali` | 245 | both fold to 'ali' |
| inflected | `detê-los` | 7870 | `detê-lo` | 5443 | detê-los is a regular inflection of detê-lo |
| inflected | `tirem-nos` | 7882 | `tirem-no` | 4938 | tirem-nos is a regular inflection of tirem-no |
| inflected | `assinaturas` | 7885 | `assinatura` | 3046 | assinaturas is a regular inflection of assinatura |
| inflected | `fritos` | 7912 | `frito` | 2749 | fritos is a regular inflection of frito |
| diacritic | `qué` | 7918 | `que` | 3 | both fold to 'que' |
| inflected | `contar-lhes` | 7973 | `contar-lhe` | 3662 | contar-lhes is a regular inflection of contar-lhe |
| inflected | `registros` | 7992 | `registro` | 7970 | registros is a regular inflection of registro |
| inflected | `salvá-los` | 7995 | `salvá-lo` | 4401 | salvá-los is a regular inflection of salvá-lo |
| diacritic | `gênio` | 8008 | `génio` | 1632 | both fold to 'genio' |
| inflected | `levá-las` | 8023 | `levá-la` | 1992 | levá-las is a regular inflection of levá-la |
| diacritic | `piça` | 8046 | `pica` | 7499 | both fold to 'pica' |
| inflected | `lagos` | 8047 | `lago` | 1746 | lagos is a regular inflection of lago |
| inflected | `voçês` | 8134 | `voçê` | 7640 | voçês is a regular inflection of voçê |
| inflected | `otários` | 8192 | `otário` | 4123 | otários is a regular inflection of otário |
| inflected | `hobbits` | 8276 | `hobbit` | 8039 | hobbits is a regular inflection of hobbit |
| diacritic | `saír` | 8287 | `sair` | 110 | both fold to 'sair' |
| diacritic | `là` | 8340 | `lá` | 59 | both fold to 'la' |
| inflected | `impedi-los` | 8356 | `impedi-lo` | 5039 | impedi-los is a regular inflection of impedi-lo |
| inflected | `escrituras` | 8365 | `escritura` | 8988 | escrituras is a regular inflection of escritura |
| inflected | `chips` | 8402 | `chip` | 3164 | chips is a regular inflection of chip |
| inflected | `t-shirts` | 8425 | `t-shirt` | 4723 | t-shirts is a regular inflection of t-shirt |
| diacritic | `täo` | 8438 | `tão` | 120 | both fold to 'tao' |
| inflected | `tê-las` | 8458 | `tê-la` | 2423 | tê-las is a regular inflection of tê-la |
| inflected | `buscá-las` | 8479 | `buscá-la` | 3064 | buscá-las is a regular inflection of buscá-la |
| diacritic | `prêmio` | 8558 | `prémio` | 1556 | both fold to 'premio' |
| inflected | `segui-los` | 8568 | `segui-lo` | 4898 | segui-los is a regular inflection of segui-lo |
| inflected | `vikings` | 8595 | `viking` | 8378 | vikings is a regular inflection of viking |
| inflected | `egípcios` | 8617 | `egípcio` | 6223 | egípcios is a regular inflection of egípcio |
| inflected | `protegê-los` | 8631 | `protegê-lo` | 4502 | protegê-los is a regular inflection of protegê-lo |
| diacritic | `cirurgiã` | 8666 | `cirurgia` | 1702 | both fold to 'cirurgia' |
| inflected | `fazê-las` | 8677 | `fazê-la` | 3509 | fazê-las is a regular inflection of fazê-la |
| inflected | `dei-lhes` | 8682 | `dei-lhe` | 2793 | dei-lhes is a regular inflection of dei-lhe |
| inflected | `sagrados` | 8704 | `sagrado` | 2020 | sagrados is a regular inflection of sagrado |
| inflected | `super-heróis` | 8846 | `super-herói` | 6444 | super-heróis is a regular inflection of super-herói |
| inflected | `vejo-os` | 8884 | `vejo-o` | 5004 | vejo-os is a regular inflection of vejo-o |
| inflected | `manda-os` | 8921 | `manda-o` | 6426 | manda-os is a regular inflection of manda-o |
| inflected | `fá-los` | 8926 | `fá-lo` | 1933 | fá-los is a regular inflection of fá-lo |
| inflected | `quecas` | 8956 | `queca` | 4705 | quecas is a regular inflection of queca |
| inflected | `areias` | 8984 | `areia` | 2332 | areias is a regular inflection of areia |
| inflected | `mantém-nos` | 8999 | `mantém-no` | 6697 | mantém-nos is a regular inflection of mantém-no |
| inflected | `beijinhos` | 9021 | `beijinho` | 7623 | beijinhos is a regular inflection of beijinho |
| inflected | `recordes` | 9049 | `recorde` | 3326 | recordes is a regular inflection of recorde |
| inflected | `põe-nos` | 9086 | `põe-no` | 6341 | põe-nos is a regular inflection of põe-no |
| inflected | `totós` | 9130 | `totó` | 5634 | totós is a regular inflection of totó |
| inflected | `apanhámo-los` | 9149 | `apanhámo-lo` | 4903 | apanhámo-los is a regular inflection of apanhámo-lo |
| diacritic | `mäe` | 9226 | `mãe` | 125 | both fold to 'mae' |
| inflected | `dou-lhes` | 9231 | `dou-lhe` | 2655 | dou-lhes is a regular inflection of dou-lhe |
| inflected | `matou-os` | 9245 | `matou-o` | 4172 | matou-os is a regular inflection of matou-o |
| inflected | `águias` | 9271 | `águia` | 3850 | águias is a regular inflection of águia |
| inflected | `touros` | 9322 | `touro` | 4458 | touros is a regular inflection of touro |
| inflected | `ninjas` | 9356 | `ninja` | 5206 | ninjas is a regular inflection of ninja |
| diacritic | `provávelmente` | 9380 | `provavelmente` | 565 | both fold to 'provavelmente' |
| inflected | `fazer-lhes` | 9385 | `fazer-lhe` | 2259 | fazer-lhes is a regular inflection of fazer-lhe |
| inflected | `convencê-los` | 9407 | `convencê-lo` | 5805 | convencê-los is a regular inflection of convencê-lo |
| diacritic | `sí` | 9417 | `si` | 259 | both fold to 'si' |
| diacritic | `prá` | 9436 | `pra` | 847 | both fold to 'pra' |
| diacritic | `encontrámo-nos` | 9459 | `encontramo-nos` | 2358 | both fold to 'encontramo-nos' |
| inflected | `bem-vindas` | 9461 | `bem-vinda` | 2354 | bem-vindas is a regular inflection of bem-vinda |
| diacritic | `sím` | 9462 | `sim` | 33 | both fold to 'sim' |
| inflected | `mos` | 9477 | `mo` | 2684 | mos is a regular inflection of mo |
| diacritic | `benção` | 9493 | `bênção` | 3478 | both fold to 'bencao' |
| inflected | `conta-lhes` | 9515 | `conta-lhe` | 6393 | conta-lhes is a regular inflection of conta-lhe |
| inflected | `relâmpagos` | 9533 | `relâmpago` | 5605 | relâmpagos is a regular inflection of relâmpago |
| inflected | `mandá-los` | 9567 | `mandá-lo` | 5303 | mandá-los is a regular inflection of mandá-lo |
| inflected | `tem-nos` | 9600 | `tem-no` | 8146 | tem-nos is a regular inflection of tem-no |
| inflected | `cus` | 9674 | `cu` | 1420 | cus is a regular inflection of cu |
| inflected | `escoceses` | 9678 | `escocês` | 5968 | escoceses is a regular inflection of escocês |
| inflected | `avisá-los` | 9681 | `avisá-lo` | 6105 | avisá-los is a regular inflection of avisá-lo |
| inflected | `detetores` | 9708 | `detetor` | 5769 | detetores is a regular inflection of detetor |
| inflected | `tira-os` | 9741 | `tira-o` | 4679 | tira-os is a regular inflection of tira-o |
| inflected | `indianos` | 9763 | `indiano` | 6595 | indianos is a regular inflection of indiano |
| inflected | `deixá-las` | 9792 | `deixá-la` | 2530 | deixá-las is a regular inflection of deixá-la |
| diacritic | `pênis` | 9802 | `pénis` | 2673 | both fold to 'penis' |
| inflected | `chamá-los` | 9838 | `chamá-lo` | 4288 | chamá-los is a regular inflection of chamá-lo |

_5 further suspects omitted; see the TSV for the full list._


