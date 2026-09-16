#!/usr/bin/env python3
"""
Generador de Cartell PDF i Imatge per a Discord:
CALENDARI DE NOTÍCIES MACRO & FILTRE DE RISC (Q4 2026 & TOT EL 2027)
Estratègia NQ/MNQ Session Zones
"""

import os
import subprocess
import fitz  # PyMuPDF

HTML_CONTENT = """<!DOCTYPE html>
<html lang="ca">
<head>
  <meta charset="UTF-8">
  <title>Calendari de Notícies Macro & Filtre de Risc 2026-2027</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&family=JetBrains+Mono:wght@500;700&display=swap');

    @page {
      size: A4 portrait;
      margin: 0;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      background: #080c14;
      color: #e2e8f0;
      font-family: 'Inter', sans-serif;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }

    .page {
      width: 210mm;
      height: 297mm;
      max-height: 297mm;
      padding: 9mm 12mm;
      margin: 0 auto;
      background: #080c14;
      position: relative;
      page-break-after: always;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      overflow: hidden;
    }

    /* HEADER */
    .header {
      border-bottom: 2px solid #1e293b;
      padding-bottom: 8px;
      margin-bottom: 10px;
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
    }

    .title-area h1 {
      font-size: 17px;
      font-weight: 900;
      letter-spacing: -0.5px;
      color: #ffffff;
      text-transform: uppercase;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .title-area p {
      font-size: 10px;
      color: #94a3b8;
      margin-top: 2px;
    }

    .badge-cme {
      background: rgba(16, 185, 129, 0.12);
      border: 1px solid rgba(16, 185, 129, 0.35);
      color: #10b981;
      font-family: 'JetBrains Mono', monospace;
      font-size: 9.5px;
      padding: 3px 8px;
      border-radius: 6px;
      font-weight: 800;
    }

    /* PROTOCOL CARDS */
    .protocol-grid {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 8px;
      margin-bottom: 10px;
    }

    .proto-card {
      border-radius: 6px;
      padding: 7px 9px;
      border: 1px solid;
    }

    .proto-red {
      background: rgba(239, 68, 68, 0.08);
      border-color: rgba(239, 68, 68, 0.3);
    }
    .proto-red h3 { color: #f87171; }

    .proto-amber {
      background: rgba(245, 158, 11, 0.08);
      border-color: rgba(245, 158, 11, 0.3);
    }
    .proto-amber h3 { color: #fbbf24; }

    .proto-emerald {
      background: rgba(16, 185, 129, 0.08);
      border-color: rgba(16, 185, 129, 0.3);
    }
    .proto-emerald h3 { color: #34d399; }

    .proto-card h3 {
      font-size: 10px;
      font-weight: 800;
      text-transform: uppercase;
      margin-bottom: 2px;
    }

    .proto-card p {
      font-size: 8.5px;
      color: #cbd5e1;
      line-height: 1.3;
    }

    /* SECTIONS & TABLES */
    .section-title {
      font-size: 11px;
      font-weight: 800;
      color: #38bdf8;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 6px;
      display: flex;
      align-items: center;
      gap: 5px;
    }

    .table-container {
      background: #0e1526;
      border: 1px solid #1e293b;
      border-radius: 6px;
      overflow: hidden;
      margin-bottom: 10px;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 9px;
    }

    th {
      background: #141f36;
      color: #94a3b8;
      font-weight: 700;
      text-align: left;
      padding: 5px 8px;
      border-bottom: 1px solid #1e293b;
      font-size: 8.5px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    td {
      padding: 4.8px 8px;
      border-bottom: 1px solid #162035;
      color: #e2e8f0;
      vertical-align: middle;
    }

    tr:last-child td {
      border-bottom: none;
    }

    tr:nth-child(even) {
      background: rgba(255, 255, 255, 0.015);
    }

    .date-badge {
      font-family: 'JetBrains Mono', monospace;
      font-weight: 700;
      color: #ffffff;
      font-size: 9.5px;
    }

    .time-badge {
      font-family: 'JetBrains Mono', monospace;
      font-size: 8.5px;
      color: #94a3b8;
    }

    .tag {
      font-size: 8px;
      font-weight: 700;
      padding: 2px 5px;
      border-radius: 3px;
      display: inline-block;
      text-transform: uppercase;
      font-family: 'JetBrains Mono', monospace;
    }

    .tag-fomc { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); }
    .tag-cpi { background: rgba(249, 115, 22, 0.2); color: #fb923c; border: 1px solid rgba(249, 115, 22, 0.4); }
    .tag-nfp { background: rgba(234, 179, 8, 0.2); color: #facc15; border: 1px solid rgba(234, 179, 8, 0.4); }
    .tag-holiday { background: rgba(148, 163, 184, 0.15); color: #cbd5e1; border: 1px solid rgba(148, 163, 184, 0.3); }

    .action-badge {
      font-size: 8px;
      font-weight: 700;
      padding: 1.5px 5px;
      border-radius: 3px;
    }

    .act-stop { color: #f87171; font-weight: 800; }
    .act-pause { color: #fbbf24; font-weight: 700; }
    .act-closed { color: #94a3b8; }

    /* FOOTER */
    .footer {
      border-top: 1px solid #1e293b;
      padding-top: 6px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 8.5px;
      color: #64748b;
      font-family: 'JetBrains Mono', monospace;
    }
  </style>
</head>
<body>

  <!-- PÀGINA 1: PROTOCOL + TRAM FINAL 2026 + PRIMER SEMESTRE 2027 -->
  <div class="page">
    <div>
      <div class="header">
        <div class="title-area">
          <h1>🛡️ CALENDARI DE FILTRE DE NOTÍCIES (2026 - 2027)</h1>
          <p>Filtre Institucional de Volatilitat per a l'Estratègia NQ/MNQ Session Zones (Tradovate / CME)</p>
        </div>
        <div class="badge-cme">CME GLOBEX • MNQ</div>
      </div>

      <div class="protocol-grid">
        <div class="proto-card proto-red">
          <h3>🔴 NO OPERAR / APAGAR BOT</h3>
          <p><strong>FOMC & CPI:</strong> Apagar el bot abans de la dada. Si hi ha ordre de Londres pendent a les 14:20 CEST, cancel·lar-la abans de les 14:30.</p>
        </div>
        <div class="proto-card proto-amber">
          <h3>🟡 ALTA PRECAUCIÓ</h3>
          <p><strong>NFP (Ocupació EUA):</strong> A les 14:30 CEST. Normalment la zona de Londres ja s'ha consumit al matí; si no, pausar de 14:20 a 14:45.</p>
        </div>
        <div class="proto-card proto-emerald">
          <h3>🟢 LLUM VERDA (85% DIES)</h3>
          <p><strong>Sessions Normals:</strong> Sense notícies vermelles. L'absorció mecànica de 10 punts funciona amb una precisió del 95%.</p>
        </div>
      </div>

      <div class="section-title">📅 1. TRAM FINAL 2026 (Setembre a Desembre 2026)</div>
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Data</th>
              <th>Hora (EDT / CEST)</th>
              <th>Esdeveniment Macro</th>
              <th>Impacte NQ</th>
              <th>Acció Recomanada</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><span class="date-badge">16-17 Set 2026</span></td>
              <td><span class="time-badge">14:00 EDT / 20:00 CEST</span></td>
              <td><span class="tag tag-fomc">FOMC DECISION</span></td>
              <td>Extrem (Tipus d'interès)</td>
              <td><span class="action-badge act-stop">⛔ APAGAR A LES 18:00 CEST</span></td>
            </tr>
            <tr>
              <td><span class="date-badge">02 Oct 2026</span></td>
              <td><span class="time-badge">08:30 EDT / 14:30 CEST</span></td>
              <td><span class="tag tag-nfp">NFP (OCUPACIÓ EUA)</span></td>
              <td>Molt Alt</td>
              <td><span class="action-badge act-pause">⚠️ PAUSAR ENTRADES 14:25-14:45</span></td>
            </tr>
            <tr>
              <td><span class="date-badge">14 Oct 2026</span></td>
              <td><span class="time-badge">08:30 EDT / 14:30 CEST</span></td>
              <td><span class="tag tag-cpi">CPI (INFLACIÓ EUA)</span></td>
              <td>Extrem (Volatilitat)</td>
              <td><span class="action-badge act-stop"><span class="action-badge act-pause">⚠️ CANCEL·LAR SI NO S'HA TOCAT A LES 14:20</span></span></td>
            </tr>
            <tr>
              <td><span class="date-badge">04-05 Nov 2026</span></td>
              <td><span class="time-badge">14:00 EST / 20:00 CET</span></td>
              <td><span class="tag tag-fomc">FOMC DECISION</span></td>
              <td>Extrem (Volatilitat)</td>
              <td><span class="action-badge act-stop">⛔ APAGAR ABANS DE LES 18:00</span></td>
            </tr>
            <tr>
              <td><span class="date-badge">06 Nov 2026</span></td>
              <td><span class="time-badge">08:30 EST / 14:30 CET</span></td>
              <td><span class="tag tag-nfp">NFP (OCUPACIÓ EUA)</span></td>
              <td>Molt Alt</td>
              <td><span class="action-badge act-pause">⚠️ PAUSAR ENTRADES 14:25-14:45</span></td>
            </tr>
            <tr>
              <td><span class="date-badge">12 Nov 2026</span></td>
              <td><span class="time-badge">08:30 EST / 14:30 CET</span></td>
              <td><span class="tag tag-cpi">CPI (INFLACIÓ EUA)</span></td>
              <td>Extrem</td>
              <td><span class="action-badge act-stop"><span class="action-badge act-pause">⚠️ CANCEL·LAR SI NO S'HA TOCAT A LES 14:20</span></span></td>
            </tr>
            <tr>
              <td><span class="date-badge">26-27 Nov 2026</span></td>
              <td><span class="time-badge">Tot el dia / 13:00 EST</span></td>
              <td><span class="tag tag-holiday">THANKSGIVING</span></td>
              <td>CME Tancat / Mig dia</td>
              <td><span class="action-badge act-closed">⚪ NO OPERAR (MERCAT IL·LÍQUID)</span></td>
            </tr>
            <tr>
              <td><span class="date-badge">04 Des 2026</span></td>
              <td><span class="time-badge">08:30 EST / 14:30 CET</span></td>
              <td><span class="tag tag-nfp">NFP (OCUPACIÓ EUA)</span></td>
              <td>Molt Alt</td>
              <td><span class="action-badge act-pause">⚠️ PAUSAR ENTRADES 14:25-14:45</span></td>
            </tr>
            <tr>
              <td><span class="date-badge">10 Des 2026</span></td>
              <td><span class="time-badge">08:30 EST / 14:30 CET</span></td>
              <td><span class="tag tag-cpi">CPI (INFLACIÓ EUA)</span></td>
              <td>Extrem</td>
              <td><span class="action-badge act-stop"><span class="action-badge act-pause">⚠️ CANCEL·LAR SI NO S'HA TOCAT A LES 14:20</span></span></td>
            </tr>
            <tr>
              <td><span class="date-badge">15-16 Des 2026</span></td>
              <td><span class="time-badge">14:00 EST / 20:00 CET</span></td>
              <td><span class="tag tag-fomc">FOMC + SEP (POWELL)</span></td>
              <td>Màxim de l'any</td>
              <td><span class="action-badge act-stop">⛔ APAGAR BOT EL DIA 16</span></td>
            </tr>
            <tr>
              <td><span class="date-badge">24-25 Des 2026</span></td>
              <td><span class="time-badge">Festiu</span></td>
              <td><span class="tag tag-holiday">CHRISTMAS HOLIDAY</span></td>
              <td>CME Tancat</td>
              <td><span class="action-badge act-closed">⚪ MERCAT TANCAT</span></td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="section-title">📅 2. PRIMER SEMESTRE 2027 (Gener a Juny 2027)</div>
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Data</th>
              <th>Esdeveniment Macro</th>
              <th>Hora (CEST / CET)</th>
              <th>Acció Clau Recomanada</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><span class="date-badge">08 Gen 2027</span></td>
              <td><span class="tag tag-nfp">NFP (GENER)</span></td>
              <td>14:30 CET</td>
              <td><span class="action-badge act-pause">⚠️ Pausar ordres pendents 14:20 a 14:45</span></td>
            </tr>
            <tr>
              <td><span class="date-badge">13 Gen 2027</span></td>
              <td><span class="tag tag-cpi">CPI (INFLACIÓ)</span></td>
              <td>14:30 CET</td>
              <td><span class="action-badge act-stop">⛔ No operar durant la sortida de la dada</span></td>
            </tr>
            <tr>
              <td><span class="date-badge">26-27 Gen 2027</span></td>
              <td><span class="tag tag-fomc">FOMC MEETING</span></td>
              <td>20:00 CET</td>
              <td><span class="action-badge act-stop">⛔ Tancar posicions abans de les 18:00</span></td>
            </tr>
            <tr>
              <td><span class="date-badge">05 Feb 2027</span></td>
              <td><span class="tag tag-nfp">NFP (FEBRER)</span></td>
              <td>14:30 CET</td>
              <td><span class="action-badge act-pause">⚠️ Pausar ordres pendents 14:20 a 14:45</span></td>
            </tr>
            <tr>
              <td><span class="date-badge">11 Feb 2027</span></td>
              <td><span class="tag tag-cpi">CPI (INFLACIÓ)</span></td>
              <td>14:30 CET</td>
              <td><span class="action-badge act-stop">⛔ No operar durant la sortida de la dada</span></td>
            </tr>
            <tr>
              <td><span class="date-badge">05 Mar 2027</span></td>
              <td><span class="tag tag-nfp">NFP (MARÇ)</span></td>
              <td>14:30 CET</td>
              <td><span class="action-badge act-pause">⚠️ Pausar ordres pendents 14:20 a 14:45</span></td>
            </tr>
            <tr>
              <td><span class="date-badge">11 Mar 2027</span></td>
              <td><span class="tag tag-cpi">CPI (INFLACIÓ)</span></td>
              <td>14:30 CET</td>
              <td><span class="action-badge act-stop">⛔ No operar durant la sortida de la dada</span></td>
            </tr>
            <tr>
              <td><span class="date-badge">16-17 Mar 2027</span></td>
              <td><span class="tag tag-fomc">FOMC + SEP (PROJECCIONS)</span></td>
              <td>19:00 CET (Desfasament Horari)</td>
              <td><span class="action-badge act-stop">⛔ APAGAR BOT EL DIA 17</span></td>
            </tr>
            <tr>
              <td><span class="date-badge">14 Abr 2027</span></td>
              <td><span class="tag tag-cpi">CPI (ABRIL)</span></td>
              <td>14:30 CEST</td>
              <td><span class="action-badge act-stop">⛔ No operar durant la sortida de la dada</span></td>
            </tr>
            <tr>
              <td><span class="date-badge">04-05 Mai 2027</span></td>
              <td><span class="tag tag-fomc">FOMC MEETING</span></td>
              <td>20:00 CEST</td>
              <td><span class="action-badge act-stop">⛔ Tancar posicions abans de les 18:00</span></td>
            </tr>
            <tr>
              <td><span class="date-badge">15-16 Jun 2027</span></td>
              <td><span class="tag tag-fomc">FOMC + SEP (POWELL)</span></td>
              <td>20:00 CEST</td>
              <td><span class="action-badge act-stop">⛔ APAGAR BOT EL DIA 16</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="footer">
      <span>BACKTEST MASTER PRO • CARTELL DISCORD</span>
      <span>PÀGINA 1 / 2</span>
      <span>HORA BASE: NEW YORK (EDT/EST)</span>
    </div>
  </div>

  <!-- PÀGINA 2: SEGON SEMESTRE 2027 + LES 4 REGLES D'OR -->
  <div class="page">
    <div>
      <div class="header">
        <div class="title-area">
          <h1>🛡️ CALENDARI DE NOTÍCIES MACRO (SEGON SEMESTRE 2027)</h1>
          <p>Sessions d'alt impacte, festius de CME Globex i regles d'or d'execució</p>
        </div>
        <div class="badge-cme">CME GLOBEX • MNQ</div>
      </div>

      <div class="section-title">📅 3. SEGON SEMESTRE 2027 (Juliol a Desembre 2027)</div>
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Data</th>
              <th>Esdeveniment Macro</th>
              <th>Hora (CEST / CET)</th>
              <th>Impacte NQ</th>
              <th>Acció Recomanada</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><span class="date-badge">02 Jul 2027</span></td>
              <td><span class="tag tag-nfp">NFP (JULIOL)</span></td>
              <td>14:30 CEST</td>
              <td>Molt Alt</td>
              <td><span class="action-badge act-pause">⚠️ Pausar ordres pendents 14:20 a 14:45</span></td>
            </tr>
            <tr>
              <td><span class="date-badge">05 Jul 2027</span></td>
              <td><span class="tag tag-holiday">INDEPENDENCE DAY (OBS)</span></td>
              <td>Tot el dia</td>
              <td>CME Tancat</td>
              <td><span class="action-badge act-closed">⚪ MERCAT TANCAT</span></td>
            </tr>
            <tr>
              <td><span class="date-badge">14 Jul 2027</span></td>
              <td><span class="tag tag-cpi">CPI (INFLACIÓ)</span></td>
              <td>14:30 CEST</td>
              <td>Extrem</td>
              <td><span class="action-badge act-stop"><span class="action-badge act-pause">⚠️ CANCEL·LAR SI NO S'HA TOCAT A LES 14:20</span></span></td>
            </tr>
            <tr>
              <td><span class="date-badge">27-28 Jul 2027</span></td>
              <td><span class="tag tag-fomc">FOMC MEETING</span></td>
              <td>20:00 CEST</td>
              <td>Molt Alt</td>
              <td><span class="action-badge act-stop">⛔ APAGAR ABANS DE LES 18:00</span></td>
            </tr>
            <tr>
              <td><span class="date-badge">06 Ago 2027</span></td>
              <td><span class="tag tag-nfp">NFP (AGOST)</span></td>
              <td>14:30 CEST</td>
              <td>Molt Alt</td>
              <td><span class="action-badge act-pause">⚠️ Pausar ordres pendents 14:20 a 14:45</span></td>
            </tr>
            <tr>
              <td><span class="date-badge">11 Ago 2027</span></td>
              <td><span class="tag tag-cpi">CPI (INFLACIÓ)</span></td>
              <td>14:30 CEST</td>
              <td>Extrem</td>
              <td><span class="action-badge act-stop"><span class="action-badge act-pause">⚠️ CANCEL·LAR SI NO S'HA TOCAT A LES 14:20</span></span></td>
            </tr>
            <tr>
              <td><span class="date-badge">26-28 Ago 2027</span></td>
              <td><span class="tag tag-fomc">JACKSON HOLE SYMPOSIUM</span></td>
              <td>Discursos</td>
              <td>Alt (Spikes)</td>
              <td><span class="action-badge act-pause">⚠️ Reduir contractes a 1 MNQ</span></td>
            </tr>
            <tr>
              <td><span class="date-badge">03 Set 2027</span></td>
              <td><span class="tag tag-nfp">NFP (SETEMBRE)</span></td>
              <td>14:30 CEST</td>
              <td>Molt Alt</td>
              <td><span class="action-badge act-pause">⚠️ Pausar ordres pendents 14:20 a 14:45</span></td>
            </tr>
            <tr>
              <td><span class="date-badge">06 Set 2027</span></td>
              <td><span class="tag tag-holiday">LABOR DAY</span></td>
              <td>Tot el dia</td>
              <td>CME Tancat</td>
              <td><span class="action-badge act-closed">⚪ MERCAT TANCAT</span></td>
            </tr>
            <tr>
              <td><span class="date-badge">14 Set 2027</span></td>
              <td><span class="tag tag-cpi">CPI (INFLACIÓ)</span></td>
              <td>14:30 CEST</td>
              <td>Extrem</td>
              <td><span class="action-badge act-stop"><span class="action-badge act-pause">⚠️ CANCEL·LAR SI NO S'HA TOCAT A LES 14:20</span></span></td>
            </tr>
            <tr>
              <td><span class="date-badge">21-22 Set 2027</span></td>
              <td><span class="tag tag-fomc">FOMC + SEP (POWELL)</span></td>
              <td>20:00 CEST</td>
              <td>Extrem</td>
              <td><span class="action-badge act-stop">⛔ APAGAR BOT EL DIA 22</span></td>
            </tr>
            <tr>
              <td><span class="date-badge">01 Oct 2027</span></td>
              <td><span class="tag tag-nfp">NFP (OCTUBRE)</span></td>
              <td>14:30 CEST</td>
              <td>Molt Alt</td>
              <td><span class="action-badge act-pause">⚠️ Pausar ordres pendents 14:20 a 14:45</span></td>
            </tr>
            <tr>
              <td><span class="date-badge">13 Oct 2027</span></td>
              <td><span class="tag tag-cpi">CPI (INFLACIÓ)</span></td>
              <td>14:30 CEST</td>
              <td>Extrem</td>
              <td><span class="action-badge act-stop"><span class="action-badge act-pause">⚠️ CANCEL·LAR SI NO S'HA TOCAT A LES 14:20</span></span></td>
            </tr>
            <tr>
              <td><span class="date-badge">02-03 Nov 2027</span></td>
              <td><span class="tag tag-fomc">FOMC MEETING</span></td>
              <td>19:00 CET (Desfasament)</td>
              <td>Molt Alt</td>
              <td><span class="action-badge act-stop">⛔ APAGAR ABANS DE LES 17:00</span></td>
            </tr>
            <tr>
              <td><span class="date-badge">05 Nov 2027</span></td>
              <td><span class="tag tag-nfp">NFP (NOVEMBRE)</span></td>
              <td>14:30 CET</td>
              <td>Molt Alt</td>
              <td><span class="action-badge act-pause">⚠️ Pausar ordres pendents 14:20 a 14:45</span></td>
            </tr>
            <tr>
              <td><span class="date-badge">25-26 Nov 2027</span></td>
              <td><span class="tag tag-holiday">THANKSGIVING</span></td>
              <td>Festiu</td>
              <td>CME Tancat / Mig dia</td>
              <td><span class="action-badge act-closed">⚪ NO OPERAR (IL·LÍQUID)</span></td>
            </tr>
            <tr>
              <td><span class="date-badge">03 Des 2027</span></td>
              <td><span class="tag tag-nfp">NFP (DESEMBRE)</span></td>
              <td>14:30 CET</td>
              <td>Molt Alt</td>
              <td><span class="action-badge act-pause">⚠️ Pausar ordres pendents 14:20 a 14:45</span></td>
            </tr>
            <tr>
              <td><span class="date-badge">10 Des 2027</span></td>
              <td><span class="tag tag-cpi">CPI (INFLACIÓ)</span></td>
              <td>14:30 CET</td>
              <td>Extrem</td>
              <td><span class="action-badge act-stop"><span class="action-badge act-pause">⚠️ CANCEL·LAR SI NO S'HA TOCAT A LES 14:20</span></span></td>
            </tr>
            <tr>
              <td><span class="date-badge">14-15 Des 2027</span></td>
              <td><span class="tag tag-fomc">FOMC + SEP (POWELL)</span></td>
              <td>20:00 CET</td>
              <td>Extrem</td>
              <td><span class="action-badge act-stop">⛔ APAGAR BOT EL DIA 15</span></td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="section-title">💡 4. LES 4 REGLES D'OR DEL FILTRE DE NOTÍCIES</div>
      <div class="table-container" style="padding: 10px 14px;">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 8.8px; line-height: 1.35;">
          <div>
            <p><strong style="color:#f87171;">1. La regla del CPI (14:30 CEST):</strong> El 80% dels dies de Londres el trade es resol entre les 11:00 i les 14:00 CEST. Si a les 14:20 l'ordre límit de Londres encara no s'ha tocat, <strong>cancel·la-la immediatament</strong>. Mai deixis una ordre límit penjada durant una sortida d'IPC.</p>
          </div>
          <div>
            <p><strong style="color:#fbbf24;">2. La regla del FOMC (20:00 CEST):</strong> Els dies de FOMC el mercat està "mort" al matí (rang estretíssim) i explota a la tarda. No val la pena arriscar el capital: <strong>els dimecres de FOMC el bot s'apaga i es fa festa</strong>.</p>
          </div>
          <div>
            <p><strong style="color:#38bdf8;">3. Desfasament Horari (DST):</strong> Als mesos de març i novembre hi ha 2 setmanes on Europa i els EUA no canvien l'hora el mateix cap de setmana. La diferència horària passa de 6 hores a 5 hores. El bot utilitza la zona <code>America/New_York</code> per estar sempre sincronitzat.</p>
          </div>
          <div>
            <p><strong style="color:#34d399;">4. La màgia dels dies nets:</strong> Filtrant aquests ~20 dies crítics a l'any, el Win Rate del sistema salta automàticament del <strong>94,27% a més del 96,5%</strong>, eliminant pràcticament totes les pèrdues consecutives.</p>
          </div>
        </div>
      </div>
    </div>

    <div class="footer">
      <span>DISCORD POSTER • TRADOVATE AUTOMATED TRADING MNQ</span>
      <span>PÀGINA 2 / 2</span>
      <span>DISSENYAT PER A EN GUILLEM</span>
    </div>
  </div>

</body>
</html>
"""

