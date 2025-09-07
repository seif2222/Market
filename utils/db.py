import os
import sqlite3
from typing import Dict, List, Optional

import qrcode

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data.sqlite3")
QR_DIR_DEFAULT = os.path.join(BASE_DIR, "static", "qr")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    os.makedirs(QR_DIR_DEFAULT, exist_ok=True)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            price_egp REAL NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0,
            date_added TEXT NOT NULL,
            qr_path TEXT
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_date TEXT NOT NULL,
            total_egp REAL NOT NULL,
            print_lang TEXT
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL,
            product_id TEXT NOT NULL,
            name TEXT NOT NULL,
            price_egp REAL NOT NULL,
            quantity INTEGER NOT NULL,
            line_total REAL NOT NULL,
            FOREIGN KEY(sale_id) REFERENCES sales(id)
        );
        """
    )
    conn.commit()
    conn.close()


def _generate_qr_for_product(product_id: str, qr_dir: Optional[str] = None) -> str:
    qr_dir = qr_dir or QR_DIR_DEFAULT
    os.makedirs(qr_dir, exist_ok=True)
    img = qrcode.make(product_id)
    file_path = os.path.join(qr_dir, f"{product_id}.png")
    img.save(file_path)
    return file_path


def upsert_product(product_id: str, name: str, price_egp: float, quantity: int, date_added: str, qr_dir: Optional[str] = None) -> None:
    conn = get_connection()
    cur = conn.cursor()
    qr_path = _generate_qr_for_product(product_id, qr_dir)
    cur.execute(
        """
        INSERT INTO products (product_id, name, price_egp, quantity, date_added, qr_path)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(product_id) DO UPDATE SET
            name=excluded.name,
            price_egp=excluded.price_egp,
            quantity=excluded.quantity,
            date_added=excluded.date_added,
            qr_path=excluded.qr_path
        """,
        (product_id, name, price_egp, quantity, date_added, qr_path),
    )
    conn.commit()
    conn.close()


def fetch_all_products() -> List[sqlite3.Row]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT product_id, name, price_egp, quantity, date_added, qr_path FROM products ORDER BY date_added DESC, name ASC")
    rows = cur.fetchall()
    conn.close()
    return rows


def fetch_product_by_product_id(product_id: str) -> Optional[sqlite3.Row]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT product_id, name, price_egp, quantity, date_added, qr_path FROM products WHERE product_id = ?", (product_id,))
    row = cur.fetchone()
    conn.close()
    return row


def delete_product_by_product_id(product_id: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
    conn.commit()
    conn.close()


def create_sale_with_items(sale_date: str, items: List[Dict], total_egp: float) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO sales (sale_date, total_egp, print_lang) VALUES (?, ?, ?)", (sale_date, total_egp, None))
    sale_id = cur.lastrowid
    for item in items:
        cur.execute(
            """
            INSERT INTO sale_items (sale_id, product_id, name, price_egp, quantity, line_total)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                sale_id,
                item["product_id"],
                item["name"],
                item["price_egp"],
                item["quantity"],
                item["line_total"],
            ),
        )
    conn.commit()
    conn.close()
    return sale_id


def decrement_product_stock(product_id: str, quantity: int) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE products SET quantity = MAX(quantity - ?, 0) WHERE product_id = ?",
        (quantity, product_id),
    )
    conn.commit()
    conn.close()


def fetch_sales_report(period: str, date_str: str):
    conn = get_connection()
    cur = conn.cursor()
    if period == "monthly":
        # date_str: YYYY-MM
        cur.execute(
            """
            SELECT sale_date, total_egp, print_lang FROM sales
            WHERE substr(sale_date, 1, 7) = ?
            ORDER BY sale_date DESC
            """,
            (date_str,),
        )
    else:
        # daily, date_str: YYYY-MM-DD
        cur.execute(
            """
            SELECT sale_date, total_egp, print_lang FROM sales
            WHERE substr(sale_date, 1, 10) = ?
            ORDER BY sale_date DESC
            """,
            (date_str,),
        )
    rows = cur.fetchall()
    total_sum = sum([row["total_egp"] for row in rows]) if rows else 0.0
    conn.close()
    return rows, total_sum