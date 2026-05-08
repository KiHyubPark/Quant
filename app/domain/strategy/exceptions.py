class StrategyNotFoundError(Exception):
    def __init__(self, strategy_id: str) -> None:
        super().__init__(f"전략을 찾을 수 없습니다. (id={strategy_id})")
