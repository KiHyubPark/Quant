from app.application.order.commands import CancelOrderCommand, PlaceOrderCommand
from app.domain.order.entity import Order, Trade
from app.domain.order.repository import OrderRepository


class OrderUseCases:
    def __init__(self, repository: OrderRepository) -> None:
        self._repository = repository

    async def place(self, command: PlaceOrderCommand) -> Order:
        from app.domain.order.entity import OrderStatus
        from datetime import datetime, timezone

        order = Order(
            order_id="",  # repository에서 채번
            stock_code=command.stock_code,
            order_type=command.order_type,
            quantity=command.quantity,
            price=command.price,
            status=OrderStatus.PENDING,
            created_at=datetime.now(tz=timezone.utc).isoformat(),
        )
        return await self._repository.place(order)

    async def cancel(self, command: CancelOrderCommand) -> Order:
        return await self._repository.cancel(command.order_id)

    async def get(self, order_id: str) -> Order:
        return await self._repository.get(order_id)

    async def list_trades(self) -> list[Trade]:
        return await self._repository.list_trades()
