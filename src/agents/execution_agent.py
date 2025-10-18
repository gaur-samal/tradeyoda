"""Execution agent compatible with DhanHQ v2.2 (OrderUpdate synchronous)."""
import ssl, certifi, websocket
import threading, time
from datetime import datetime
from dhanhq import DhanContext, dhanhq, OrderUpdate
from src.utils.logger import log

# ----- SSL and certifi -----
ssl_context = ssl.create_default_context(cafile=certifi.where())
websocket.setdefaulttimeout(10)
websocket._https_proxy_from_env = True
websocket._create_default_https_context = lambda: ssl_context


class ExecutionAgent:
    """Handles live order updates and order placement."""

    def __init__(self, dhan_context: DhanContext):
        self.dhan_context = dhan_context
        self.dhan = dhanhq(dhan_context)
        self.order_update_client: OrderUpdate | None = None
        self.active_orders: dict = {}
        self.is_running = False
        self.ws_thread: threading.Thread | None = None

    # ------------------------------------------------------------------
    def start_order_updates(self, on_update_callback=None):
        """Connect once to Dhan order‑update feed (synchronous)."""
        try:
            if self.is_running:
                log.warning("⚠️ Order‑update feed already running")
                return True

            self.order_update_client = OrderUpdate(self.dhan_context)
            self.order_update_client.on_update = (
                on_update_callback or self._default_order_handler
            )

            def _run_socket_once():
                """Keep single connection open; stop on failure or shutdown."""
                try:
                    log.info("🔌 Connecting to Dhan Order‑Update WebSocket (SYNC)…")
                    self.order_update_client.connect_to_dhan_websocket_sync()
                    log.info("✅ Order‑Update WebSocket session ended")
                except Exception as e:
                    if self.is_running:
                        log.error(f"❌ Order‑Update WebSocket error: {e}")

            # Start thread
            self.is_running = True
            self.ws_thread = threading.Thread(
                target=_run_socket_once, daemon=True, name="OrderUpdateSyncWS"
            )
            self.ws_thread.start()
            log.info("✅ Order‑update thread started")
            return True

        except Exception as e:
            log.error(f"❌ Order WS start error: {e}")
            self.is_running = False
            return False

    # ------------------------------------------------------------------
    def stop_order_updates(self):
        """Close socket gracefully."""
        try:
            if not self.is_running:
                log.warning("⚠️ Order‑update feed not running")
                return True

            self.is_running = False
            if self.order_update_client:
                try:
                    self.order_update_client.close_connection()
                    log.info("✅ Order‑update WebSocket closed")
                except Exception:
                    if hasattr(self.order_update_client, "disconnect"):
                        self.order_update_client.disconnect()
                        log.info("✅ Order‑update WebSocket disconnected")

            if self.ws_thread and self.ws_thread.is_alive():
                log.info("🧹 Waiting for WebSocket thread to exit…")
                self.ws_thread.join(timeout=5)
            return True

        except Exception as e:
            log.error(f"❌ Order WS stop error: {e}")
            return False

    # ------------------------------------------------------------------
    def _default_order_handler(self, message):
        """Handle order‑update packets with Correlation and Remarks."""
        try:
            data = message.get("Data", {})
            order_id = data.get("OrderNo") or data.get("orderId")
            corr = data.get("CorrelationId")
            remark = data.get("Remarks")
            status = data.get("Status") or data.get("orderStatus")

            if order_id:
                self.active_orders[order_id] = {
                    "status": status,
                    "updated_at": datetime.now(),
                    "correlation": corr,
                    "remarks": remark,
                }
                log.info(f"📢 Order Update {order_id}: {status} ({remark})")
        except Exception as e:
            log.error(f"WS handler error: {e}")

    # ------------------------------------------------------------------
    def place_order(self, order_params: dict) -> dict:
        """Place order via Dhan REST API."""
        try:
            product = order_params.get("product_type", "INTRADAY")
            if order_params.get("use_super_order"):
                product = "SO"

            payload = {
                "transactionType": order_params.get("transaction_type", "BUY"),
                "exchangeSegment": order_params.get("exchange_segment", "NSE_FNO"),
                "productType": product,
                "orderType": order_params.get("order_type", "LIMIT"),
                "validity": order_params.get("validity", "DAY"),
                "securityId": str(order_params["security_id"]),
                "quantity": str(order_params["quantity"]),
                "price": str(order_params.get("price", 0)),
                "triggerPrice": str(order_params.get("trigger_price", 0)),
                "boProfitValue": str(order_params.get("bo_profit_value", 0)),
                "boStopLossValue": str(order_params.get("bo_stop_loss_value", 0)),
                "targetPrice": str(order_params.get("target_price", 0)),
                "stopLossPrice": str(order_params.get("stop_loss_price", 0)),
                "trailingJump": str(order_params.get("trailing_jump", 0)),
            }

            resp = self.dhan.place_order(**payload)
            if resp and resp.get("status") == "success":
                oid = resp["data"].get("orderId")
                self.active_orders[oid] = {
                    "status": "PENDING",
                    "params": payload,
                    "placed_at": datetime.now(),
                }
                log.info(f"✅ Order placed: {oid}")
                return {"success": True, "order_id": oid, "response": resp}

            log.error(f"Order failed: {resp}")
            return {"success": False, "response": resp}
        except Exception as e:
            log.error(f"❌ Order placement error: {e}")
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------
    def place_bracket_or_super_order(self, setup: dict) -> dict:
        """Utility to package setup into rest order."""
        try:
            body = {
                "security_id": setup["security_id"],
                "exchange_segment": "NSE_FNO",
                "transaction_type": setup.get("transaction_type", "BUY"),
                "order_type": "LIMIT",
                "product_type": "SO" if setup.get("use_super_order") else "BO",
                "quantity": setup.get("quantity", 50),
                "price": setup["entry_price"],
                "bo_profit_value": abs(setup["target_price"] - setup["entry_price"]),
                "bo_stop_loss_value": abs(setup["entry_price"] - setup["stop_loss"]),
                "target_price": setup.get("target_price"),
                "stop_loss_price": setup.get("stop_loss"),
                "trailing_jump": setup.get("trailing_jump", 0),
            }
            return self.place_order(body)
        except Exception as e:
            log.error(f"Super/BO order error: {e}")
            return {"success": False, "error": str(e)}

