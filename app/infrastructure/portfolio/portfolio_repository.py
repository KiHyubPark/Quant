from app.domain.portfolio.entity import Balance, Position
from app.domain.portfolio.exceptions import PositionNotFoundError


class InMemoryPortfolioRepository:
    """
    더미 포트폴리오 저장소.

    실제 계좌 잔고 없이도 API를 테스트할 수 있도록
    하드코딩된 샘플 데이터를 반환한다.
    KIS API 연동 시 kis_portfolio_repository.py로 교체 예정.
    """

    _DUMMY_POSITIONS: tuple[Position, ...] = (
        Position(
            stock_code="005930",
            stock_name="삼성전자",
            quantity=10,
            avg_price=70000,
            current_price=75000,
            profit_loss=50000,
            profit_loss_rate=7.14,
        ),
        Position(
            stock_code="000660",
            stock_name="SK하이닉스",
            quantity=5,
            avg_price=120000,
            current_price=130000,
            profit_loss=50000,
            profit_loss_rate=8.33,
        ),
    )

    async def get_balance(self) -> Balance:
        total_eval = sum(
            p.current_price * p.quantity for p in self._DUMMY_POSITIONS
        )
        total_profit_loss = sum(p.profit_loss for p in self._DUMMY_POSITIONS)
        return Balance(
            cash=5_000_000,
            total_eval=total_eval,
            total_profit_loss=total_profit_loss,
            positions=self._DUMMY_POSITIONS,
        )

    async def get_positions(self) -> list[Position]:
        return list(self._DUMMY_POSITIONS)

    async def get_position(self, stock_code: str) -> Position:
        for pos in self._DUMMY_POSITIONS:
            if pos.stock_code == stock_code:
                return pos
        raise PositionNotFoundError(stock_code)
