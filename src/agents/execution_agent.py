"""Execution agent with real-time order updates."""
from dhanhq import DhanContext, dhanhq, OrderUpdate
import threading
import time
from datetime import datetime
from typing import Dict, Callable, Optional
from src.utils.logger import log


class ExecutionAgent:
    """Agent for order execution and monitoring with WebSocket updates."""
    
    def __init__(self, dhan_context: DhanContext):
        self.dhan_context = dhan_context
        self.dhan = dhanhq(dhan_context)
        self.order_update_client: Optional[OrderUpdate] = None
        self.active_orders: Dict[str, Dict] = {}
        self.order_callbacks = []
        self.is_running = False
        self.update_thread: Optional[threading.Thread] = None
    
    def start_order_updates(self, on_update_callback: Callable = None) -> bool:
        """
        Start real-time order update feed via WebSocket.
        
        Args:
            on_update_callback: Callback function for order updates
        
        Returns:
            bool: Success status
        """
        try:
            if self.is_running:
                log.warning("Order updates already running")
                return True
            
            self.order_update_client = OrderUpdate(self.dhan_context)
            
            # Set callback
            if on_update_callback:
                self.order_update_client.on_update = on_update_callback
            else:
                self.order_update_client.on_update = self._default_order_handler
            
            self.is_running = True
            
            # Start worker thread
            self.update_thread = threading.Thread(
                target=self._order_update_worker,
                daemon=True,
                name="OrderUpdateWorker"
            )
            self.update_thread.start()
            
            log.info("✅ Order update feed started")
            return True
            
        except Exception as e:
            log.error(f"❌ Error starting order updates: {str(e)}")
            return False
    
    def _order_update_worker(self):
        """Worker thread for order updates with auto-reconnect."""
        while self.is_running:
            try:
                self.order_update_client.connect_to_dhan_websocket_sync()
            except Exception as e:
                log.error(f"OrderUpdate connection error: {e}. Reconnecting in 5 seconds...")
                time.sleep(5)
    
    def _default_order_handler(self, order_data: dict):
        """Default handler for order updates."""
        try:
            data = order_data.get("Data", {})
            order_id = data.get("orderId")
            order_status = data.get("orderStatus")
            
            log.info(f"📢 Order Update: {order_id} -> {order_status}")
            
            # Update active orders
            if order_id in self.active_orders:
                self.active_orders[order_id].update({
                    'status': order_status,
                    'updated_at': datetime.now(),
                    'update_data': data
                })
            
            # Trigger registered callbacks
            for callback in self.order_callbacks:
                try:
                    callback(data)
                except Exception as cb_error:
                    log.error(f"Callback error: {cb_error}")
                    
        except Exception as e:
            log.error(f"Order handler error: {str(e)}")
    
    def register_order_callback(self, callback: Callable):
        """Register custom callback for order updates."""
        self.order_callbacks.append(callback)
        log.info("Registered new order callback")
    
    def stop_order_updates(self):
        """Stop order update feed."""
        self.is_running = False
        if self.order_update_client:
            log.info("✅ Order updates stopped")
    
    def place_order(self, order_params: Dict) -> Dict:
        """
        Place order via Dhan API.
        
        Args:
            order_params: Order parameters
        
        Returns:
            dict: Order response
        """
        try:
            order_response = self.dhan.place_order(
                security_id=order_params['security_id'],
                exchange_segment=order_params['exchange_segment'],
                transaction_type=order_params['transaction_type'],
                quantity=order_params['quantity'],
                order_type=order_params['order_type'],
                product_type=order_params['product_type'],
                price=order_params.get('price', 0),
                validity=order_params.get('validity', 'DAY'),
                disclosed_quantity=order_params.get('disclosed_quantity', 0),
                after_market_order=order_params.get('after_market_order', False),
                amo_time=order_params.get('amo_time', 'OPEN'),
                bo_profit_value=order_params.get('bo_profit_value', 0),
                bo_stop_loss_Value=order_params.get('bo_stop_loss_Value', 0)
            )
            
            if order_response.get('status') == 'success':
                order_id = order_response['data']['orderId']
                
                self.active_orders[order_id] = {
                    'params': order_params,
                    'placed_at': datetime.now(),
                    'status': 'PENDING',
                    'response': order_response
                }
                
                log.info(f"✅ Order placed: {order_id}")
                return {'success': True, 'order_id': order_id, 'data': order_response}
            
            log.error(f"❌ Order failed: {order_response}")
            return {'success': False, 'error': order_response}
            
        except Exception as e:
            log.error(f"❌ Order placement error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def place_bracket_order(self, trade_setup: Dict) -> Dict:
        """
        Place Bracket Order with SL and Target.
        
        Args:
            trade_setup: Trade setup with entry, target, SL
        
        Returns:
            dict: Order response
        """
        try:
            order_params = {
                'security_id': trade_setup['security_id'],
                'exchange_segment': self.dhan.NSE_FNO,
                'transaction_type': self.dhan.BUY,
                'quantity': trade_setup['quantity'],
                'order_type': self.dhan.LIMIT,
                'product_type': self.dhan.BO,
                'price': trade_setup['entry_price'],
                'bo_profit_value': trade_setup.get('target_value', 0),
                'bo_stop_loss_Value': trade_setup.get('sl_value', 0)
            }
            
            result = self.place_order(order_params)
            return result
            
        except Exception as e:
            log.error(f"❌ Bracket order error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def modify_order(self, order_id: str, **kwargs) -> Dict:
        """Modify pending order."""
        try:
            response = self.dhan.modify_order(
                order_id=order_id,
                order_type=kwargs.get('order_type'),
                leg_name=kwargs.get('leg_name'),
                quantity=kwargs.get('quantity'),
                price=kwargs.get('price'),
                trigger_price=kwargs.get('trigger_price'),
                disclosed_quantity=kwargs.get('disclosed_quantity'),
                validity=kwargs.get('validity')
            )
            
            log.info(f"Order modified: {order_id}")
            return {'success': response.get('status') == 'success', 'data': response}
            
        except Exception as e:
            log.error(f"Modify order error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def cancel_order(self, order_id: str) -> Dict:
        """Cancel order."""
        try:
            response = self.dhan.cancel_order(order_id=order_id)
            log.info(f"Order cancelled: {order_id}")
            return {'success': response.get('status') == 'success', 'data': response}
            
        except Exception as e:
            log.error(f"Cancel order error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_positions(self) -> Dict:
        """Get current positions."""
        try:
            positions = self.dhan.get_positions()
            return positions
        except Exception as e:
            log.error(f"Position fetch error: {str(e)}")
            return {}
    
    def get_fund_limits(self) -> Dict:
        """Get fund limits."""
        try:
            funds = self.dhan.get_fund_limits()
            return funds
        except Exception as e:
            log.error(f"Fund limits error: {str(e)}")
            return {}
    
    def margin_calculator(
        self,
        exchange_segment,
        transaction_type,
        security_id,
        quantity,
        product_type,
        price
    ) -> Dict:
        """Calculate margin required."""
        try:
            margin = self.dhan.margin_calculator(
                exchange_segment=exchange_segment,
                transaction_type=transaction_type,
                security_id=security_id,
                quantity=quantity,
                product_type=product_type,
                price=price
            )
            return margin
        except Exception as e:
            log.error(f"Margin calculator error: {str(e)}")
            return {}

