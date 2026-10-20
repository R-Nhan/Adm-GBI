# Cadastro de localização da irmandade – CCB Guanambi/BA

Formulário web em que cada casa informa onde mora e quantos irmãos frequentam, por faixa de idade e comum congregação. A posição da casa é marcada na **planta cadastral da prefeitura**, com imagem de satélite por baixo. As respostas vão para uma Planilha Google e depois alimentam o mapa de calor das próximas casas de oração.

## Mapa da irmandade (`site/Mapa/mapa.html`)

Página separada, na mesma pasta `site`, que lê a planilha e mostra **um ponto por família** sobre a planta e o satélite:

- **cor** = comum congregação (cada comum tem sempre a mesma cor; "Outra" é cinza);
- **tamanho** = quantas pessoas da casa frequentam (ou só uma faixa de idade, escolhida no painel);
- legenda com contagem por comum, que também liga e desliga cada comum;
- opção de **mancha de densidade** (sombra cinza) somando as comuns visíveis;
- passar o mouse ou tocar num ponto mostra comum, faixas de idade e santa ceia. Sem nome, telefone nem endereço.

**Para ativar com dados reais** (uma vez):

1. No editor do Apps Script, abra **Configurações do projeto > Propriedades do script** e crie `CHAVE_MAPA` com uma chave longa e secreta.
2. Cole o arquivo `apps-script-cadastro.gs` inteiro de novo no Apps Script e faça **Implantar > Gerenciar implantações > editar (lápis) > Nova versão**. A URL não muda.
3. Gere os arquivos (comando abaixo) e publique a pasta `site`.
4. Abra `.../Mapa/mapa.html` e digite a chave. Ela fica guardada no navegador de quem digitou.

### Casas de oração e raio de cobertura

Cada casa de oração entra no mapa como uma casinha na cor da sua comum, com um círculo tracejado de **500 m, 1 km, 1,5 km ou 2 km** (a escolha é no painel; a distância é em linha reta). O painel também mostra, por comum, a parte das famílias que mora dentro do raio da própria casa, e quantas famílias ficam fora do raio de **qualquer** casa (dá para circulá-las no mapa).

As casas ficam em `gerador/casas.json`, uma linha por casa (uma comum pode ter mais de uma):

```
[
  {"comum": "São Sebastião", "nome": "", "lat": -14.2300, "lon": -42.7600},
  {"comum": "Brasília", "nome": "Casa de oração do Brasília", "lat": -14.2150, "lon": -42.7700}
]
```

`comum` deve ser escrito como na lista do formulário; `nome` é opcional (sem ele, aparece o nome da comum). Para descobrir `lat` e `lon`: abra `Mapa/mapa.html#casas`, escolha a comum, toque sobre a casa de oração no mapa e use **Copiar linha**; cole dentro de `casas.json` (separe as linhas por vírgula) e rode o comando de gerar. Também serve copiar as coordenadas do Google Maps (botão direito sobre o local). Para achar pelo endereço, há `gerador/localizar_casas.py`, que procura a rua e o número na planta (instruções no topo do arquivo).

Casas cadastradas (outubro/2026): 4 batem com o número da planta e com o rótulo "Congregação Cristã" da própria planta (São Francisco, Brasília, Morada Nova, Nova Central). Central Antiga e São Sebastião batem com o número da planta. A da Alvorada (Rua Palmira Cardoso, 52) é estimada: a planta só vai até o nº 216 dessa rua, e o 52 foi prolongado ~165 m pela direção da rua. A José Humberto Nunes (Rua Eujácio de Araújo Braga, 207, antiga **Rua H**) bate com o nº 207 da "Rua H – Lot. José Humberto Nunes" da planta. Atenção: no Google Maps, essa busca cai na *Rua Dr. José Humberto Nunes*, perto do nº 930, que é outro lugar (cerca de 2,7 km dali).

Sem a chave certa o Apps Script não devolve nada. Para ver o mapa com dados sorteados, sem planilha, acrescente `#demo` ao endereço (`Mapa/mapa.html#demo`).

## Estrutura da pasta

| Pasta / arquivo | O que é |
|---|---|
| `site/index.html` | Entrada do GitHub Pages; encaminha para o formulário. |
| `site/Forms/index.html` | **O formulário pronto.** |
| `site/Mapa/mapa.html` | **O mapa da irmandade**, que lê a planilha com a chave de acesso. |
| `apps-script-cadastro.gs` | Código do Apps Script da planilha que recebe os cadastros. |
| `fonte/MAPA_GUANAMBI.dwg` | Planta cadastral original da prefeitura (AutoCAD R14). |
| `gerador/data.json` | Planta já convertida: quadras, lotes, ruas, números das casas. |
| `dados/textrot.json` | Rotação e altura dos textos do DWG, usadas para traçar as ruas. |
| `gerador/` | Scripts que transformam a planta no formulário. |

