class BacktestResultNotFoundError(Exception):
    def __init__(self, result_id: str) -> None:
        super().__init__(f"백테스트 결과를 찾을 수 없습니다. (id={result_id})")
