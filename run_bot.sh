#!/bin/bash
# ==============================================================================
# SCRIPT D'ADMINISTRACIÓ I GESTIÓ DEL BOT TRADOVATE MNQ ZONES
# ==============================================================================

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

PID_FILE="$DIR/bot.pid"
LOG_FILE="$DIR/bot.log"
PYTHON_CMD="python3"

case "$1" in
    check)
        echo "🔍 Executant comprovació de diagnòstic..."
        $PYTHON_CMD bot/main.py --check
        ;;
    start)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p "$PID" > /dev/null 2>&1; then
                echo "⚠️ El bot ja s'està executant amb PID $PID."
                exit 1
            else
                rm -f "$PID_FILE"
            fi
        fi
        echo "🚀 Iniciant el Bot de Tradovate en segon pla..."
        nohup $PYTHON_CMD bot/main.py > /dev/null 2>&1 &
        NEW_PID=$!
        echo "$NEW_PID" > "$PID_FILE"
        echo "✅ Bot iniciat correctament amb PID $NEW_PID."
        echo "📄 Logs en temps real disponibles a: $LOG_FILE (o fes './run_bot.sh logs')"
        ;;
    run)
        echo "🚀 Executant el bot en primer pla (Ctrl+C per aturar)..."
        $PYTHON_CMD bot/main.py
        ;;
    stop)
        if [ ! -f "$PID_FILE" ]; then
            echo "ℹ️ No hi ha cap procés registrat a $PID_FILE."
            exit 0
        fi
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "🛑 Aturant el bot (PID $PID)..."
            kill "$PID"
            sleep 2
            if ps -p "$PID" > /dev/null 2>&1; then
                kill -9 "$PID"
            fi
            echo "✅ Bot aturat."
        else
            echo "ℹ️ El procés $PID no està actiu."
        fi
        rm -f "$PID_FILE"
        ;;
    status)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p "$PID" > /dev/null 2>&1; then
                echo "🟢 El bot està EN MARXA (PID: $PID)."
            else
                echo "🔴 El fitxer PID existeix però el procés no s'està executant."
            fi
        else
            echo "⚪ El bot està ATURAT."
        fi
        ;;
    logs)
        if [ -f "$LOG_FILE" ]; then
            tail -n 50 -f "$LOG_FILE"
        else
            echo "⚠️ Encara no s'ha generat cap fitxer de log."
        fi
        ;;
    test-trigger)
        echo "⚡ Forçant l'execució de col·locació de zones ara mateix..."
        $PYTHON_CMD bot/main.py --trigger-now
        ;;
    dashboard)
        echo "📊 Iniciant el Dashboard Interactiu a http://localhost:8000 ..."
        $PYTHON_CMD -m uvicorn dashboard.app:app --host 0.0.0.0 --port 8000 --reload
        ;;
    briefing)
        echo "📢 Enviant el Briefing Matinal a Discord..."
        $PYTHON_CMD -m bot.daily_briefing
        ;;
    *)
        echo "Ús: $0 {check|start|run|stop|status|logs|dashboard|briefing|test-trigger}"
        exit 1
        ;;
esac
