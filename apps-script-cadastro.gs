/**
 * Recebe os cadastros do formulário com mapa e grava numa Planilha Google.
 *
 * Como instalar:
 * 1. Crie uma Planilha Google (com a conta da secretaria) e abra Extensões > Apps Script.
 * 2. Apague o conteúdo e cole este arquivo inteiro. Salve.
 * 3. Implantar > Nova implantação > tipo "App da Web".
 *    Executar como: Eu  |  Quem pode acessar: Qualquer pessoa
 * 4. Autorize, copie a URL que termina em /exec e cole na constante ENDPOINT do arquivo HTML.
 *
 * A planilha fica privada: o formulário só consegue ACRESCENTAR linhas (doPost).
 * O mapa (mapa.html) lê pelo doGet abaixo, que só responde com a CHAVE_MAPA certa e devolve
 * apenas posição, comum e contagens. Nome, telefone, endereço e referência nunca saem da planilha.
 * Cadastre a propriedade de script CHAVE_MAPA e passe seu valor só aos irmãos responsáveis.
 * Depois de mudar este arquivo: Implantar > Gerenciar implantações > editar > Nova versão.
 */
const CHAVE_MAPA = PropertiesService.getScriptProperties().getProperty('CHAVE_MAPA') || '';
const ABA = 'Cadastros';
const COLUNAS = [
  'data_hora', 'responsavel', 'telefone', 'zona', 'rua', 'numero', 'complemento', 'bairro',
  'localidade_rural', 'referencia', 'comum',
  'freq_0_11', 'freq_12_17', 'freq_18_29', 'freq_30_59', 'freq_60_mais', 'total_frequentam',
  'qtd_santa_ceia', 'qtd_sem_santa_ceia', 'outra_comum', 'outra_comum_qtd',
  'latitude', 'longitude', 'utm_e', 'utm_n', 'origem_posicao', 'telefone_repetido', 'endereco_repetido'
];
const IDX = {}; COLUNAS.forEach((c, k) => { IDX[c] = k; });

// Endereço normalizado para comparar cadastros: rua + número + complemento, sem acento, caixa,
// pontuação nem palavras como "Rua"/"Av.". Sem rua ou sem número (s/n), não compara.
const PALAVRAS_RUA = ['rua', 'r', 'av', 'avenida', 'travessa', 'tv', 'praca', 'pc', 'de', 'da', 'do', 'dos', 'das'];
function normEnd(s) {
  return String(s == null ? '' : s).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ').trim();
}
function chaveEndereco(rua, numero, complemento) {
  const r = normEnd(rua).split(' ').filter(p => p && PALAVRAS_RUA.indexOf(p) < 0).join(' ');
  const n = normEnd(numero).replace(/\s/g, '').replace(/^0+(?=\d)/, '');
  if (!r || !n || n === 'sn' || n === '0') return '';
  return r + '|' + n + '|' + normEnd(complemento);
}

// Planilhas criadas antes de uma coluna nova: acrescenta só os títulos que faltam no fim do cabeçalho.
function garantirCabecalho(sh) {
  const falta = COLUNAS.length - sh.getMaxColumns();
  if (falta > 0) sh.insertColumnsAfter(sh.getMaxColumns(), falta);
  const atual = sh.getRange(1, 1, 1, COLUNAS.length).getValues()[0];
  COLUNAS.forEach((c, k) => { if (atual[k] === '') sh.getRange(1, k + 1).setValue(c); });
}

// Linhas da aba, sempre com COLUNAS.length colunas (as que faltarem vêm vazias).
function lerLinhas(sh) {
  const n = sh.getLastRow();
  if (n < 2) return [];
  const larg = Math.min(COLUNAS.length, sh.getLastColumn());
  return sh.getRange(2, 1, n - 1, larg).getValues().map(r => r.concat(Array(COLUNAS.length - larg).fill('')));
}

function doGet(e) {
  const resp = o => ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
  if (!CHAVE_MAPA || !e || !e.parameter || e.parameter.chave !== CHAVE_MAPA) {
    return resp({ ok: false, erro: 'chave' });
  }
  const sh = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(ABA);
  if (!sh || sh.getLastRow() < 2) return resp({ ok: true, dados: [] });
  const v = lerLinhas(sh), i = IDX;
  const dados = v.filter(r => r[i.latitude] !== '' && r[i.longitude] !== '').map(r => ({
    lat: Number(r[i.latitude]), lon: Number(r[i.longitude]), comum: r[i.comum],
    tot: Number(r[i.total_frequentam]) || 0,
    f: [r[i.freq_0_11], r[i.freq_12_17], r[i.freq_18_29], r[i.freq_30_59], r[i.freq_60_mais]].map(Number),
    sc: Number(r[i.qtd_santa_ceia]) || 0, oc: r[i.outra_comum], oq: Number(r[i.outra_comum_qtd]) || 0,
    rep: r[i.telefone_repetido] === 'SIM' || r[i.endereco_repetido] === 'SIM'
  }));
  return resp({ ok: true, dados });
}

function doPost(e) {
  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    const r = JSON.parse(e.postData.contents);
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    let sh = ss.getSheetByName(ABA);
    if (!sh) {
      sh = ss.insertSheet(ABA);
      sh.appendRow(COLUNAS);
      sh.setFrozenRows(1);
      sh.getRange('C:C').setNumberFormat('@'); // telefone como texto
    }
    garantirCabecalho(sh);
    // Marca telefone ou endereço já cadastrado (possível casa duplicada) sem bloquear o envio
    const linhas = lerLinhas(sh);
    r.telefone_repetido = linhas.some(l => String(l[IDX.telefone]) === String(r.telefone)) ? 'SIM' : '';
    const ch = chaveEndereco(r.rua, r.numero, r.complemento);
    r.endereco_repetido = ch && linhas.some(l => chaveEndereco(l[IDX.rua], l[IDX.numero], l[IDX.complemento]) === ch) ? 'SIM' : '';
    sh.appendRow(COLUNAS.map(c => (r[c] === undefined ? '' : r[c])));
    return ContentService.createTextOutput(JSON.stringify({ ok: true }))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ ok: false, erro: String(err) }))
      .setMimeType(ContentService.MimeType.JSON);
  } finally {
    lock.releaseLock();
  }
}

/**
 * Para rodar à mão no editor (selecione "marcarRepetidos" e clique em Executar), uma vez,
 * depois de colar esta versão: recalcula telefone_repetido e endereco_repetido de todas as linhas.
 * O primeiro cadastro de cada telefone/endereço fica sem marca; os seguintes recebem "SIM".
 */
function marcarRepetidos() {
  const sh = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(ABA);
  if (!sh || sh.getLastRow() < 2) return;
  garantirCabecalho(sh);
  const linhas = lerLinhas(sh), telVistos = {}, endVistos = {};
  const marcas = linhas.map(l => {
    const tel = String(l[IDX.telefone]), ch = chaveEndereco(l[IDX.rua], l[IDX.numero], l[IDX.complemento]);
    const t = tel && telVistos[tel] ? 'SIM' : '', e = ch && endVistos[ch] ? 'SIM' : '';
    if (tel) telVistos[tel] = true;
    if (ch) endVistos[ch] = true;
    return [t, e];
  });
  sh.getRange(2, IDX.telefone_repetido + 1, marcas.length, 2).setValues(marcas);
}
