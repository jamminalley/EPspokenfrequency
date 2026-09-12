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
- **Shared lemmas: 3,932 (78.6% of the original)**
- Jaccard: 0.648
- **Spearman rho on shared lemmas: 0.9552**
- pos_guess agreement: 97.2% over 3,932 shared lemmas
- MWEs: original 179, rebuild 189, shared 170

> pos_guess rules were fitted to `out/` (see scripts/fit_postag.py),
> so this agreement figure is partly circular and is not evidence
> that the tagger is good -- only that it reproduces the original,
> mistakes included.

### Largest rank movements (shared lemmas)

| lemma | original | rebuild | move |
|---|---:|---:|---:|
| `pedido` | 4851 | 1028 | -3,823 |
| `saída` | 4557 | 796 | -3,761 |
| `complicar` | 1386 | 4926 | +3,540 |
| `entrevista` | 4996 | 1678 | -3,318 |
| `sentido` | 3865 | 555 | -3,310 |
| `partida` | 4703 | 1413 | -3,290 |
| `vista` | 3864 | 637 | -3,227 |
| `unido` | 1209 | 4403 | +3,194 |
| `solto` | 1435 | 4505 | +3,070 |
| `errar` | 3435 | 367 | -3,068 |
| `branca` | 4227 | 1223 | -3,004 |
| `entrega` | 4710 | 1725 | -2,985 |
| `cuidado` | 3253 | 337 | -2,916 |
| `luta` | 3626 | 722 | -2,904 |
| `procura` | 3297 | 396 | -2,901 |
| `reserva` | 4564 | 1708 | -2,856 |
| `ajuda` | 3141 | 311 | -2,830 |
| `espera` | 2949 | 168 | -2,781 |
| `presa` | 4255 | 1483 | -2,772 |
| `escolha` | 3248 | 639 | -2,609 |
| `queixa` | 4549 | 1967 | -2,582 |
| `conversa` | 3131 | 611 | -2,520 |
| `verde` | 3698 | 1179 | -2,519 |
| `sexto` | 2210 | 4709 | +2,499 |
| `cobra` | 4455 | 1968 | -2,487 |

### In the original, missing from the rebuild

`me`, `te`, `lhe`, `mim`, `quer`, `deus`, `ti`, `tinha`, `sr`, `preciso`, `vão`, `desculpa`, `vá`, `vê`, `volta`, `fez`, `vos`, `acha`, `obrigado`, `gosto`, `feito`, `dr`, `lamento`, `visto`, `errado`, `calma`, `amo`, `sai`, `john`, `pais`, `penso`, `estivar`, `certa`, `toma`, `preso`, `sam`, `mr`, `dê`, `deve`, `esteve`, `esposo`, `olhe`, `trouxe`, `chamado`, `michael`, `natal`, `jesus`, `tira`, `vale`, `charlie`, `peter`, `perdido`, `fbi`, `miúdos`, `david`, `joe`, `vário`, `aberto`, `era`, `parabém`

_1,068 total._

### New in the rebuild, absent from the original

`a`, `o que`, `no`, `na`, `é que`, `é o`, `que não`, `o meu`, `eles`, `tua`, `nos`, `é um`, `é uma`, `pelo`, `por isso`, `pela`, `num`, `disso`, `fora`, `contigo`, `numa`, `todos os`, `parte`, `nas`, `deles`, `com ele`, `senhora`, `sozinho`, `todas as`, `cara`, `da minha`, `desta`, `filha`, `neste`, `disto`, `ei`, `deixa-me`, `nisso`, `menina`, `deste`, `irmã`, `dá-me`, `nesta`, `na minha`, `tuas`, `miúda`, `pelos`, `diz-me`, `dizem`, `fazê-lo`, `amiga`, `connosco`, `h`, `esposa`, `cala-te`, `mente`, `lembras-te`, `pelas`, `vai-te`, `á`

_1,068 total._

## Band: ranks 5001-10000

- Entries: original 5,000, rebuild 5,000
- **Shared lemmas: 3,201 (64.0% of the original)**
- Jaccard: 0.471
- **Spearman rho on shared lemmas: 0.9324**
- pos_guess agreement: 98.2% over 3,201 shared lemmas
- MWEs: original 111, rebuild 87, shared 86

> pos_guess rules were fitted to `out/` (see scripts/fit_postag.py),
> so this agreement figure is partly circular and is not evidence
> that the tagger is good -- only that it reproduces the original,
> mistakes included.

### Largest rank movements (shared lemmas)

