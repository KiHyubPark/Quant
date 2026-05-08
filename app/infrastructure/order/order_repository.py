import uuid
from datetime import datetime, timezone

from app.domain.order.entity import Order, OrderStatus, OrderType, Trade
from app.domain.order.exceptions import OrderCancelFailedError, OrderNotFoundError


class InMemoryOrderRepository:
    """
    인메모리 주문 저장소.

    - place: 즉시 FILLED 처리 (모의 체결)
    - cancel: PENDING 상태인 주문만 취소 가능
    """

    def __init__(self) -> None:
        self._orders: dict[str, Order] = {}
        self._trades: list[Trade] = []

    async def place(self, order: Order) -> Order:
        order_id = str(uuid.uuid4())
        now = datetime.now(tz=timezone.utc).isoformat()

        # 모의 체결: 시장가(price=0)는 주문 시점 기준 임의 가격 없이 FILLED
        filled_order = Order(
            order_id=order_id,
            stock_code=order.stock_code,
            order_type=order.order_type,
            quantity=order.quantity,
            price=order.price,
            status=OrderStatus.FILLED,
            created_at=order.created_at,
        )
        self._orders[order_id] = filled_order

        trade = Trade(
            trade_id=str(uuid.uuid4()),
            order_id=order_id,
            stock_code=order.stock_code,
            order_type=order.order_type,
            quantity=order.quantity,
            price=order.price,
            traded_at=now,
        )
        self._trades.append(trade)

        return filled_order

    async def cancel(self, order_id: str) -> Order:
        order = self._orders.get(order_id)
        if order is None:
            raise OrderNotFoundError(order_id)
        if order.status != OrderStatus.PENDING:
            raise OrderCancelFailedError(order_id)

        cancelled = Order(
            order_id=order.order_id,
            stock_code=order.stock_code,
            order_type=order.order_type,
            quantity=order.quantity,
            price=order.price,
            status=OrderStatus.CANCELLED,
            created_at=order.created_at,
        )
        self._orders[order_id] = cancelled
        return cancelled

    async def get(self, order_id: str) -> Order:
        order = self._orders.get(order_id)
        if order is None:
            raise OrderNotFoundError(order_id)
        return order

    async def list_trades(self) -> list[Trade]:
        return list(self._trades)
