import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker("ko_KR")

PRODUCT_CATEGORIES = ["전자제품", "패션/의류", "식품/음료", "생활용품", "스포츠/레저", "도서/문구", "뷰티/건강"]

ORDER_STATUSES = ["pending", "confirmed", "shipped", "delivered", "cancelled"]

PRODUCT_NAMES = {
    "전자제품":   ["스마트폰", "노트북", "태블릿", "이어폰", "스마트워치", "카메라", "충전기", "키보드", "마우스"],
    "패션/의류":  ["티셔츠", "청바지", "운동화", "자켓", "원피스", "가방", "모자", "양말", "스카프"],
    "식품/음료":  ["커피원두", "녹차", "과자세트", "초콜릿", "견과류", "에너지드링크", "비타민워터"],
    "생활용품":  ["치약", "샴푸", "세탁세제", "방향제", "손세정제", "휴지", "주방세제"],
    "스포츠/레저": ["요가매트", "덤벨", "러닝화", "등산스틱", "자전거헬멧", "수영모", "스키장갑"],
    "도서/문구":  ["볼펜세트", "노트", "스케치북", "형광펜", "파일철", "달력", "포스트잇"],
    "뷰티/건강":  ["선크림", "립밤", "마스크팩", "토너", "에센스", "바디로션", "핸드크림"],
}


def _random_past_datetime(days: int = 365) -> str:
    delta = timedelta(seconds=random.randint(0, days * 86400))
    return (datetime.now() - delta).strftime("%Y-%m-%d %H:%M:%S")


def generate_products(count: int) -> list[dict]:
    products = []
    for _ in range(count):
        category = random.choice(PRODUCT_CATEGORIES)
        base_name = random.choice(PRODUCT_NAMES[category])
        brand = fake.company()
        products.append({
            "name": f"{brand} {base_name}",
            "category": category,
            "price": round(random.uniform(1000, 500000), -1),
            "stock": random.randint(0, 1000),
            "description": fake.sentence(nb_words=10),
            "created_at": _random_past_datetime(365),
        })
    return products


def generate_orders(count: int, product_ids: list[int]) -> list[dict]:
    if not product_ids:
        raise ValueError("주문 생성을 위한 상품 ID 목록이 비어 있습니다.")
    orders = []
    seen_order_numbers: set[str] = set()
    for _ in range(count):
        quantity = random.randint(1, 10)
        price_per_unit = round(random.uniform(1000, 300000), -1)
        order_number = _unique_order_number(seen_order_numbers)
        orders.append({
            "order_number": order_number,
            "product_id": random.choice(product_ids),
            "quantity": quantity,
            "total_price": quantity * price_per_unit,
            "status": random.choice(ORDER_STATUSES),
            "customer_name": fake.name(),
            "created_at": _random_past_datetime(180),
        })
    return orders


def _unique_order_number(seen: set[str]) -> str:
    while True:
        num = f"ORD-{fake.unique.random_number(digits=8, fix_len=True)}"
        if num not in seen:
            seen.add(num)
            return num
