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
  'latitude', 'longitude', 'utm_e', 'utm_n', 'origem_posicao', 'telefone_repetido'
];

function doGet(e) {
  const resp = o => ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
  if (!CHAVE_MAPA || !e || !e.parameter || e.parameter.chave !== CHAVE_MAPA) {
    return resp({ ok: false, erro: 'chave' });
  }
  const sh = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(ABA);
  if (!sh || sh.getLastRow() < 2) return resp({ ok: true, dados: [] });
  const v = sh.getRange(2, 1, sh.getLastRow() - 1, COLUNAS.length).getValues();
  const i = {}; COLUNAS.forEach((c, k) => { i[c] = k; });
  const dados = v.filter(r => r[i.latitude] !== '' && r[i.longitude] !== '').map(r => ({
    lat: Number(r[i.latitude]), lon: Number(r[i.longitude]), comum: r[i.comum],
    tot: Number(r[i.total_frequentam]) || 0,
    f: [r[i.freq_0_11], r[i.freq_12_17], r[i.freq_18_29], r[i.freq_30_59], r[i.freq_60_mais]].map(Number),
    sc: Number(r[i.qtd_santa_ceia]) || 0, oc: r[i.outra_comum], oq: Number(r[i.outra_comum_qtd]) || 0,
    rep: r[i.telefone_repetido] === 'SIM'
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
    // Marca telefone já cadastrado (possível casa duplicada) sem bloquear o envio
    const n = sh.getLastRow();
    const tels = n > 1 ? sh.getRange(2, 3, n - 1, 1).getValues().flat().map(String) : [];
    r.telefone_repetido = tels.indexOf(String(r.telefone)) >= 0 ? 'SIM' : '';
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
