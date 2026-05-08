class OrderNotFoundError(Exception):
    def __init__(self, order_id: str) -> None:
        super().__init__(f"주문을 찾을 수 없습니다. (id={order_id})")


class OrderCancelFailedError(Exception):
    def __init__(self, order_id: str) -> None:
        super().__init__(f"주문 취소에 실패했습니다. (id={order_id})")
