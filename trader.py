"""
거래 오케스트레이션 - 주가 확인, 계좌 확인, 주문 실행 로직을 조직화합니다.
"""

from typing import Optional
from logger import logger
from market_data import get_current_price
from account import get_account_info
from orders import OrderResult, place_buy_order, place_sell_order, check_order_status
import config


class Trader:
    """자동 거래 시스템의 메인 로직을 담당합니다."""

    def __init__(self, stock_code: str = config.TARGET_STOCK):
        self.stock_code = stock_code
        self.buy_offset = config.BUY_OFFSET
        self.sell_offset = config.SELL_OFFSET
        self.order_quantity = config.DEFAULT_ORDER_QUANTITY

    def execute_trading_cycle(self) -> bool:
        """
        하나의 거래 사이클을 실행합니다.
        
        절차:
        1. 현재 주가 조회
        2. 계좌 잔액/보유 확인 (거래 전)
        3. 매수 주문 (현재가 - 2000 KRW)
        4. 계좌 잔액/보유 확인 (매수 후)
        5. 매도 주문 (현재가 + 2000 KRW)
        6. 계좌 잔액/보유 확인 (매도 후)
        7. 주문 상태 확인
        
        Returns:
            성공 여부 (bool)
        """
        logger.info("==== 거래 사이클 시작 ====")

        # 1. 현재 주가 조회
        current_price = get_current_price(self.stock_code)
        if not current_price:
            logger.error("주가 조회 실패, 거래 사이클 취소")
            return False

        # 2. 거래 전 계좌 상태 확인
        account_before = get_account_info()
        if not account_before:
            logger.error("계좌 조회 실패, 거래 사이클 취소")
            return False

        logger.info(
            f"거래 전 상태: 현금={account_before.cash_balance}, 보유={account_before.holdings}, "
            f"보유가치={account_before.total_holdings_value}, 총자산={account_before.total_value}"
        )

        # 주문 가격 계산
        if config.USE_CURRENT_PRICE_FOR_TEST:
            buy_price = current_price
            sell_price = current_price
            logger.info("테스트 모드: 현재가로 매수/매도 주문을 시도합니다")
        else:
            buy_price = current_price - self.buy_offset
            sell_price = current_price + self.sell_offset

        logger.info(f"주문 가격 설정: 매수={buy_price} KRW, 매도={sell_price} KRW")

        # 3. 매수 주문
        buy_result = place_buy_order(
            stock_code=self.stock_code,
            price=buy_price,
            quantity=self.order_quantity
        )

        if not buy_result.success:
            logger.warning(f"매수 주문 실패: {buy_result.message}")
            # 계속 진행할지 중단할지는 정책에 따라 결정
            # 현재는 계속 진행
        else:
            # 4. 매수 후 계좌 상태 확인
            account_after_buy = get_account_info()
            if account_after_buy:
                logger.info(
                    f"매수 후 상태: 현금={account_after_buy.cash_balance}, 보유={account_after_buy.holdings}, "
                    f"매도 가능={account_after_buy.sellable_holdings}"
                )
            else:
                account_after_buy = None

        # 5. 매도 주문
        sell_result = OrderResult()
        sellable_qty = 0
        if account_after_buy:
            sellable_qty = account_after_buy.sellable_holdings.get(self.stock_code, 0)

        if sellable_qty <= 0:
            sell_result.success = False
            sell_result.message = (
                f"매도 불가: 매도 가능 수량이 없습니다 (available={sellable_qty})"
            )
            logger.warning(sell_result.message)
        else:
            sell_result = place_sell_order(
                stock_code=self.stock_code,
                price=sell_price,
                quantity=min(self.order_quantity, sellable_qty)
            )

            if not sell_result.success:
                logger.warning(f"매도 주문 실패: {sell_result.message}")
            else:
                # 6. 매도 후 계좌 상태 확인
                account_after_sell = get_account_info()
                if account_after_sell:
                    logger.info(
                        f"매도 후 상태: 현금={account_after_sell.cash_balance}, 보유={account_after_sell.holdings}, "
                        f"매도 가능={account_after_sell.sellable_holdings}"
                    )

        # 7. 주문 상태 확인
        order_status = check_order_status(stock_code=self.stock_code)
        if order_status:
            logger.info(f"주문 상태: {order_status}")

        logger.info("==== 거래 사이클 완료 ====\n")

        # 적어도 하나의 주문이 성공했으면 True 반환
        return buy_result.success or sell_result.success

    def should_trade_now(self, current_hour: int, current_minute: int) -> bool:
        """
        현재 시간이 거래 시간 내인지 확인합니다.
        
        Args:
            current_hour: 현재 시간 (0-23)
            current_minute: 현재 분 (0-59)
            
        Returns:
            거래 가능 여부 (bool)
        """
        start_hour = config.TRADING_START_HOUR
        start_minute = config.TRADING_START_MINUTE
        end_hour = config.TRADING_END_HOUR
        end_minute = config.TRADING_END_MINUTE

        current_total_minutes = current_hour * 60 + current_minute
        start_total_minutes = start_hour * 60 + start_minute
        end_total_minutes = end_hour * 60 + end_minute

        if start_total_minutes <= current_total_minutes < end_total_minutes:
            return True
        else:
            return False