| lemma | original | rebuild | move |
|---|---:|---:|---:|
| `disputar` | 5208 | 9139 | +3,931 |
| `lisonjeado` | 9460 | 5660 | -3,800 |
| `marine` | 5613 | 9247 | +3,634 |
| `detalhar` | 9771 | 6410 | -3,361 |
| `destroçado` | 9185 | 5862 | -3,323 |
| `ria` | 8772 | 5508 | -3,264 |
| `emocionado` | 9593 | 6331 | -3,262 |
| `postar` | 5458 | 8652 | +3,194 |
| `içar` | 5079 | 8206 | +3,127 |
| `colorir` | 8436 | 5371 | -3,065 |
| `enjoado` | 8561 | 5505 | -3,056 |
| `derivar` | 5692 | 8608 | +2,916 |
| `empolgado` | 9802 | 6911 | -2,891 |
| `empenhado` | 9268 | 6418 | -2,850 |
| `costurar` | 6306 | 9045 | +2,739 |
| `moreno` | 5659 | 8392 | +2,733 |
| `desempregado` | 8693 | 5980 | -2,713 |
| `fiar` | 8698 | 5999 | -2,699 |
| `codificar` | 8017 | 5354 | -2,663 |
| `absolver` | 9213 | 6625 | -2,588 |
| `minhoca` | 8855 | 6353 | -2,502 |
| `coxa` | 7682 | 5195 | -2,487 |
| `descuidar` | 6631 | 9089 | +2,458 |
| `torrada` | 8305 | 5855 | -2,450 |
| `paralisar` | 5826 | 8269 | +2,443 |

### In the original, missing from the rebuild

`fulano`, `dificil`, `broche`, `fundador`, `riso`, `solidão`, `mamilo`, `t-shirt`, `atormentar`, `nadia`, `refúgio`, `complicação`, `presta atenção`, `riscar`, `cubo`, `encanto`, `phoenix`, `bónus`, `extensão`, `naval`, `embrulhar`, `hambúrguer`, `molhado`, `vapor`, `pierce`, `drive`, `salvamento`, `percurso`, `orientar`, `daniels`, `tirado`, `elite`, `câmbio`, `mills`, `obrigatório`, `andrea`, `técnica`, `garrett`, `beneficiar`, `hans`, `vermelhas`, `stevens`, `river`, `contabilista`, `jeitoso`, `jurisdição`, `impressionado`, `bebes`, `invocar`, `inocência`, `intervir`, `magoado`, `perfurar`, `paula`, `douglas`, `fatiar`, `passarinhar`, `necessariamente`, `judicial`, `hastings`

_1,799 total._

### New in the rebuild, absent from the original

`foi-me`, `ralar`, `pilar`, `dar-vos`, `censurar`, `disse-nos`, `vejo-o`, `all`, `doméstico`, `sacerdote`, `camponês`, `peço-lhe`, `chamam-lhe`, `homenzinho`, `leve-me`, `perguntou-me`, `impedi-lo`, `lotaria`, `deixe-nos`, `divertir-me`, `del`, `deixei-o`, `divertir-te`, `girl`, `arranjar-te`, `embebedar`, `companheira`, `condicionado`, `vire-se`, `manter-me`, `recolha`, `intimidar`, `armadilhas`, `tornei-me`, `réu`, `apanhá-los`, `vitima`, `botar`, `anfitrião`, `ajoelhar`, `revolta`, `achado`, `alistar`, `pombo`, `surpreso`, `ajudou-me`, `bárbaro`, `despedir-me`, `solta-me`, `ã`, `deixe-a`, `overdose`, `ouviste-me`, `diga-nos`, `moço`, `ensinar-te`, `emenda`, `lógico`, `devo-te`, `conte-me`

_1,799 total._

## Against the stage 1 baseline

Stage 1 reproduced the original pipeline including its flaws.
These figures isolate what the stage 2 fixes actually changed.

### Band: ranks 1-5000

- Shared with baseline: 4,262 (85.2%)
- Spearman rho vs baseline: 0.9678

**Dropped by the fixes** (in stage 1, gone in stage 2):

`uma`, `me`, `te`, `pelar`, `mim`, `sua`, `quer`, `deus`, `ti`, `sr`, `lhe`, `preciso`, `desculpa`, `volta`, `acha`, `obrigado`, `gosto`, `feito`, `dr`, `lamento`, `primeira`, `distar`, `nossos`, `calmar`, `umas`, `jack`, `john`, `vos`, `pais`, `papar`, `certa`, `amigar`, `preso`, `sam`, `deve`, `tinha`, `vê`, `irar`, `visto`, `esposar`, `chamado`, `michael`, `natal`, `vale`, `frank`, `jesus`, `tira`, `perdido`, `fbi`, `david`, `amo`, `verter`, `aberto`, `era`, `leve`, `bebido`, `entendido`, `esquerda`, `george`, `james`

_738 total._

**Promoted by the fixes** (new in stage 2):

`a`, `da`, `no`, `na`, `eles`, `dos`, `nos`, `das`, `pela`, `fora`, `às`, `contigo`, `numa`, `nas`, `aos`, `sozinho`, `cara`, `causa`, `disto`, `ei`, `deixa-me`, `menina`, `irmã`, `nesta`, `miúda`, `pelos`, `falta`, `dizem`, `fazê-lo`, `amiga`, `connosco`, `esposa`, `cala-te`, `papá`, `mente`, `lembras-te`, `pelas`, `graças`, `deixe-me`, `ver-te`, `nessa`, `disse-me`, `namorada`, `naquela`, `pra`, `sinto-me`, `direita`, `destes`, `sente-se`, `senta-te`, `disse-te`, `avó`, `rio`, `dizer-me`, `lembro-me`, `chama-se`, `dizer-te`, `destas`, `parece-me`, `ias`

