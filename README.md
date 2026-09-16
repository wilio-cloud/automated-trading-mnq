# 🚀 BACKTEST MASTER PRO 2026 — ESTRATÈGIA DE ZONES DE LIQUIDITAT NQ / MNQ

> **Sistema Quantitatiu Institucional de Mean Reversion sobre Màxims i Mínims de Sessió Verges**  
> **Dades oficials de CME Globex (`MNQ.c.0`) | 1 Any Complet (Setembre 2025 - Setembre 2026) | 352.220 Barres d'1 Minut**

---

## 📌 1. RESUM EXECUTIU DEL PROJECTE

Aquest projecte conté la investigació quantitativa completa, codi font, dades històriques d'alta resolució, motor de simulació de comptes fondejats de prop firms i estratègia Pine Script v6 per a TradingView de l'estratègia **NQ/MNQ Session Zones Mean Reversion**.

### 🌟 Resultats Clau del Sistema:
* **Modalitat Reina (Només Londres - TP 10 / SL 60)**:
  * **Win Rate**: **94,27%** (395 guanys / 24 pèrdues sobre 419 operacions).
  * **Profit Factor**: **2,74**.
  * **Benefici Net Anual (1 NQ)**: **+$50.200 USD**.
  * **Comptes Fondejats 50K amb 5 MNQ**: **+$22.376 USD nets/any** (descomptant comissions).
  * **Supervivència del compte**: **100% (0 comptes petats)**. Drawdown màxim: **$1.352 USD** (límit de $2.000).
  * **Mesos invictes**: 5 de 12 mesos amb un **100% de Win Rate**.

---

## 🎯 2. LA MECÀNICA DEL SISTEMA

L'estratègia aprofita les zones de liquiditat no mitigades (*Unswept Session Levels*) per capturar el gir del preu mitjançant ordres límit passives:

1. **Sessió Àsia (20:00 - 00:00 EDT / 02:00 - 06:00 CEST)**:
   * A les **00:00 EDT**, es fixen `Asia High` i `Asia Low`.
   * Es col·loquen 2 ordres limit: **Sell Limit** a l'High i **Buy Limit** al Low.
2. **Sessió Londres (02:00 - 05:00 EDT / 08:00 - 11:00 CEST)**:
   * A les **05:00 EDT (11:00 CEST)**, es fixen `London High` i `London Low`.
   * Es col·loquen 2 ordres limit: **Sell Limit** a l'High i **Buy Limit** al Low.
   * Si els nivells d'Àsia no s'han tocat, continuen actius (en la modalitat All Sessions).
3. **Regles d'Execució d'Or**:
   * 🔒 **1 sol trade per zona per dia**: Un cop el preu toca el nivell, la zona queda consumida i morta.
   * ⏰ **Tancament CME EOD**: A les **16:55 EDT (22:55 CEST)** es cancel·len totes les ordres pendents i es tanquen les posicions obertes a mercat abans del tancament diari del CME Globex.

---

## 🔬 3. EL "SWEET SPOT" DEL NASDAQ

El punt de partida habitual és **TP 10 / SL 30** (R:R 1:3).  
L'escombrat paramètric de 110 combinacions va descobrir la dinàmica real del mercat:

* **La Dilatació del Nasdaq (*Overshoot*)**: Quan el Nasdaq escombra una zona institucional, sol fer una metxa de penetració d'entre **20 i 40 punts** abans de girar-se. Amb 30 punts d'SL, el mercat et treu per pocs punts just abans d'iniciar el rebot.
* **Donar aire a l'Stop Loss (50 a 60 punts)**:
  * El Win Rate salta del **82,3% al 94,3%**.
  * El Benefici Net puja un **+50%** (de $49.200 a $74.000 USD per NQ).
  * Les pèrdues anuals cauen dràsticament.

---

## 🏆 4. ESCALAT MULTI-COMPTE (5 MNQ NOMÉS LONDRES)

Rendiment net real a la butxaca (amb comissions de broker/CME de -$6,50 RT descomptades) per a flotes de comptes fondejats de 50K operats amb Trade Copier:

| Nre. Comptes | Benefici Brut Anual | Comissions CME | 💰 BENEFICI NET ANUAL | 📅 NET MENSUAL | 🛡️ Supervivència |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **1 Compte** | $25.100 | -$2.724 | **$22.376 USD** | **$1.865 / mes** | 100% (0 petats) |
| **2 Comptes** | $50.200 | -$5.447 | **$44.753 USD** | **$3.729 / mes** | 100% (0 petats) |
| **3 Comptes** | $75.300 | -$8.170 | **$67.130 USD** | **$5.594 / mes** | 100% (0 petats) |
| **4 Comptes** | $100.400 | -$10.894 | **$89.506 USD** | **$7.459 / mes** | 100% (0 petats) |
| **5 Comptes** | $125.500 | -$13.617 | **$111.882 USD** | **$9.324 / mes** | 100% (0 petats) |
| **10 Comptes** | **$251.000** | **-$27.235** | **$223.765 USD** | **$18.647 / mes** | **100% (0 petats)** |

*(Drawdown màxim històric registrat: $1.352 USD sobre el límit de $2.000 de 50K).*

---

## ⚠️ 5. COMPLIMENT DE LA NORMA APEX LEGACY (5:1)

