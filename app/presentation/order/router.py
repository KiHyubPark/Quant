from fastapi import APIRouter, Depends, HTTPException

from app.application.order.commands import CancelOrderCommand, PlaceOrderCommand
from app.application.order.use_cases import OrderUseCases
from app.domain.order.exceptions import OrderCancelFailedError, OrderNotFoundError
from app.infrastructure.order.order_repository import InMemoryOrderRepository
from app.presentation.order.schemas import OrderResponseSchema, PlaceOrderSchema, TradeSchema

router = APIRouter(prefix="/orders", tags=["Order"])

_order_repo = InMemoryOrderRepository()


def get_use_cases() -> OrderUseCases:
    return OrderUseCases(_order_repo)


def _order_to_dict(order) -> dict:
    return {
        "order_id": order.order_id,
        "stock_code": order.stock_code,
        "order_type": order.order_type,
        "quantity": order.quantity,
        "price": order.price,
        "status": order.status,
        "created_at": order.created_at,
    }


def _trade_to_dict(trade) -> dict:
    return {
        "trade_id": trade.trade_id,
        "order_id": trade.order_id,
        "stock_code": trade.stock_code,
        "order_type": trade.order_type,
        "quantity": trade.quantity,
        "price": trade.price,
        "traded_at": trade.traded_at,
    }


@router.post("", response_model=OrderResponseSchema, status_code=201, summary="주문 실행")
async def place_order(
    body: PlaceOrderSchema,
    use_cases: OrderUseCases = Depends(get_use_cases),
):
    order = await use_cases.place(
        PlaceOrderCommand(
            stock_code=body.stock_code,
            order_type=body.order_type,
            quantity=body.quantity,
            price=body.price,
        )
    )
    return _order_to_dict(order)


@router.delete("/{order_id}", response_model=OrderResponseSchema, summary="주문 취소")
async def cancel_order(
    order_id: str,
    use_cases: OrderUseCases = Depends(get_use_cases),
):
    try:
        order = await use_cases.cancel(CancelOrderCommand(order_id=order_id))
        return _order_to_dict(order)
    except OrderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except OrderCancelFailedError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/trades", response_model=list[TradeSchema], summary="체결 내역 조회")
async def list_trades(use_cases: OrderUseCases = Depends(get_use_cases)):
    trades = await use_cases.list_trades()
    return [_trade_to_dict(t) for t in trades]


@router.get("/{order_id}", response_model=OrderResponseSchema, summary="주문 단건 조회")
async def get_order(
    order_id: str,
    use_cases: OrderUseCases = Depends(get_use_cases),
):
    try:
        order = await use_cases.get(order_id)
        return _order_to_dict(order)
    except OrderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