_738 total._

### Band: ranks 5001-10000

- Shared with baseline: 3,627 (72.5%)
- Spearman rho vs baseline: 0.9416

**Dropped by the fixes** (in stage 1, gone in stage 2):

`ingrediente`, `definição`, `porno`, `altar`, `concorrer`, `chef`, `cigano`, `deduzir`, `honestidade`, `indefeso`, `gaiola`, `desfeito`, `reconsiderar`, `ponto final`, `anual`, `recomendação`, `concreto`, `cultivar`, `furar`, `thor`, `monitorizar`, `válido`, `esplêndido`, `deu-te`, `bébé`, `hudson`, `terramoto`, `política`, `rodado`, `patente`, `flechar`, `formal`, `insecto`, `restrito`, `isolado`, `claque`, `feriado`, `escotilha`, `aleatório`, `cortina`, `nasa`, `artilharia`, `marijuana`, `ooh`, `congelado`, `manda`, `morango`, `dvd`, `irlanda`, `facebook`, `indicação`, `húmido`, `precipitar`, `pontaria`, `fêmeo`, `bernard`, `moore`, `poeira`, `frankenstein`, `providenciar`

_1,373 total._

**Promoted by the fixes** (new in stage 2):

`ralar`, `pilar`, `sabotar`, `censurar`, `disse-nos`, `vejo-o`, `doméstico`, `sacerdote`, `camponês`, `peço-lhe`, `chamam-lhe`, `homenzinho`, `leve-me`, `perguntou-me`, `impedi-lo`, `deixe-nos`, `divertir-me`, `deixei-o`, `divertir-te`, `arranjar-te`, `embebedar`, `companheira`, `condicionado`, `vire-se`, `manter-me`, `intimidar`, `armadilhas`, `tornei-me`, `réu`, `apanhá-los`, `vitima`, `botar`, `anfitrião`, `ajoelhar`, `revolta`, `achado`, `alistar`, `pombo`, `ajudou-me`, `pecador`, `despedir-me`, `solta-me`, `deixe-a`, `fundar`, `ouviste-me`, `diga-nos`, `moço`, `ensinar-te`, `emenda`, `lógico`, `devo-te`, `conte-me`, `servo`, `encontra-se`, `bicha`, `perdê-lo`, `naqueles`, `arranja-me`, `apanhar-te`, `neta`

_1,373 total._

## Gold-set lemmatizer accuracy

> **Provisional.** 0 of 400 gold rows carry a human
> verdict. For unreviewed rows the gold falls back to
> `claude_lemma`, a first-pass guess, so these numbers measure
> agreement with that guess rather than accuracy. Fill in
> `jim_lemma` / `jim_verdict` in eval/lemma_gold.tsv to make them
> meaningful.

Gold set: `eval/lemma_gold.tsv` — 400 scored rows

| backend | accuracy | ranks 1-1000 | 1001-10000 | 10001+ |
|---|---:|---:|---:|---:|
| `gated` | **95.0%** | 96.2% | 96.0% | 92.5% |
| `spacy` | **83.8%** | 82.3% | 83.3% | 85.8% |

<details><summary>gated: 20 disagreements</summary>

| surface | gold | predicted |
|---|---|---|
| `lo` | `o` | `ele` |
| `procura` | `procurar` | `procura` |
| `miúda` | `miúdo` | `miúda` |
| `fomos` | `ir` | `ser` |
| `vejam` | `ver` | `vir` |
| `estados` | `estado` | `estados` |
| `ferida` | `ferida` | `ferir` |
| `mentes` | `mentir` | `mente` |
| `numero` | `número` | `numero` |
| `voces` | `você` | `voces` |
| `arruinado` | `arruinar` | `arruinado` |
| `quadrados` | `quadrado` | `quadrados` |
| `educados` | `educado` | `educar` |
| `honrados` | `honrado` | `honrar` |
| `sacas` | `sacar` | `saca` |
| `mascarada` | `mascarado` | `mascarar` |
| `bodes` | `bode` | `bodes` |
| `cientifica` | `científico` | `cientifico` |
| `corrompido` | `corromper` | `corrompido` |
| `sâo` | `são` | `ser` |

</details>

<details><summary>spacy: 65 disagreements</summary>