Als comptes PA Legacy d'Apex, l'Stop Loss **no pot ser superior a 5 vegades el Take Profit**:
* **TP 10 / SL 60** = 6,0:1 $\rightarrow$ ❌ **Prohibit a Apex Legacy**.
* **TP 12 / SL 60** = 5,0:1 $\rightarrow$ ✅ **Límit legal exacte** (92,8% WR | +$22.944 nets/compte amb 4 MNQ).
* **TP 12 / SL 50** = 4,17:1 $\rightarrow$ 🛡️ **Recomanat amb Marge** (evita problemes per slippage, 89,5% WR | Max DD $1.408 | +$18.400 nets/compte amb 4 MNQ).

---

## 📂 6. ESTRUCTURA DELS FITXERS

```text
backtest-master-pro-2026/
├── README.md                      # Aquest document mestre
├── INFORME_DISCORD_NQ_ZONES.md   # Informe complet de 9 seccions preparat per a Discord
├── NQ_Zones_Strategy_v6.pine      # Codi font Pine Script v6 per a TradingView
├── data/
│   ├── mnq_1m_1year.parquet       # Dades 1-minut contínues 1 any CME Globex (11 MB)
│   ├── mnq_1m_1year.csv           # Dades en CSV (30 MB)
│   ├── nq_today.json              # Dades intraday d'auditoria
│   └── nq_now.json
├── engine/
│   ├── backtester.py              # Motor de backtesting basat en esdeveniments
│   └── optimizer.py               # Algorismes d'optimització de quadrícula
├── results/
│   ├── grid_1year_results.csv     # Resultats de les 110 combinacions de TP/SL (All sessions)
│   ├── grid_london_only.csv       # Resultats de la quadrícula Només Londres
│   └── grid_search_results.csv
└── scripts/
    ├── optimize_london_only.py    # Generador de mètriques exclusives de Londres
    ├── test_tp11_comparison.py    # Anàlisi comparatiu de TP 10 vs 11 vs 12 amb comissions
    ├── test_apex_legacy_combos.py # Optimitzador de ràtios legals Apex Legacy
    ├── funded_simulation.py       # Simulació de cicle de vida de comptes de 50K
    ├── scale_10accounts.py        # Càlcul de rendiments multi-compte (1 a 10 comptes)
    ├── fast_optimizer_1year.py    # Motor ràpid d'optimització 2D
    ├── inspect_5days.py           # Eina per auditar dates concretes barra a barra
    └── download_1year.py          # Script de descàrrega de Databento
```

---

## 💻 7. COM EXECUTAR ELS SCRIPTS

Tots els scripts utilitzen Python 3 amb `pandas`, `numpy` i `pyarrow`:

```bash
# Executar el comparatiu de TP 10 vs TP 11 vs TP 12 amb comissions
python3 scripts/test_tp11_comparison.py

# Executar l'optimització exclusiva de Londres
python3 scripts/optimize_london_only.py

# Executar la simulació de comptes fondejats de 50K
python3 scripts/funded_simulation.py

# Comprovar les combinacions compliants amb Apex Legacy
python3 scripts/test_apex_legacy_combos.py
```

---

## 📈 8. INTEGRACIÓ AMB TRADINGVIEW (PINE SCRIPT v6)

El fitxer `NQ_Zones_Strategy_v6.pine` conté l'estratègia en la versió més recent de Pine Script:
1. Obre TradingView i vés al **Pine Editor**.
2. Obre `NQ_Zones_Strategy_v6.pine` i enganxa el contingut.
3. Fes clic a **Add to chart**.
4. Des dels paràmetres de l'script pots:
   * Activar/desactivar la sessió d'Àsia o Londres amb una casella.
   * Configurar l'Stop Loss i el Take Profit en punts.
   * Triar el nombre de contractes (ex: 5 per a MNQ).

---

## 🤖 9. BOT D'EXECUCIÓ AUTOMATITZADA PER A TRADOVATE

El paquet `bot/` conté el sistema autònom en Python per connectar-se directament a **Tradovate (Demo o Live)** i executar l'estratègia de zones de Londres amb ordres límit natives tipus Bracket OSO (Order Sends Order):

* **Gestió de Risc**: 1 MNQ per posició per a capital inicial de 1.000$ (amb escalat automàtic a 2 MNQ a partir de 2.200$).
* **Sweet Spot de Londres**: TP a 10 punts (+20$), SL a 60 punts (-120$).
* **Ordres OSO al Broker**: Tant el Take Profit com l'Stop Loss es pengen al servidor de CME des del moment d'execució.
* **Sense límit d'1 pèrdua**: Tant London High com London Low operen de manera independent.
* **Tancament EOD**: Cancel·lació d'ordres pendents i liquidació forçosa a les 16:55 EDT (22:55 CEST) per complir els marges intradia.

### ⚙️ Configuració Ràpida:
1. Copia la plantilla de credencials:
   ```bash
   cp .env.example .env
   ```
2. Edita `.env` i afegeix el teu usuari de Tradovate, contrasenya i API Secret. Mantén `TRADOVATE_ENV=demo` inicialment.
3. Comprova que tot estigui correcte:
   ```bash
   ./run_bot.sh check
   ```

### 🚀 Comandes d'Administració:
```bash
./run_bot.sh check         # Diagnòstic complet de connexió, contracte actiu i zones
./run_bot.sh start         # Inicia el bot en segon pla (24/7 en VPS)
./run_bot.sh status        # Comprova l'estat del procés
./run_bot.sh logs          # Visualitza els logs en temps real
./run_bot.sh test-trigger  # Força la col·locació de zones immediatament (per a proves)
./run_bot.sh stop          # Atura el bot amb seguretat
```