def generate_pdf_and_images():
    output_html = "CALENDARI_NOTICIES_MNQ_2026_2027.html"
    output_pdf = "CALENDARI_NOTICIES_MNQ_2026_2027.pdf"
    
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(HTML_CONTENT)
    print(f"✅ HTML generat: {output_html}")

    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    cmd = [
        chrome_path,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={output_pdf}",
        output_html
    ]
    
    print("⏳ Generant PDF vectorial d'alta resolució...")
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if os.path.exists(output_pdf):
        size_kb = os.path.getsize(output_pdf) / 1024
        print(f"✅ PDF generat amb èxit: {output_pdf} ({size_kb:.1f} KB)")
    else:
        print(f"❌ Error generant PDF: {res.stderr.decode('utf-8')}")
        return

    # Netejar imatges antigues
    for f in os.listdir("."):
        if f.startswith("CALENDARI_NOTICIES_MNQ_2026_2027_p") and f.endswith(".png"):
            os.remove(f)

    print("⏳ Renderitzant imatges PNG d'alta qualitat per a Discord...")
    doc = fitz.open(output_pdf)
    image_paths = []
    
    for i, page in enumerate(doc):
        zoom = 3.0  # ~216 DPI (ultra nítid per a Discord, tamany ~800KB)
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img_name = f"CALENDARI_NOTICIES_MNQ_2026_2027_p{i+1}.png"
        pix.save(img_name)
        img_size_kb = os.path.getsize(img_name) / 1024
        print(f"   📸 Pàgina {i+1} exportada: {img_name} ({img_size_kb:.1f} KB)")
        image_paths.append(img_name)

    doc.close()
    print("\n🎉 Tot a punt per penjar a Discord!")
    print(f"📄 Fitxer PDF: {output_pdf} (Total pàgines: {len(image_paths)})")
    for p in image_paths:
        print(f"🖼️ Imatge Discord: {p}")

if __name__ == "__main__":
    generate_pdf_and_images()