| surface | gold | predicted |
|---|---|---|
| `ao` | `ao` | `a o` |
| `nos` | `nos` | `nós` |
| `lo` | `o` | `lo` |
| `queres` | `querer` | `queres` |
| `preciso` | `precisar` | `preciso` |
| `vão` | `ir` | `vão` |
| `nas` | `nas` | `em o` |
| `aos` | `aos` | `a o` |
| `achas` | `achar` | `achas` |
| `procura` | `procurar` | `procura` |
| `maior` | `maior` | `grande` |
| `devo` | `dever` | `devo` |
| `armas` | `arma` | `armas` |
| `peço` | `pedir` | `peçar` |
| `encontrei` | `encontrar` | `encontrei` |
| `fique` | `ficar` | `fique` |
| `tinhas` | `ter` | `tinhas` |
| `miúda` | `miúdo` | `miúda` |
| `pare` | `parar` | `pare` |
| `nesse` | `nesse` | `em esse` |
| `fomos` | `ir` | `ser` |
| `saia` | `sair` | `saia` |
| `vejam` | `ver` | `vejam` |
| `agradeço` | `agradecer` | `agradeçar` |
| `cheguei` | `chegar` | `cheguei` |
| `venho` | `vir` | `ver` |
| `estados` | `estado` | `estados` |
| `importas` | `importar` | `importas` |
| `possamos` | `poder` | `possamos` |
| `estejam` | `estar` | `estejam` |
| `abram` | `abrir` | `abram` |
| `garanto` | `garantir` | `garantar` |
| `mentes` | `mentir` | `mente` |
| `naquilo` | `naquilo` | `em aquilo` |
| `avancem` | `avançar` | `avancar` |
| `precisavas` | `precisar` | `precisavas` |
| `saberemos` | `saber` | `sabere` |
| `inglesa` | `inglês` | `inglesa` |
| `numero` | `número` | `numero` |
| `voces` | `você` | `voce` |
| `apanhámo` | `apanhar` | `apanhámo` |
| `punha` | `pôr` | `punha` |
| `insisto` | `insistir` | `insistar` |
| `comam` | `comer` | `comam` |
| `bebido` | `beber` | `bebir` |
| `puderam` | `poder` | `puder` |
| `combinámos` | `combinar` | `combinámos` |
| `pilhas` | `pilha` | `pilhas` |
| `quadrados` | `quadrado` | `quadrados` |
| `disparas` | `disparar` | `dispara` |
| `educados` | `educado` | `educar` |
| `salgado` | `salgado` | `salgar` |
| `atendi` | `atender` | `atendi` |
| `despeçam` | `despedir` | `despeçam` |
| `lavaste` | `lavar` | `lavaste` |
| `sacas` | `sacar` | `saca` |
| `julgavas` | `julgar` | `julgavas` |
| `colabora` | `colaborar` | `colabora` |
| `jure` | `jurar` | `jure` |
| `mascarada` | `mascarado` | `mascarar` |

_5 more._

</details>


## Quality report

# Quality report: suspect duplicate entries

Stage 2. Gate: FAIL on suspects.

**249 suspects**: diacritic 37, inflected 212

