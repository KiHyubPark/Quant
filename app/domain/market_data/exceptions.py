class StockNotFoundError(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(f"종목을 찾을 수 없습니다. (code={code})")
