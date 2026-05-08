class PositionNotFoundError(Exception):
    def __init__(self, stock_code: str) -> None:
        super().__init__(f"보유 종목을 찾을 수 없습니다. (code={stock_code})")
