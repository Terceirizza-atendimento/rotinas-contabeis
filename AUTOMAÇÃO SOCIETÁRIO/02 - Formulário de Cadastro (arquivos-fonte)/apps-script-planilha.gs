var NOTIFY_EMAIL = "atendimento@terceirizza.com.br";

function doPost(e) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
  var data = JSON.parse(e.postData.contents);

  function s(v) { return (v === undefined || v === null) ? "" : v; }

  var socios = data.socios || [];
  function socioCols(i) {
    var p = socios[i] || {};
    return [
      s(p.nome), s(p.nascimento), s(p.naturalidade), s(p.cpf), s(p.rg), s(p.orgao),
      p.tituloNaoPossui ? "não possui" : s(p.tituloEleitor),
      s(p.estadoCivil), s(p.regime), s(p.nomeMae),
      p.nomePaiNaoSei ? "não informado" : s(p.nomePai),
      s(data.cotas && data.cotas[i])
    ];
  }

  var adminIdx = data.socioAdminIndex || 0;
  var adminName = (socios[adminIdx] && socios[adminIdx].nome) || ("Sócio " + (adminIdx + 1));

  var row = [new Date(), s(data.tipo), s(data.cnpjExistente)]
    .concat(socioCols(0), socioCols(1), socioCols(2))
    .concat([
      adminName,
      data.irpf2025Enviou ? "Sim" : "Não", s(data.irpf2025Recibo),
      data.irpf2026Enviou ? "Sim" : "Não", s(data.irpf2026Recibo),
      s(data.enderecoResidencial),
      s(data.emailComercial), s(data.celularComercial),
      s(data.razaoSocial1), s(data.razaoSocial2), s(data.nomeFantasia),
      s(data.enderecoComercial), s(data.iptu), s(data.metragem),
      s(data.atendimento), s(data.horarioFuncionamento),
      s(data.capitalSocial),
      s(data.atividades),
      s(data.faturamento)
    ])
    .concat(socioCols(3), socioCols(4), socioCols(5));

  sheet.appendRow(row);
  ensureExtraHeaders(sheet);

  var mailResult = { sent: false };
  try {
    mailResult.quotaBefore = MailApp.getRemainingDailyQuota();
    sendNotification(data, adminName, sheet);
    mailResult.sent = true;
  } catch (err) {
    mailResult.error = String(err && err.message ? err.message : err);
  }

  return ContentService.createTextOutput(JSON.stringify({ ok: true, mail: mailResult }))
    .setMimeType(ContentService.MimeType.JSON);
}

// Sócios 4 a 6 ficam nas colunas BG em diante (depois do Faturamento_Projetado),
// para não mexer na posição das colunas que já existem.
function ensureExtraHeaders(sheet) {
  var firstExtraCol = 59;
  if (sheet.getRange(1, firstExtraCol).getValue() !== "") return;
  var fields = ["Nome", "Nascimento", "Naturalidade", "CPF", "RG", "OrgaoExpedidor",
    "TituloEleitor", "EstadoCivil", "Regime", "Mae", "Pai", "Cota"];
  var headers = [];
  for (var n = 4; n <= 6; n++) {
    for (var i = 0; i < fields.length; i++) headers.push("Socio" + n + "_" + fields[i]);
  }
  sheet.getRange(1, firstExtraCol, 1, headers.length).setValues([headers]);
}