## Configuração atual

- **Planilha (Apps Script):** `https://script.google.com/macros/s/AKfycbwJpe-ysXfj967E8RDQ8V8Z45z_ouElR9lqPThVeuY0aBxwgqvebvXu-ja4Pv-C7fpCkw/exec`
- **Datum da planta:** a planta da prefeitura está em **SAD69 / UTM 23S**. Para alinhar com o satélite e gerar latitude/longitude corretas (SIRGAS 2000/WGS84), o formulário aplica o deslocamento `SAT_OFF = [44.2, 43.7]` metros (leste, norte). Esse valor foi conferido sobre a imagem no Centro e no lado leste.
- **Satélite:** Esri World Imagery, gratuito com atribuição. Em Guanambi, a imagem vai até o zoom 18.
- **Painel de calibração:** abra o site com `#ajuste` no final do link.

## Publicar no GitHub Pages

O workflow `.github/workflows/deploy-pages.yml` publica automaticamente a pasta `site` quando houver um envio para as branches `main` ou `master`.

1. Envie este projeto para um repositório no GitHub.
2. No repositório, abra **Settings > Pages**.
3. Em **Build and deployment > Source**, escolha **GitHub Actions**.
4. Abra a aba **Actions** e acompanhe o workflow **Publicar no GitHub Pages**.

A raiz do endereço publicado abre o formulário. O mapa administrativo fica em `Mapa/mapa.html`.
Mantenha `CHAVE_MAPA` somente nas propriedades privadas do Apps Script; não coloque a chave no HTML nem no repositório do GitHub.

## Mudar só o texto, as perguntas ou o visual

1. Edite `gerador/template.html` (formulário) ou `gerador/template_mapa.html` (mapa).
2. Gere os dois, rodando dentro da pasta `gerador`:
   ```
   python3 assemble.py ../site "URL_DO_APPS_SCRIPT" 44.2 43.7
   ```
3. Envie as alterações ao GitHub; o workflow publicará a pasta `site`.

Se mudar ou acrescentar perguntas, atualize também a lista `COLUNAS` no `apps-script-cadastro.gs`. Depois apague a aba "Cadastros" da planilha, para o cabeçalho ser recriado.

## Quando a prefeitura mandar uma planta nova (DWG)

Precisa de Python 3 com `pyproj` e do **LibreDWG** (programa `dwgread`; a versão usada foi a 0.13.3).

```
dwgread -O GeoJSON -o mapa.geojson NOVO_MAPA.dwg
dwgread -O JSON    -o mapa.json    NOVO_MAPA.dwg
python3 gerador/extrair_rotacao.py mapa.json textrot.json
python3 gerador/build.py mapa.geojson gerador/data.json textrot.json
cd gerador && python3 assemble.py ../site "URL_DO_APPS_SCRIPT" 44.2 43.7
```

Os nomes das ruas vêm da camada **TEXTODERUA** do DWG, e os números das casas vêm dos textos numéricos dos lotes. Se a nova planta vier em SIRGAS 2000, e não em SAD69, use `0 0` no lugar de `44.2 43.7`. Para conferir, use o painel `#ajuste`.

## Como o formulário acha a casa

- Cada rótulo de nome de rua vira um trecho de rua, usando a posição, a direção e o comprimento do texto. Os trechos com o mesmo nome são ligados entre si.
- Quando os números das casas continuam em linha depois do último rótulo, a rua é prolongada até onde eles vão.
- Ao digitar o número, o formulário procura esse número a até 30 m da rua escolhida. Se não achar, posiciona entre os números vizinhos. Se também não der, pede para a pessoa tocar no mapa.
- O campo `origem_posicao` da planilha registra como cada ponto foi obtido: número achado na planta, aproximado, marcado no mapa ou GPS.

## Colunas da planilha

data_hora, responsavel, telefone, zona, rua, numero, complemento, bairro, localidade_rural, referencia, comum, freq_0_11, freq_12_17, freq_18_29, freq_30_59, freq_60_mais, total_frequentam, qtd_santa_ceia, qtd_sem_santa_ceia, outra_comum, outra_comum_qtd, latitude, longitude, utm_e, utm_n (SIRGAS 2000), origem_posicao, telefone_repetido.
