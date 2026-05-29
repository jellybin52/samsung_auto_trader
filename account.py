"""
계좌 정보 조회 - 잔액 및 보유 주식 정보를 가져옵니다.
"""

from typing import Dict, Optional
from logger import logger
from api_client import api_client
from auth import get_auth_token
import config
import os


class AccountInfo:
    """계좌 정보를 담는 클래스."""

    def __init__(self):
        self.cash_balance: Optional[int] = None
        self.holdings: Dict[str, int] = {}  # {주식코드: 수량}
        self.sellable_holdings: Dict[str, int] = {}  # {주식코드: 매도 가능 수량}
        self.holding_values: Dict[str, int] = {}  # {주식코드: 평가액}
        self.total_holdings_value: Optional[int] = None
        self.total_value: Optional[int] = None
        self.account_number: str = ""

    def __repr__(self) -> str:
        return (
            f"AccountInfo(cash={self.cash_balance}, total_holdings_value={self.total_holdings_value}, "
            f"total_value={self.total_value}, holdings={self.holdings}, "
            f"sellable={self.sellable_holdings})"
        )


def get_account_info() -> Optional[AccountInfo]:
    """
    계좌 정보를 조회합니다 (잔액 및 보유 주식).
    
    Returns:
        AccountInfo 객체, 실패 시 None
    """
    try:
        token = get_auth_token()
        account_number = os.getenv('GH_ACCOUNT')

        if not account_number:
            logger.error("환경변수 GH_ACCOUNT를 설정해야 합니다")
            return None

        app_key = os.getenv('GH_APPKEY')
        app_secret = os.getenv('GH_APPSECRET')

        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {token}",
            "appKey": app_key,
            "appSecret": app_secret,
            "tr_id": "VTTC8434R",
            "custtype": "P",
        }

        params = {
            "CANO": account_number,  # 계좌번호
            "ACNT_PRDT_CD": "01",  # 계좌상품코드 (기본값)
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "00",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
        }

        logger.debug(f"계좌정보 조회: {account_number}")
        response = api_client.get(
            config.HOLDINGS_ENDPOINT,
            headers=headers,
            params=params
        )

        account_info = AccountInfo()
        account_info.account_number = account_number

        # 응답에서 현금 잔액 추출
        output2 = response.get('output2', [])
        if isinstance(output2, dict):
            output2 = [output2]

        if isinstance(output2, list) and len(output2) > 0:
            account_summary = output2[0]
        else:
            account_summary = {}

        cash = None
        if isinstance(account_summary, dict):
            cash = account_summary.get('nass_amt')
            if cash is None:
                cash = account_summary.get('dnca_tot_amt')
            if cash is None:
                cash = account_summary.get('scts_evlu_amt')
            if cash is None:
                cash = account_summary.get('tot_evlu_amt')

        if cash is not None:
            try:
                account_info.cash_balance = int(cash)
            except (TypeError, ValueError):
                logger.warning(f"현금 잔액 변환 실패: {cash}")

        # 응답에서 보유 주식 정보 추출
        holdings_list = response.get('output1', [])
        if isinstance(holdings_list, dict):
            holdings_list = [holdings_list]

        if not isinstance(holdings_list, list):
            holdings_list = []

        total_holdings = 0
        total_holding_value = 0

        for holding in holdings_list:
            if not isinstance(holding, dict):
                continue

            stock_code = holding.get('pdno') or holding.get('pdno_code') or holding.get('stck_iscd')
            quantity = holding.get('hldg_qty') or holding.get('hldg_qty_sum') or holding.get('hldg_qty')
            sellable = holding.get('ord_psbl_qty') or holding.get('ord_psbl_qty_sum')
            value = holding.get('evlu_amt') or holding.get('pchs_amt') or holding.get('tot_evlu_amt')

            if stock_code and quantity is not None:
                try:
                    quantity_int = int(quantity)
                    account_info.holdings[stock_code] = quantity_int
                    total_holdings += quantity_int
                except (TypeError, ValueError):
                    logger.warning(f"보유 수량 변환 실패: {quantity} for {stock_code}")
                    continue

                try:
                    sellable_int = int(sellable) if sellable is not None else 0
                except (TypeError, ValueError):
                    logger.warning(f"매도 가능 수량 변환 실패: {sellable} for {stock_code}")
                    sellable_int = 0
                account_info.sellable_holdings[stock_code] = sellable_int

                if value is not None:
                    try:
                        value_int = int(float(value))
                        account_info.holding_values[stock_code] = value_int
                        total_holding_value += value_int
                    except (TypeError, ValueError):
                        logger.warning(f"보유 평가액 변환 실패: {value} for {stock_code}")

        if total_holding_value > 0:
            account_info.total_holdings_value = total_holding_value

        if account_info.cash_balance is not None:
            account_info.total_value = account_info.cash_balance + (account_info.total_holdings_value or 0)

        logger.info(f"계좌 정보 조회 완료: {account_info}")
        return account_info

    except Exception as e:
        logger.error(f"계좌 정보 조회 실패: {e}")
        return None