function sendNotification(data, adminName, sheet) {
  function s(v) { return (v === undefined || v === null) ? "-" : (v === "" ? "-" : v); }
  var tipoLabel = data.tipo === "alteracao" ? "Alteração de empresa existente" : "Abertura de empresa nova";
  var linha = sheet.getLastRow();
  var planilhaUrl = sheet.getParent().getUrl() + "#gid=" + sheet.getSheetId() + "&range=A" + linha;
  var socios = data.socios || [];
  var cotas = data.cotas || [];

  function row2(label, value) {
    return '<tr><td style="padding:4px 12px 4px 0;color:#555;white-space:nowrap;vertical-align:top;">' + label +
      '</td><td style="padding:4px 0;font-weight:600;">' + value + '</td></tr>';
  }
  function sectionTitle(title) {
    return '<tr><td colspan="2" style="padding:18px 0 6px;border-bottom:2px solid #171B54;font-family:Georgia,serif;font-size:16px;color:#171B54;font-weight:700;">' + title + '</td></tr>';
  }

  var html = [];
  html.push('<div style="font-family:Arial,sans-serif;font-size:14px;color:#222;max-width:640px;">');
  html.push('<h2 style="font-family:Georgia,serif;color:#171B54;margin-bottom:0;">Novo cadastro recebido</h2>');
  html.push('<p style="color:#777;margin-top:4px;">' + tipoLabel + (data.cnpjExistente ? " — CNPJ " + s(data.cnpjExistente) : "") + '</p>');
  html.push('<table style="border-collapse:collapse;width:100%;">');

  for (var i = 0; i < socios.length; i++) {
    var p = socios[i] || {};
    html.push(sectionTitle("Sócio " + (i + 1) + (i === (data.socioAdminIndex || 0) ? " (administrador)" : "")));
    html.push(row2("Nome completo", s(p.nome)));
    html.push(row2("Nascimento / Naturalidade", s(p.nascimento) + " — " + s(p.naturalidade)));
    html.push(row2("CPF / RG", s(p.cpf) + " / " + s(p.rg) + " (" + s(p.orgao) + ")"));
    html.push(row2("Título de eleitor", p.tituloNaoPossui ? "não possui" : s(p.tituloEleitor)));
    html.push(row2("Estado civil", s(p.estadoCivil) + (p.regime ? " — " + p.regime : "")));
    html.push(row2("Mãe / Pai", s(p.nomeMae) + " / " + (p.nomePaiNaoSei ? "não informado" : s(p.nomePai))));
    html.push(row2("Cota societária", s(cotas[i]) + "%"));
  }

  html.push(sectionTitle("Imposto de Renda (responsável)"));
  html.push(row2("IRPF 2025", data.irpf2025Enviou ? "Enviou — recibo " + s(data.irpf2025Recibo) : "Não enviou"));
  html.push(row2("IRPF 2026", data.irpf2026Enviou ? "Enviou — recibo " + s(data.irpf2026Recibo) : "Não enviou"));

  html.push(sectionTitle("Endereço e contato"));
  html.push(row2("Endereço residencial", s(data.enderecoResidencial)));
  html.push(row2("E-mail comercial", s(data.emailComercial)));
  html.push(row2("Celular comercial", s(data.celularComercial)));

  html.push(sectionTitle("Empresa"));
  html.push(row2("Razão social (opção 1)", s(data.razaoSocial1)));
  html.push(row2("Razão social (opção 2)", s(data.razaoSocial2)));
  html.push(row2("Nome fantasia", s(data.nomeFantasia)));
  html.push(row2("Endereço comercial", s(data.enderecoComercial)));
  html.push(row2("IPTU / Metragem", s(data.iptu) + " / " + s(data.metragem) + " m²"));
  html.push(row2("Atendimento", data.atendimento === "presencial" ? "Loja física / presencial — horário: " + s(data.horarioFuncionamento) : "Home office / sem atendimento presencial"));

  html.push(sectionTitle("Financeiro"));
  html.push(row2("Capital social", s(data.capitalSocial)));
  html.push(row2("Atividades", s(data.atividades)));
  html.push(row2("Faturamento projetado", s(data.faturamento)));

  html.push('</table>');
  html.push('<p style="margin-top:24px;"><a href="' + planilhaUrl + '" style="background:#171B54;color:#fff;padding:10px 16px;border-radius:8px;text-decoration:none;font-weight:600;">Ver linha na planilha</a></p>');
  html.push('</div>');

  var plainFallback = "Novo cadastro de empresa recebido. Abra este e-mail em um cliente compatível com HTML, ou veja a linha na planilha: " + planilhaUrl;

  MailApp.sendEmail({
    to: NOTIFY_EMAIL,
    subject: "Novo cadastro de empresa recebido — " + (s(data.nomeFantasia) || adminName),
    body: plainFallback,
    htmlBody: html.join("")
  });
}
