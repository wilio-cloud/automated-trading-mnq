import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import requests
from bot.config import config

logger = logging.getLogger("TradovateClient")

class TradovateClient:
    def __init__(self):
        self.base_url = config.base_url
        self.access_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        self.user_id: Optional[int] = None
        self.account_id: Optional[int] = config.account_id
        self.account_spec: Optional[str] = config.account_spec

    def authenticate(self) -> bool:
        """
        Autentica amb Tradovate utilitzant l'endpoint /auth/accesstokenrequest.
        Renova automàticament el token si és a punt d'expirar.
        """
        if not config.user or not config.password:
            logger.warning("Credencials de Tradovate no configurades a .env (TRADOVATE_USER o TRADOVATE_PASS buit).")
            return False

        # Si el token és vigent (amb marge de 5 minuts), no cal renovar
        if self.access_token and self.token_expiry:
            if datetime.now() < self.token_expiry - timedelta(minutes=5):
                return True

        url = f"{self.base_url}/auth/accesstokenrequest"
        payload = {
            "name": config.user,
            "password": config.password,
            "appId": config.app_id,
            "appVersion": config.app_version,
            "sec": config.sec
        }
        if config.cid:
            try:
                payload["cid"] = int(config.cid)
            except ValueError:
                payload["cid"] = config.cid

        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        
        try:
            logger.info(f"Connectant a Tradovate ({config.tradovate_env.upper()}): {url}...")
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                self.access_token = data.get("accessToken")
                self.user_id = data.get("userId")
                
                # Expiració
                expiration_str = data.get("expirationTime")
                if expiration_str:
                    try:
                        self.token_expiry = datetime.fromisoformat(expiration_str.replace("Z", "+00:00"))
                    except Exception:
                        self.token_expiry = datetime.now() + timedelta(hours=2)
                else:
                    self.token_expiry = datetime.now() + timedelta(hours=2)

                logger.info("✅ Autenticació amb Tradovate completada amb èxit!")
                
                # Auto-resoldre compte si no estava fixat
                if not self.account_id or not self.account_spec:
                    self._resolve_default_account()
                return True
            else:
                logger.error(f"Error d'autenticació Tradovate: HTTP {resp.status_code} - {resp.text}")
                return False
        except Exception as e:
            logger.error(f"Excepció durant l'autenticació: {e}")
            return False

    def _get_headers(self) -> Dict[str, str]:
        if not self.access_token:
            self.authenticate()
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def _resolve_default_account(self):
        """Troba el compte actiu per defecte si no s'ha especificat a .env."""
        try:
            accounts = self.get_accounts()
            if accounts and len(accounts) > 0:
                acc = accounts[0]
                self.account_id = acc.get("id")
                self.account_spec = acc.get("name")
                logger.info(f"Compte per defecte assignat: {self.account_spec} (ID: {self.account_id})")
        except Exception as e:
            logger.warning(f"No s'ha pogut auto-resoldre el compte: {e}")

    def get_accounts(self) -> List[Dict[str, Any]]:
        """Retorna la llista de comptes de l'usuari."""
        url = f"{self.base_url}/account/list"
        resp = requests.get(url, headers=self._get_headers(), timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_cash_balance(self) -> float:
        """
        Retorna el saldo de liquidació o caixa en efectiu del compte.
        """
        try:
            url = f"{self.base_url}/cashBalance/list"
            resp = requests.get(url, headers=self._get_headers(), timeout=10)
            if resp.status_code == 200:
                items = resp.json()
                for item in items:
                    if not self.account_id or item.get("accountId") == self.account_id:
                        return float(item.get("amount", 0.0))
            
            # Fallback directament a la llista de comptes
            accounts = self.get_accounts()
            for acc in accounts:
                if not self.account_id or acc.get("id") == self.account_id:
                    if "balance" in acc:
                        return float(acc["balance"])
        except Exception as e:
            logger.warning(f"No s'ha pogut consultar el saldo directe: {e}")
            
        return 1000.0  # Fallback segur per defecte

    def suggest_contract(self, symbol_text: str = "MNQ") -> Optional[str]:
        """Consulta l'API de Tradovate per suggerir el contracte actiu."""
        url = f"{self.base_url}/contract/suggest?text={symbol_text}"
        try:
            resp = requests.get(url, headers=self._get_headers(), timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0:
                    return data[0].get("name")
        except Exception as e:
            logger.debug(f"Error suggerint contracte: {e}")
        return None

    def find_contract(self, name: str) -> Optional[Dict[str, Any]]:
        """Busca les metadades d'un contracte pel seu nom exacte."""
        url = f"{self.base_url}/contract/find?name={name}"
        try:
            resp = requests.get(url, headers=self._get_headers(), timeout=10)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logger.error(f"Error consultant contracte {name}: {e}")
        return None

    def place_bracket_order(
        self,
        symbol: str,
        action: str,  # "Buy" o "Sell"
        qty: int,
        entry_price: float,
        tp_price: float,
        sl_price: float
    ) -> Optional[Dict[str, Any]]:
        """
        Envia una ordre OSO (Order Sends Order) / Bracket nativa a Tradovate.
        L'ordre pare és Limit, i en omplir-se genera automàticament l'Stop Loss i el Take Profit com a parell OCO.
        """
        url = f"{self.base_url}/order/placeOSO"
        
        # Acció oposada per a les sortides
        exit_action = "Sell" if action.lower() == "buy" else "Buy"

        payload = {
            "accountSpec": self.account_spec,
            "accountId": self.account_id,
            "action": action.capitalize(),
            "symbol": symbol,
            "orderQty": qty,
            "orderType": "Limit",
            "price": round(entry_price, 2),
            "isAutomated": True,
            "bracket1": {
                "action": exit_action,
                "orderType": "Stop",
                "stopPrice": round(sl_price, 2)
            },
            "bracket2": {
                "action": exit_action,
                "orderType": "Limit",
                "price": round(tp_price, 2)
            }
        }

        logger.info(
            f"Enviant ordre OSO a Tradovate: {action.upper()} {qty} {symbol} @ {entry_price:.2f} "
            f"[TP: {tp_price:.2f} | SL: {sl_price:.2f}]"
        )
        
        try:
            resp = requests.post(url, json=payload, headers=self._get_headers(), timeout=10)
            if resp.status_code in (200, 201):
                data = resp.json()
                logger.info(f"✅ Ordre OSO col·locada correctament: {data}")
                return data
            else:
                logger.error(f"❌ Error col·locant ordre OSO: HTTP {resp.status_code} - {resp.text}")
                return None
        except Exception as e:
            logger.error(f"Excepció en place_bracket_order: {e}")
            return None

    def get_open_orders(self) -> List[Dict[str, Any]]:
        """Retorna les ordres actives/pendents."""
        url = f"{self.base_url}/order/list"
        try:
            resp = requests.get(url, headers=self._get_headers(), timeout=10)
            if resp.status_code == 200:
                all_orders = resp.json()
                # Filtrar per compte si cal
                return [o for o in all_orders if not self.account_id or o.get("accountId") == self.account_id]
        except Exception as e:
            logger.error(f"Error consultant ordres: {e}")
        return []

    def cancel_order(self, order_id: int) -> bool:
        """Cancel·la una ordre específica."""
        url = f"{self.base_url}/order/cancelorder"
        payload = {"orderId": order_id}
        try:
            resp = requests.post(url, json=payload, headers=self._get_headers(), timeout=10)
            return resp.status_code in (200, 201)
        except Exception as e:
            logger.error(f"Error cancel·lant ordre {order_id}: {e}")
            return False

    def cancel_all_pending_orders(self) -> int:
        """Cancel·la totes les ordres que encara estiguin en estat 'Working' o 'Pending'."""
        orders = self.get_open_orders()
        canceled_count = 0
        for o in orders:
            status = o.get("ordStatus", "").lower()
            if status in ("working", "accepted", "pending"):
                oid = o.get("id")
                if oid and self.cancel_order(oid):
                    canceled_count += 1
        logger.info(f"Cancel·lades {canceled_count} ordres pendents.")
        return canceled_count

    def get_positions(self) -> List[Dict[str, Any]]:
        """Retorna les posicions obertes actuals."""
        url = f"{self.base_url}/position/list"
        try:
            resp = requests.get(url, headers=self._get_headers(), timeout=10)
            if resp.status_code == 200:
                all_positions = resp.json()
                return [p for p in all_positions if not self.account_id or p.get("accountId") == self.account_id]
        except Exception as e:
            logger.error(f"Error consultant posicions: {e}")
        return []

    def close_all_positions(self, symbol: Optional[str] = None) -> bool:
        """
        Tanca/aplana (flatten) qualsevol posició oberta a mercat (utilitzat per a l'EOD de les 16:55 EDT).
        """
        positions = self.get_positions()
        success = True
        for pos in positions:
            net_pos = pos.get("netPos", 0)
            if net_pos == 0:
                continue
            
            contract_id = pos.get("contractId")
            # Liquidar posició
            url = f"{self.base_url}/order/liquidateposition"
            payload = {
                "accountId": self.account_id,
                "contractId": contract_id,
                "admin": False
            }
            logger.warning(f"Liquidant posició EOD: Contracte ID {contract_id} (Net: {net_pos})...")
            try:
                resp = requests.post(url, json=payload, headers=self._get_headers(), timeout=10)
                if resp.status_code not in (200, 201):
                    logger.error(f"Error liquidant posició: {resp.status_code} - {resp.text}")
                    success = False
            except Exception as e:
                logger.error(f"Excepció liquidant posició: {e}")
                success = False
        return success

tradovate_client = TradovateClient()
