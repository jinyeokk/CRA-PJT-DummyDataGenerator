import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.panel import Panel
from rich import box

import db
from generators import generate_products, generate_orders

console = Console()


@click.group()
def cli():
    """Dummy Data Generator - SQLite 연동 POC"""


@cli.command()
@click.option("--db-path", default=None, help="SQLite DB 파일 경로 (기본값: dummy_data.db)")
@click.option("--reset", is_flag=True, help="기존 데이터를 삭제하고 초기화")
def init(db_path, reset):
    """DB 스키마를 초기화합니다."""
    if reset:
        console.print("[yellow]기존 테이블을 삭제하고 재생성합니다...[/yellow]")
        db.reset_db(db_path)
    else:
        db.init_db(db_path)
    console.print("[green]✓[/green] DB 초기화 완료")


@cli.command()
@click.option("--products", "n_products", default=20, show_default=True, help="생성할 상품 수")
@click.option("--orders",   "n_orders",   default=50, show_default=True, help="생성할 주문 수")
@click.option("--db-path", default=None, help="SQLite DB 파일 경로")
@click.option("--reset", is_flag=True, help="생성 전 기존 데이터 초기화")
def generate(n_products, n_orders, db_path, reset):
    """더미 데이터를 생성하여 DB에 삽입합니다."""
    db.init_db(db_path)
    if reset:
        console.print("[yellow]기존 데이터를 초기화합니다...[/yellow]")
        db.reset_db(db_path)
        db.init_db(db_path)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        # --- Products ---
        task_p = progress.add_task("[cyan]상품 데이터 생성 중...", total=n_products)
        products = generate_products(n_products)

        with db.transaction(db_path) as conn:
            conn.executemany(
                "INSERT INTO products (name, category, price, stock, description, created_at) "
                "VALUES (:name, :category, :price, :stock, :description, :created_at)",
                products,
            )
            product_ids = [
                row[0]
                for row in conn.execute("SELECT id FROM products").fetchall()
            ]
        progress.update(task_p, completed=n_products)

        # --- Orders ---
        task_o = progress.add_task("[magenta]주문 데이터 생성 중...", total=n_orders)
        orders = generate_orders(n_orders, product_ids)

        chunk = max(1, n_orders // 10)
        with db.transaction(db_path) as conn:
            for i in range(0, n_orders, chunk):
                batch = orders[i : i + chunk]
                conn.executemany(
                    "INSERT INTO orders (order_number, product_id, quantity, total_price, status, customer_name, created_at) "
                    "VALUES (:order_number, :product_id, :quantity, :total_price, :status, :customer_name, :created_at)",
                    batch,
                )
                progress.update(task_o, advance=len(batch))

    console.print(Panel(
        f"[bold green]✓ 완료[/bold green]\n"
        f"  상품: [cyan]{n_products}[/cyan]건 삽입\n"
        f"  주문: [magenta]{n_orders}[/magenta]건 삽입",
        title="더미 데이터 생성 결과",
        box=box.ROUNDED,
    ))


@cli.command()
@click.option("--db-path", default=None, help="SQLite DB 파일 경로")
@click.option("--limit", default=10, show_default=True, help="테이블당 출력 행 수")
def preview(db_path, limit):
    """DB에 저장된 더미 데이터를 미리봅니다."""
    db.init_db(db_path)
    conn = db.get_connection(db_path)

    _print_table(
        conn,
        f"SELECT id, name, category, price, stock, created_at FROM products LIMIT {limit}",
        title=f"[cyan]상품(Product)[/cyan] — 최근 {limit}건",
        columns=["ID", "상품명", "카테고리", "가격(₩)", "재고", "생성일시"],
    )

    _print_table(
        conn,
        f"SELECT o.id, o.order_number, p.name AS product, o.quantity, o.total_price, o.status, o.customer_name, o.created_at "
        f"FROM orders o JOIN products p ON o.product_id = p.id LIMIT {limit}",
        title=f"[magenta]주문(Order)[/magenta] — 최근 {limit}건",
        columns=["ID", "주문번호", "상품명", "수량", "합계(₩)", "상태", "고객명", "생성일시"],
    )

    conn.close()


@cli.command()
@click.option("--db-path", default=None, help="SQLite DB 파일 경로")
def stats(db_path):
    """DB 요약 통계를 출력합니다."""
    db.init_db(db_path)
    conn = db.get_connection(db_path)

    p = conn.execute("""
        SELECT COUNT(*) total, AVG(price) avg_price, MIN(price) min_price, MAX(price) max_price
        FROM products
    """).fetchone()

    o = conn.execute("""
        SELECT COUNT(*) total, status, SUM(total_price) revenue
        FROM orders GROUP BY status
    """).fetchall()

    table = Table(title="[cyan]상품 통계[/cyan]", box=box.SIMPLE_HEAVY)
    table.add_column("항목"); table.add_column("값", justify="right")
    table.add_row("총 상품 수", f"{p['total']:,}")
    table.add_row("평균 가격", f"₩{p['avg_price']:,.0f}" if p['avg_price'] else "—")
    table.add_row("최저 가격", f"₩{p['min_price']:,.0f}" if p['min_price'] else "—")
    table.add_row("최고 가격", f"₩{p['max_price']:,.0f}" if p['max_price'] else "—")
    console.print(table)

    o_table = Table(title="[magenta]주문 통계 (상태별)[/magenta]", box=box.SIMPLE_HEAVY)
    o_table.add_column("상태"); o_table.add_column("건수", justify="right"); o_table.add_column("매출", justify="right")
    for row in o:
        o_table.add_row(row["status"], f"{row['total']:,}", f"₩{row['revenue']:,.0f}")
    console.print(o_table)

    conn.close()


def _print_table(conn, query: str, title: str, columns: list[str]):
    rows = conn.execute(query).fetchall()
    table = Table(title=title, box=box.SIMPLE_HEAVY, show_lines=False)
    for col in columns:
        table.add_column(col)
    for row in rows:
        table.add_row(*[str(v) if v is not None else "—" for v in row])
    console.print(table)


if __name__ == "__main__":
    cli()
