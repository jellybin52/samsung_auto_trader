"""
주문 실행 - 매수/매도 주문을 체결하고 상태를 확인합니다.
"""

from typing import Optional, Dict
from datetime import datetime
from logger import logger
from api_client import api_client
from auth import get_auth_token
import config
import os


class OrderResult:
    """주문 결과를 담는 클래스."""

    def __init__(self):
        self.success: bool = False
        self.order_id: Optional[str] = None
        self.message: str = ""
        self.details: Dict = {}

    def __repr__(self) -> str:
        return f"OrderResult(success={self.success}, order_id={self.order_id}, msg={self.message})"


def place_buy_order(
    stock_code: str,
    price: int,
    quantity: int = config.DEFAULT_ORDER_QUANTITY
) -> OrderResult:
    """
    매수 주문을 실행합니다.
    
    Args:
        stock_code: 주식 코드 (예: 005930)
        price: 주문 가격 (KRW)
        quantity: 주문 수량 (기본값: 1)
        
    Returns:
        OrderResult 객체
    """
    return _place_order(
        order_type="BUY",
        stock_code=stock_code,
        price=price,
        quantity=quantity
    )


def place_sell_order(
    stock_code: str,
    price: int,
    quantity: int = config.DEFAULT_ORDER_QUANTITY
) -> OrderResult:
    """
    매도 주문을 실행합니다.
    
    Args:
        stock_code: 주식 코드 (예: 005930)
        price: 주문 가격 (KRW)
        quantity: 주문 수량 (기본값: 1)
        
    Returns:
        OrderResult 객체
    """
    return _place_order(
        order_type="SELL",
        stock_code=stock_code,
        price=price,
        quantity=quantity
    )


def _place_order(
    order_type: str,
    stock_code: str,
    price: int,
    quantity: int
) -> OrderResult:
    """
    내부 주문 함수.
    
    Args:
        order_type: "BUY" 또는 "SELL"
        stock_code: 주식 코드
        price: 주문 가격
        quantity: 주문 수량
        
    Returns:
        OrderResult 객체
    """
    result = OrderResult()

    try:
        token = get_auth_token()
        account_number = os.getenv('GH_ACCOUNT')

        if not account_number:
            result.message = "환경변수 GH_ACCOUNT를 설정해야 합니다"
            logger.error(result.message)
            return result

        app_key = os.getenv('GH_APPKEY')
        app_secret = os.getenv('GH_APPSECRET')

        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {token}",
            "appKey": app_key,
            "appSecret": app_secret,
            "tr_id": "VTTC0802U" if order_type == "BUY" else "VTTC0801U",
            "custtype": "P",
        }

        # 주문 방향 코드
        order_direction = "01" if order_type == "BUY" else "02"

        body = {
            "CANO": account_number,
            "ACNT_PRDT_CD": "01",
            "PDNO": stock_code,
            "ORD_DVSN": "00",  # 주문 구분 00: 지정가
            "ORD_QTY": str(quantity),
            "ORD_UNPR": str(price),
            "EXCG_ID_DVSN_CD": "KRX",
            "SLL_TYPE": "01" if order_type == "SELL" else "",
        }

        logger.info(
            f"{order_type} 주문 요청: {stock_code} x {quantity} @ {price} KRW"
        )

        response = api_client.post(
            config.BUY_ORDER_ENDPOINT if order_type == "BUY" else config.SELL_ORDER_ENDPOINT,
            headers=headers,
            json_body=body
        )

        # 응답 확인
        # NOTE: 정확한 필드명은 API 응답 구조에 따라 조정 필요
        if response.get('rt_cd') == '0':  # 성공
            result.success = True
            output_data = response.get('output') or response.get('output1') or response.get('output2') or {}
            if isinstance(output_data, list):
                output_data = output_data[0] if output_data else {}
            result.order_id = output_data.get('ODNO') or output_data.get('od_no') or output_data.get('ORD_NO')
            result.message = "주문 접수 성공"
            result.details = response
            logger.info(f"{order_type} 주문 접수: 주문번호 = {result.order_id}")
        else:
            result.success = False
            result.message = response.get('msg1', '주문 실패')
            result.details = response
            logger.warning(f"{order_type} 주문 실패: {result.message}")

        return result

    except Exception as e:
        result.success = False
        result.message = str(e)
        logger.error(f"{order_type} 주문 실패: {e}")
        return result


def check_order_status(
    account_number: Optional[str] = None,
    stock_code: Optional[str] = None
) -> Optional[Dict]:
    """
    최근 주문 상태를 조회합니다.
    
    Args:
        account_number: 계좌번호 (기본값: 환경변수에서 읽음)
        stock_code: 주식 코드 (기본값: 005930)
        
    Returns:
        주문 상태 딕셔너리, 실패 시 None
    """
    try:
        token = get_auth_token()
        if not account_number:
            account_number = os.getenv('GH_ACCOUNT')

        if not account_number:
            logger.error("환경변수 GH_ACCOUNT를 설정해야 합니다")
            return None

        if not stock_code:
            stock_code = config.TARGET_STOCK

        app_key = os.getenv('GH_APPKEY')
        app_secret = os.getenv('GH_APPSECRET')

        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {token}",
            "appKey": app_key,
            "appSecret": app_secret,
            "tr_id": "VTTC8001R",
            "custtype": "P",
        }

        today = datetime.today().strftime("%Y%m%d")
        params = {
            "CANO": account_number,
            "ACNT_PRDT_CD": "01",
            "INQR_STRT_DT": today,
            "INQR_END_DT": today,
            "SLL_BUY_DVSN_CD": "00",
            "CCLD_DVSN": "00",
            "INQR_DVSN": "01",
            "INQR_DVSN_3": "00",
            "PDNO": stock_code,
            "ORD_GNO_BRNO": "",
            "ODNO": "",
            "INQR_DVSN_1": "",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
            "EXCG_ID_DVSN_CD": "KRX",
        }

        logger.debug(f"주문 상태 조회: {stock_code}")
        response = api_client.get(
            config.ORDER_STATUS_ENDPOINT,
            headers=headers,
            params=params
        )

        # 응답에서 주문 정보 추출
        orders = response.get('output1') or response.get('output') or response.get('output2') or []
        if isinstance(orders, dict):
            orders = [orders]

        if orders:
            logger.info(f"최근 주문 상태: {len(orders)}개 주문 조회됨")
            return orders
        else:
            logger.info("최근 주문이 없습니다")
            return []

    except Exception as e:
        logger.error(f"주문 상태 조회 실패: {e}")
        return None
