import logging
from bot.config import config

logger = logging.getLogger("RiskManager")

class RiskManager:
    def __init__(self):
        self.day_margin_per_mnq = 100.0  # Marge intradia estàndard a Tradovate
        self.min_cash_buffer = 300.0      # Coixí mínim de seguretat absolut

    def calculate_contracts(self, cash_balance: float) -> int:
        """
        Calcula el nombre de contractes MNQ basat en el mode del bot,
        el capital actual i els llindars d'escalat.
        """
        if not config.auto_scale:
            return config.initial_contracts

        mode = config.bot_mode

        # 1. Mode Avaluació Prop Firm (Turbo Fast-Pass)
        if mode == "evaluation":
            qty = config.evaluation_contracts
            logger.info(f"[Mode Eval] Capital: ${cash_balance:,.2f} | Posició fixa: {qty} MNQ")
            return qty

        # 2. Mode Comptes Fondejats (Apex / Prop Firms ~50K)
        if mode == "funded" and cash_balance >= 20000.0:
            if cash_balance < config.funded_buffer_threshold:
                qty = config.funded_buffer_contracts  # 3 MNQ per blindar el compte (< $52,100)
            else:
                qty = config.funded_max_contracts     # 5 MNQ un cop assolit el matalàs
            logger.info(f"[Mode Funded] Capital: ${cash_balance:,.2f} | Posició: {qty} MNQ (Buffer: ${config.funded_buffer_threshold:,.0f})")
            return qty

        # 3. Mode Compte Real Personal (Escalat des d'1 MNQ)
        if cash_balance >= config.scale_threshold_4:
            qty = 4
        elif cash_balance >= config.scale_threshold_3:
            qty = 3
        elif cash_balance >= config.scale_threshold_2:
            qty = 2
        else:
            qty = 1

        logger.info(f"[Mode Real/Personal] Capital: ${cash_balance:,.2f} | Posició calculada: {qty} MNQ")
        return qty

    def validate_margin(self, cash_balance: float, contracts: int) -> bool:
        """
        Comprova que hi hagi prou marge al compte per obrir la posició sense perill
        de liquidació automàtica per part del broker.
        """
        required_margin = contracts * self.day_margin_per_mnq
        total_needed = required_margin + self.min_cash_buffer

        if cash_balance < total_needed:
            err_msg = (
                f"⚠️ Marge insuficient! Saldo disponible: ${cash_balance:,.2f}, "
                f"Requerit per operar ({contracts} MNQ + coixí): ${total_needed:,.2f}."
            )
            logger.error(err_msg)
            return False

        return True

risk_manager = RiskManager()