| kind | entry | rank | duplicate of | rank | detail |
|---|---|---:|---|---:|---|
| inflected | `nos` | 90 | `no` | 34 | nos is a regular inflection of no |
| inflected | `nas` | 230 | `na` | 38 | nas is a regular inflection of na |
| inflected | `tuas` | 463 | `tua` | 88 | tuas is a regular inflection of tua |
| inflected | `pelos` | 525 | `pelo` | 144 | pelos is a regular inflection of pelo |
| inflected | `pelas` | 701 | `pela` | 184 | pelas is a regular inflection of pela |
| diacritic | `á` | 718 | `a` | 4 | both fold to 'a' |
| inflected | `graças` | 739 | `graça` | 1130 | graças is a regular inflection of graça |
| inflected | `destes` | 985 | `deste` | 410 | destes is a regular inflection of deste |
| diacritic | `näo` | 1010 | `não` | 5 | both fold to 'nao' |
| inflected | `destas` | 1064 | `desta` | 333 | destas is a regular inflection of desta |
| inflected | `céus` | 1075 | `céu` | 893 | céus is a regular inflection of céu |
| inflected | `termos` | 1101 | `termo` | 3148 | termos is a regular inflection of termo |
| inflected | `dessas` | 1250 | `dessa` | 818 | dessas is a regular inflection of dessa |
| inflected | `histórias` | 1315 | `história` | 309 | histórias is a regular inflection of história |
| inflected | `desses` | 1364 | `desse` | 861 | desses is a regular inflection of desse |
| inflected | `estados` | 1378 | `estado` | 424 | estados is a regular inflection of estado |
| inflected | `unidos` | 1379 | `unido` | 4403 | unidos is a regular inflection of unido |
| inflected | `bem-vindos` | 1582 | `bem-vindo` | 1120 | bem-vindos is a regular inflection of bem-vindo |
| inflected | `daqueles` | 1607 | `daquele` | 1234 | daqueles is a regular inflection of daquele |
| inflected | `eis` | 1737 | `ei` | 371 | eis is a regular inflection of ei |
| inflected | `acções` | 2029 | `acção` | 1251 | acções is a regular inflection of acção |
| inflected | `operações` | 2071 | `operação` | 1095 | operações is a regular inflection of operação |
| diacritic | `idéia` | 2160 | `ideia` | 228 | both fold to 'ideia' |
| inflected | `daquelas` | 2177 | `daquela` | 1229 | daquelas is a regular inflection of daquela |
| inflected | `juntas` | 2222 | `junta` | 4492 | juntas is a regular inflection of junta |
| inflected | `nestas` | 2462 | `nesta` | 458 | nestas is a regular inflection of nesta |
| inflected | `nestes` | 2490 | `neste` | 336 | nestes is a regular inflection of neste |
| inflected | `neles` | 2501 | `nele` | 773 | neles is a regular inflection of nele |
| inflected | `secretos` | 2559 | `secreto` | 1078 | secretos is a regular inflection of secreto |
| inflected | `vê-los` | 2563 | `vê-lo` | 844 | vê-los is a regular inflection of vê-lo |
| inflected | `diz-lhes` | 2742 | `diz-lhe` | 1161 | diz-lhes is a regular inflection of diz-lhe |
| inflected | `certos` | 2767 | `certo` | 114 | certos is a regular inflection of certo |
| inflected | `anjos` | 2792 | `anjo` | 1913 | anjos is a regular inflection of anjo |
| inflected | `ondas` | 2828 | `onda` | 2558 | ondas is a regular inflection of onda |
| diacritic | `hã` | 2952 | `ha` | 2743 | both fold to 'ha' |
| inflected | `jóias` | 2974 | `jóia` | 5433 | jóias is a regular inflection of jóia |
| inflected | `sombras` | 3064 | `sombra` | 2131 | sombras is a regular inflection of sombra |
| inflected | `federais` | 3077 | `federal` | 1972 | federais is a regular inflection of federal |
| inflected | `sais` | 3141 | `sal` | 2428 | sais is a regular inflection of sal |
| inflected | `guerreiros` | 3183 | `guerreiro` | 2633 | guerreiros is a regular inflection of guerreiro |
| inflected | `deixá-los` | 3185 | `deixá-lo` | 1644 | deixá-los is a regular inflection of deixá-lo |
| inflected | `reis` | 3287 | `rei` | 491 | reis is a regular inflection of rei |
| inflected | `ajudá-los` | 3405 | `ajudá-lo` | 1231 | ajudá-los is a regular inflection of ajudá-lo |
| inflected | `dar-lhes` | 3451 | `dar-lhe` | 1127 | dar-lhes is a regular inflection of dar-lhe |
| inflected | `dizer-lhes` | 3511 | `dizer-lhe` | 1200 | dizer-lhes is a regular inflection of dizer-lhe |
| inflected | `matá-los` | 3638 | `matá-lo` | 1327 | matá-los is a regular inflection of matá-lo |
| inflected | `namorados` | 3661 | `namorado` | 1001 | namorados is a regular inflection of namorado |
| inflected | `guerras` | 3705 | `guerra` | 375 | guerras is a regular inflection of guerra |
| inflected | `insectos` | 3718 | `insecto` | 4930 | insectos is a regular inflection of insecto |
| inflected | `nessas` | 3725 | `nessa` | 816 | nessas is a regular inflection of nessa |
| inflected | `actos` | 3766 | `acto` | 2401 | actos is a regular inflection of acto |
| inflected | `objectos` | 3778 | `objecto` | 3263 | objectos is a regular inflection of objecto |
| inflected | `levá-los` | 3789 | `levá-lo` | 1525 | levá-los is a regular inflection of levá-lo |
| inflected | `disse-lhes` | 3881 | `disse-lhe` | 1151 | disse-lhes is a regular inflection of disse-lhe |
| inflected | `nesses` | 3945 | `nesse` | 846 | nesses is a regular inflection of nesse |
| inflected | `nações` | 3987 | `nação` | 2215 | nações is a regular inflection of nação |
| inflected | `actividades` | 4027 | `actividade` | 2962 | actividades is a regular inflection of actividade |
| inflected | `putas` | 4064 | `puta` | 732 | putas is a regular inflection of puta |
| inflected | `santos` | 4100 | `santo` | 1478 | santos is a regular inflection of santo |
| inflected | `fuzileiros` | 4120 | `fuzileiro` | 5720 | fuzileiros is a regular inflection of fuzileiro |
| inflected | `detectives` | 4127 | `detective` | 962 | detectives is a regular inflection of detective |
| inflected | `encontrá-los` | 4352 | `encontrá-lo` | 1614 | encontrá-los is a regular inflection of encontrá-lo |
| diacritic | `nâo` | 4367 | `não` | 5 | both fold to 'nao' |
| diacritic | `vôo` | 4408 | `voo` | 1214 | both fold to 'voo' |
| inflected | `gajas` | 4419 | `gaja` | 3556 | gajas is a regular inflection of gaja |
| diacritic | `aquí` | 4447 | `aqui` | 39 | both fold to 'aqui' |
| inflected | `maravilhas` | 4551 | `maravilha` | 2394 | maravilhas is a regular inflection of maravilha |
| inflected | `galinhas` | 4555 | `galinha` | 2515 | galinhas is a regular inflection of galinha |
| inflected | `deixa-os` | 4568 | `deixa-o` | 1902 | deixa-os is a regular inflection of deixa-o |
| inflected | `tê-los` | 4579 | `tê-lo` | 1509 | tê-los is a regular inflection of tê-lo |
| inflected | `deixem-nos` | 4594 | `deixem-no` | 4191 | deixem-nos is a regular inflection of deixem-no |
| inflected | `nelas` | 4603 | `nela` | 1185 | nelas is a regular inflection of nela |
| inflected | `óptimos` | 4617 | `óptimo` | 312 | óptimos is a regular inflection of óptimo |
| inflected | `diga-lhes` | 4674 | `diga-lhe` | 2411 | diga-lhes is a regular inflection of diga-lhe |
| inflected | `damas` | 4683 | `dama` | 2870 | damas is a regular inflection of dama |
| inflected | `fazê-los` | 4820 | `fazê-lo` | 562 | fazê-los is a regular inflection of fazê-lo |
| diacritic | `cú` | 4873 | `cu` | 1417 | both fold to 'cu' |
| inflected | `donuts` | 4880 | `donut` | 7299 | donuts is a regular inflection of donut |
| diacritic | `bébé` | 4917 | `bebé` | 442 | both fold to 'bebe' |
| inflected | `objectivos` | 5093 | `objectivo` | 1608 | objectivos is a regular inflection of objectivo |
| inflected | `actores` | 5095 | `actor` | 3173 | actores is a regular inflection of actor |
| inflected | `armadilhas` | 5096 | `armadilha` | 1906 | armadilhas is a regular inflection of armadilha |
| inflected | `apanhá-los` | 5111 | `apanhá-lo` | 2715 | apanhá-los is a regular inflection of apanhá-lo |
| diacritic | `ã` | 5147 | `a` | 4 | both fold to 'a' |
| diacritic | `pêlo` | 5218 | `pelo` | 144 | both fold to 'pelo' |
| inflected | `vê-las` | 5224 | `vê-la` | 1337 | vê-las is a regular inflection of vê-la |
| inflected | `zombies` | 5327 | `zombie` | 5335 | zombies is a regular inflection of zombie |
| inflected | `àqueles` | 5365 | `àquele` | 3230 | àqueles is a regular inflection of àquele |
| inflected | `bonecas` | 5373 | `boneca` | 2963 | bonecas is a regular inflection of boneca |
| inflected | `dá-lhes` | 5416 | `dá-lhe` | 1490 | dá-lhes is a regular inflection of dá-lhe |
| inflected | `projectos` | 5437 | `projecto` | 1639 | projectos is a regular inflection of projecto |
| inflected | `avós` | 5471 | `avó` | 1030 | avós is a regular inflection of avó |
| inflected | `aspectos` | 5607 | `aspecto` | 1605 | aspectos is a regular inflection of aspecto |
| inflected | `buscá-los` | 5644 | `buscá-lo` | 2391 | buscá-los is a regular inflection of buscá-lo |
| inflected | `vi-os` | 5847 | `vi-o` | 2249 | vi-os is a regular inflection of vi-o |
| inflected | `gregos` | 5898 | `grego` | 3432 | gregos is a regular inflection of grego |
| inflected | `peles` | 5910 | `pele` | 1168 | peles is a regular inflection of pele |
| inflected | `conhecê-los` | 5931 | `conhecê-lo` | 1620 | conhecê-los is a regular inflection of conhecê-lo |
| inflected | `drones` | 5932 | `drone` | 6074 | drones is a regular inflection of drone |
| inflected | `espelhos` | 5942 | `espelho` | 2184 | espelhos is a regular inflection of espelho |
| inflected | `laboratórios` | 5961 | `laboratório` | 1186 | laboratórios is a regular inflection of laboratório |
| diacritic | `nã` | 6070 | `na` | 38 | both fold to 'na' |
| inflected | `noutras` | 6103 | `noutra` | 2363 | noutras is a regular inflection of noutra |
| inflected | `mostrar-lhes` | 6199 | `mostrar-lhe` | 3170 | mostrar-lhes is a regular inflection of mostrar-lhe |
| diacritic | `pêlos` | 6239 | `pelos` | 525 | both fold to 'pelos' |
| inflected | `pêlos` | 6239 | `pêlo` | 5218 | pêlos is a regular inflection of pêlo |
| inflected | `chuis` | 6246 | `chui` | 6434 | chuis is a regular inflection of chui |
| inflected | `indústrias` | 6335 | `indústria` | 3458 | indústrias is a regular inflection of indústria |
| inflected | `tácticas` | 6346 | `táctica` | 4967 | tácticas is a regular inflection of táctica |
| inflected | `mantê-los` | 6377 | `mantê-lo` | 3449 | mantê-los is a regular inflection of mantê-lo |
| inflected | `costumes` | 6389 | `costume` | 2601 | costumes is a regular inflection of costume |
| inflected | `amadores` | 6395 | `amador` | 4476 | amadores is a regular inflection of amador |
| inflected | `leva-os` | 6481 | `leva-o` | 3324 | leva-os is a regular inflection of leva-o |
| inflected | `futuros` | 6507 | `futuro` | 597 | futuros is a regular inflection of futuro |
| diacritic | `â` | 6525 | `a` | 4 | both fold to 'a' |
| inflected | `câmeras` | 6529 | `câmera` | 3852 | câmeras is a regular inflection of câmera |
| inflected | `elfos` | 6536 | `elfo` | 7779 | elfos is a regular inflection of elfo |
| inflected | `infectados` | 6552 | `infectado` | 5298 | infectados is a regular inflection of infectado |
| inflected | `escuros` | 6589 | `escuro` | 1235 | escuros is a regular inflection of escuro |
| inflected | `gangues` | 6773 | `gangue` | 4827 | gangues is a regular inflection of gangue |
| inflected | `tirá-los` | 6813 | `tirá-lo` | 3050 | tirá-los is a regular inflection of tirá-lo |
| inflected | `direcções` | 6817 | `direcção` | 1110 | direcções is a regular inflection of direcção |
| inflected | `les` | 6841 | `le` | 4450 | les is a regular inflection of le |
| diacritic | `sózinho` | 6860 | `sozinho` | 307 | both fold to 'sozinho' |
| diacritic | `demônio` | 6956 | `demónio` | 1398 | both fold to 'demonio' |
| inflected | `pô-los` | 6999 | `pô-lo` | 3171 | pô-los is a regular inflection of pô-lo |
| inflected | `trazê-los` | 7005 | `trazê-lo` | 3471 | trazê-los is a regular inflection of trazê-lo |
| inflected | `usá-los` | 7019 | `usá-lo` | 3023 | usá-los is a regular inflection of usá-lo |
| inflected | `demônios` | 7077 | `demônio` | 6956 | demônios is a regular inflection of demônio |
| inflected | `marines` | 7100 | `marine` | 9247 | marines is a regular inflection of marine |
| inflected | `matem-nos` | 7112 | `matem-no` | 5656 | matem-nos is a regular inflection of matem-no |
| inflected | `dróides` | 7134 | `dróide` | 8415 | dróides is a regular inflection of dróide |
| diacritic | `jà` | 7161 | `já` | 46 | both fold to 'ja' |
| inflected | `tigres` | 7165 | `tigre` | 3179 | tigres is a regular inflection of tigre |
| inflected | `ouvi-los` | 7176 | `ouvi-lo` | 3616 | ouvi-los is a regular inflection of ouvi-lo |
| inflected | `shots` | 7210 | `shot` | 8376 | shots is a regular inflection of shot |
| inflected | `activos` | 7311 | `activo` | 3944 | activos is a regular inflection of activo |
| inflected | `fracturas` | 7346 | `fractura` | 5918 | fracturas is a regular inflection of fractura |
| diacritic | `joia` | 7347 | `jóia` | 5433 | both fold to 'joia' |
| inflected | `eléctricos` | 7351 | `eléctrico` | 5008 | eléctricos is a regular inflection of eléctrico |
| inflected | `digo-lhes` | 7377 | `digo-lhe` | 2552 | digo-lhes is a regular inflection of digo-lhe |
| inflected | `gangs` | 7443 | `gang` | 4586 | gangs is a regular inflection of gang |
| inflected | `espectáculos` | 7535 | `espectáculo` | 1289 | espectáculos is a regular inflection of espectáculo |
| inflected | `boys` | 7578 | `boy` | 4694 | boys is a regular inflection of boy |
| inflected | `levem-nos` | 7579 | `levem-no` | 3359 | levem-nos is a regular inflection of levem-no |
| inflected | `quadrados` | 7586 | `quadrado` | 5134 | quadrados is a regular inflection of quadrado |
| inflected | `servos` | 7589 | `servo` | 5216 | servos is a regular inflection of servo |
| inflected | `numas` | 7624 | `numa` | 221 | numas is a regular inflection of numa |
| inflected | `directos` | 7626 | `directo` | 1970 | directos is a regular inflection of directo |
| diacritic | `entäo` | 7642 | `então` | 69 | both fold to 'entao' |
| inflected | `robots` | 7694 | `robot` | 4824 | robots is a regular inflection of robot |
| inflected | `quero-os` | 7699 | `quero-o` | 4110 | quero-os is a regular inflection of quero-o |
| inflected | `mostra-lhes` | 7718 | `mostra-lhe` | 5458 | mostra-lhes is a regular inflection of mostra-lhe |
| inflected | `mata-os` | 7735 | `mata-o` | 3250 | mata-os is a regular inflection of mata-o |
| diacritic | `polo` | 7746 | `pólo` | 6011 | both fold to 'polo' |
| inflected | `deixe-os` | 7759 | `deixe-o` | 3910 | deixe-os is a regular inflection of deixe-o |
| inflected | `metanfetaminas` | 7797 | `metanfetamina` | 9634 | metanfetaminas is a regular inflection of metanfetamina |
| inflected | `usá-las` | 7858 | `usá-la` | 3590 | usá-las is a regular inflection of usá-la |
| inflected | `fodidos` | 7865 | `fodido` | 3707 | fodidos is a regular inflection of fodido |
| inflected | `idéias` | 7881 | `idéia` | 2160 | idéias is a regular inflection of idéia |
| inflected | `camisolas` | 7883 | `camisola` | 2825 | camisolas is a regular inflection of camisola |
| inflected | `ofensas` | 7919 | `ofensa` | 3247 | ofensas is a regular inflection of ofensa |
| inflected | `apanhem-nos` | 7932 | `apanhem-no` | 4658 | apanhem-nos is a regular inflection of apanhem-no |
| diacritic | `alí` | 7937 | `ali` | 244 | both fold to 'ali' |
| inflected | `detê-los` | 7959 | `detê-lo` | 5468 | detê-los is a regular inflection of detê-lo |
| inflected | `tirem-nos` | 7970 | `tirem-no` | 4947 | tirem-nos is a regular inflection of tirem-no |
| inflected | `assinaturas` | 7974 | `assinatura` | 3035 | assinaturas is a regular inflection of assinatura |
| inflected | `fritos` | 8004 | `frito` | 2745 | fritos is a regular inflection of frito |
| diacritic | `qué` | 8010 | `que` | 3 | both fold to 'que' |
| inflected | `contar-lhes` | 8066 | `contar-lhe` | 3651 | contar-lhes is a regular inflection of contar-lhe |
| inflected | `registros` | 8085 | `registro` | 8063 | registros is a regular inflection of registro |
| inflected | `salvá-los` | 8088 | `salvá-lo` | 4405 | salvá-los is a regular inflection of salvá-lo |
| diacritic | `gênio` | 8101 | `génio` | 1628 | both fold to 'genio' |
| inflected | `levá-las` | 8116 | `levá-la` | 1991 | levá-las is a regular inflection of levá-la |
| diacritic | `piça` | 8139 | `pica` | 7571 | both fold to 'pica' |
| inflected | `lagos` | 8140 | `lago` | 1741 | lagos is a regular inflection of lago |
| inflected | `voçês` | 8225 | `voçê` | 7720 | voçês is a regular inflection of voçê |
| inflected | `actuais` | 8257 | `actual` | 3265 | actuais is a regular inflection of actual |
| inflected | `otários` | 8280 | `otário` | 4125 | otários is a regular inflection of otário |
| inflected | `hobbits` | 8367 | `hobbit` | 8132 | hobbits is a regular inflection of hobbit |
| diacritic | `saír` | 8378 | `sair` | 108 | both fold to 'sair' |
| diacritic | `là` | 8432 | `lá` | 59 | both fold to 'la' |
| inflected | `impedi-los` | 8448 | `impedi-lo` | 5053 | impedi-los is a regular inflection of impedi-lo |
| inflected | `escrituras` | 8457 | `escritura` | 9095 | escrituras is a regular inflection of escritura |
| inflected | `chips` | 8495 | `chip` | 3150 | chips is a regular inflection of chip |
| inflected | `t-shirts` | 8517 | `t-shirt` | 4734 | t-shirts is a regular inflection of t-shirt |
| diacritic | `täo` | 8529 | `tão` | 119 | both fold to 'tao' |
| inflected | `tê-las` | 8549 | `tê-la` | 2415 | tê-las is a regular inflection of tê-la |
| inflected | `buscá-las` | 8570 | `buscá-la` | 3054 | buscá-las is a regular inflection of buscá-la |
| diacritic | `prêmio` | 8653 | `prémio` | 1547 | both fold to 'premio' |
| inflected | `segui-los` | 8662 | `segui-lo` | 4906 | segui-los is a regular inflection of segui-lo |
| inflected | `vikings` | 8691 | `viking` | 8471 | vikings is a regular inflection of viking |
| inflected | `egípcios` | 8712 | `egípcio` | 6266 | egípcios is a regular inflection of egípcio |
| inflected | `protegê-los` | 8727 | `protegê-lo` | 4506 | protegê-los is a regular inflection of protegê-lo |
| diacritic | `cirurgiã` | 8762 | `cirurgia` | 1696 | both fold to 'cirurgia' |
| inflected | `injecções` | 8772 | `injecção` | 4359 | injecções is a regular inflection of injecção |
| inflected | `directores` | 8774 | `director` | 1387 | directores is a regular inflection of director |
| inflected | `fazê-las` | 8775 | `fazê-la` | 3492 | fazê-las is a regular inflection of fazê-la |
| inflected | `dei-lhes` | 8780 | `dei-lhe` | 2787 | dei-lhes is a regular inflection of dei-lhe |
| inflected | `excepções` | 8798 | `excepção` | 3794 | excepções is a regular inflection of excepção |

_49 further suspects omitted; see the TSV for the full list._


