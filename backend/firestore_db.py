"""
firestore_db.py — Firebase Firestore adapter for ProfitPilot.

Replaces database.py / Supabase PostgreSQL entirely.
No sleeping. No pausing. Always available.

Firestore Collections:
  user_profiles/{uid}              — business profile
  users/{uid}/products/{pid}       — inventory
  users/{uid}/sales/{sid}          — sale transactions
  users/{uid}/bills/{bid}          — invoices
  users/{uid}/alerts/{aid}         — smart alerts
  festival_demands/{slug}          — AI demand cache
"""

from datetime import datetime, timedelta, timezone
from firebase_admin import firestore as _fs
from google.cloud.firestore_v1.base_query import FieldFilter

SERVER_TIMESTAMP = _fs.SERVER_TIMESTAMP


# ── Firestore client ───────────────────────────────────────────────────

def get_db():
    """Return the Firestore client (firebase-admin must already be initialized)."""
    return _fs.client()


# ── Collection references ──────────────────────────────────────────────

def _user_ref(user_id: str):
    return get_db().collection('users').document(user_id)

def products_col(user_id: str):
    return _user_ref(user_id).collection('products')

def sales_col(user_id: str):
    return _user_ref(user_id).collection('sales')

def bills_col(user_id: str):
    return _user_ref(user_id).collection('bills')

def alerts_col(user_id: str):
    return _user_ref(user_id).collection('alerts')

def profiles_col():
    return get_db().collection('user_profiles')

def festival_col():
    return get_db().collection('festival_demands')


# ── Date helpers ───────────────────────────────────────────────────────

def utcnow():
    return datetime.now(timezone.utc)

def days_ago(n: int):
    return datetime.now(timezone.utc) - timedelta(days=n)

def today_start():
    now = datetime.now(timezone.utc)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)

def _ts(dt):
    """Ensure datetime is timezone-aware UTC."""
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    return dt

def _parse_dt(s):
    """Parse ISO string or Firestore timestamp to aware datetime."""
    if s is None:
        return None
    if isinstance(s, datetime):
        return _ts(s)
    if hasattr(s, 'timestamp'):          # Firestore DatetimeWithNanoseconds
        return _ts(s)
    try:
        return datetime.fromisoformat(str(s).replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return None

def _fmt_dt(dt, fmt='%d-%m-%Y %H:%M') -> str:
    """Format datetime for display."""
    if dt is None:
        return 'Never'
    dt = _parse_dt(dt)
    if dt is None:
        return 'Never'
    return dt.strftime(fmt)


# ── Product CRUD ───────────────────────────────────────────────────────

def get_all_products(user_id: str) -> list:
    docs = products_col(user_id).order_by('name').stream()
    return [_doc_to_product(d) for d in docs]

def get_product(user_id: str, product_id: str) -> dict | None:
    doc = products_col(user_id).document(product_id).get()
    return _doc_to_product(doc) if doc.exists else None

def get_product_by_name(user_id: str, name: str) -> dict | None:
    docs = products_col(user_id)\
        .where(filter=FieldFilter('name_lower', '==', name.lower().strip()))\
        .limit(1).stream()
    for d in docs:
        return _doc_to_product(d)
    return None

def get_products_by_categories(user_id: str, categories: list) -> list:
    if not categories:
        return []
    cats = [c.lower() for c in categories][:30]      # Firestore 'in' limit
    docs = products_col(user_id).where(filter=FieldFilter('category', 'in', cats)).stream()
    return [_doc_to_product(d) for d in docs]

def insert_product(user_id: str, name: str, category: str, price: float,
                   stock: int, cost_price: float = None) -> str:
    """Insert and return new document ID."""
    ref = products_col(user_id).document()
    ref.set({
        'user_id': user_id,
        'name': name,
        'name_lower': name.lower(),
        'category': category.lower(),
        'price': float(price),
        'cost_price': float(cost_price) if cost_price else None,
        'stock': int(stock),
        'created_at': SERVER_TIMESTAMP,
        'last_sold_at': None,
    })
    return ref.id

def update_product(user_id: str, product_id: str, **kwargs):
    updates = {}
    if 'name' in kwargs and kwargs['name']:
        updates['name'] = kwargs['name']
        updates['name_lower'] = kwargs['name'].lower()
    if 'price' in kwargs and kwargs['price'] is not None:
        updates['price'] = float(kwargs['price'])
    if 'stock' in kwargs and kwargs['stock'] is not None:
        updates['stock'] = int(kwargs['stock'])
    if 'category' in kwargs and kwargs['category']:
        updates['category'] = kwargs['category'].lower()
    if 'cost_price' in kwargs:
        updates['cost_price'] = float(kwargs['cost_price']) if kwargs['cost_price'] else None
    if updates:
        products_col(user_id).document(product_id).update(updates)

def add_stock(user_id: str, product_id: str, quantity: int) -> int:
    ref = products_col(user_id).document(product_id)
    doc = ref.get()
    if not doc.exists:
        return 0
    new_stock = doc.to_dict().get('stock', 0) + quantity
    ref.update({'stock': new_stock})
    return new_stock

def decrement_stock(user_id: str, product_id: str, quantity: int):
    ref = products_col(user_id).document(product_id)
    ref.update({'stock': _fs.Increment(-quantity)})

def delete_product(user_id: str, product_id: str):
    products_col(user_id).document(product_id).delete()

def _doc_to_product(doc) -> dict:
    d = doc.to_dict()
    d['id'] = doc.id
    if 'created_at' in d and d['created_at'] is not None:
        d['created_at'] = _fmt_dt(d['created_at'])
    if 'last_sold_at' in d and d['last_sold_at'] is not None:
        d['last_sold_at'] = _fmt_dt(d['last_sold_at'])
    return d


# ── Sales CRUD ─────────────────────────────────────────────────────────

def insert_sale(user_id: str, product_id: str, product_name: str,
                category: str, quantity: int, total_price: float,
                sold_at: datetime = None) -> str:
    ref = sales_col(user_id).document()
    ts = _ts(sold_at) if sold_at else SERVER_TIMESTAMP
    ref.set({
        'user_id': user_id,
        'product_id': product_id,
        'product_name': product_name,
        'category': category.lower(),
        'quantity': int(quantity),
        'total_price': float(total_price),
        'sold_at': ts,
    })
    # Update product's last_sold_at timestamp
    products_col(user_id).document(product_id).update({'last_sold_at': ts})
    return ref.id

def get_sales_since(user_id: str, since: datetime) -> list:
    docs = sales_col(user_id)\
        .where(filter=FieldFilter('sold_at', '>=', _ts(since)))\
        .order_by('sold_at').stream()
    return [_doc_to_sale(d) for d in docs]

def get_all_sales(user_id: str) -> list:
    docs = sales_col(user_id).order_by('sold_at').stream()
    return [_doc_to_sale(d) for d in docs]

def _doc_to_sale(doc) -> dict:
    d = doc.to_dict()
    d['id'] = doc.id
    raw = d.get('sold_at')
    d['_sold_at_dt'] = _parse_dt(raw)   # keep raw datetime for aggregation
    d['sold_at'] = _fmt_dt(raw)
    return d


# ── Bill CRUD ──────────────────────────────────────────────────────────

def insert_bill(user_id: str, bill_number: str, customer_name: str,
                items: list, subtotal: float, gst_amount: float,
                total: float) -> str:
    ref = bills_col(user_id).document()
    ref.set({
        'user_id': user_id,
        'bill_number': bill_number,
        'customer_name': customer_name,
        'items': items,
        'subtotal': float(subtotal),
        'gst_amount': float(gst_amount),
        'total': float(total),
        'created_at': SERVER_TIMESTAMP,
    })
    return ref.id

def get_bills(user_id: str, limit: int = 20) -> list:
    docs = bills_col(user_id)\
        .order_by('created_at', direction=_fs.Query.DESCENDING)\
        .limit(limit).stream()
    return [_doc_to_bill(d) for d in docs]

def get_bill(user_id: str, bill_id: str) -> dict | None:
    doc = bills_col(user_id).document(bill_id).get()
    return _doc_to_bill(doc) if doc.exists else None

def search_bills(user_id: str, q: str, limit: int = 20) -> list:
    # Firestore doesn't support LIKE; fetch recent 100 and filter
    docs = bills_col(user_id)\
        .order_by('created_at', direction=_fs.Query.DESCENDING)\
        .limit(100).stream()
    q_lower = q.lower()
    results = []
    for doc in docs:
        b = _doc_to_bill(doc)
        if (q_lower in b.get('bill_number', '').lower() or
                q_lower in b.get('customer_name', '').lower()):
            results.append(b)
            if len(results) >= limit:
                break
    return results

def _doc_to_bill(doc) -> dict:
    d = doc.to_dict()
    d['id'] = doc.id
    raw = d.get('created_at')
    d['created_at'] = _fmt_dt(raw)
    return d


# ── Alert CRUD ─────────────────────────────────────────────────────────

def clear_alerts(user_id: str):
    db = get_db()
    batch = db.batch()
    for doc in alerts_col(user_id).stream():
        batch.delete(doc.reference)
    batch.commit()

def insert_alert(user_id: str, level: str, message: str):
    alerts_col(user_id).add({
        'user_id': user_id,
        'level': level,
        'message': message,
        'created_at': SERVER_TIMESTAMP,
        'is_read': False,
    })

def get_alerts(user_id: str, limit: int = 10) -> list:
    docs = alerts_col(user_id)\
        .order_by('created_at', direction=_fs.Query.DESCENDING)\
        .limit(limit).stream()
    result = []
    for doc in docs:
        d = doc.to_dict()
        d['id'] = doc.id
        result.append(d)
    return result


# ── User profile CRUD ──────────────────────────────────────────────────

def get_user_profile(user_id: str) -> dict | None:
    doc = profiles_col().document(user_id).get()
    if doc.exists:
        d = doc.to_dict()
        d['firebase_uid'] = user_id
        return d
    return None

def upsert_user_profile(user_id: str, data: dict):
    profiles_col().document(user_id).set(data, merge=True)

def delete_user_data(user_id: str):
    """Delete all user data across all collections."""
    db = get_db()
    for col_ref in [products_col(user_id), sales_col(user_id),
                    bills_col(user_id), alerts_col(user_id)]:
        batch = db.batch()
        count = 0
        for doc in col_ref.stream():
            batch.delete(doc.reference)
            count += 1
            if count >= 500:
                batch.commit()
                batch = db.batch()
                count = 0
        if count:
            batch.commit()

    counts = {}
    for name, col_ref in [('products', products_col(user_id)),
                           ('sales', sales_col(user_id)),
                           ('bills', bills_col(user_id)),
                           ('alerts', alerts_col(user_id))]:
        counts[name] = 0  # already deleted
    return counts


# ── Festival demand cache ──────────────────────────────────────────────

def get_festival_demand(festival_name: str) -> dict | None:
    slug = festival_name.lower().replace(' ', '_')
    doc = festival_col().document(slug).get()
    return doc.to_dict() if doc.exists else None

def save_festival_demand(festival_name: str, categories: list,
                         items: list, source: str):
    slug = festival_name.lower().replace(' ', '_')
    festival_col().document(slug).set({
        'festival_name': festival_name,
        'categories': categories,
        'items': items,
        'source': source,
        'created_at': SERVER_TIMESTAMP,
    })


# ── Aggregated metrics (replace complex SQL JOINs) ─────────────────────

def get_bulk_sales_metrics(user_id: str) -> dict:
    """
    Returns per-product sales aggregates for the last 7 days.
    {product_id: {last_7_days_sales, avg_last_7, avg_last_3, avg_prev_3}}
    """
    since = days_ago(7)
    three_ago = days_ago(3)
    six_ago = days_ago(6)

    sales = get_sales_since(user_id, since)
    raw = {}

    for s in sales:
        pid = s['product_id']
        sold_dt = s.get('_sold_at_dt')
        if not sold_dt:
            continue
        sold_dt = _ts(sold_dt)
        qty = s.get('quantity', 0)

        if pid not in raw:
            raw[pid] = {'last_7': 0, 'last_3': 0, 'prev_3': 0}

        raw[pid]['last_7'] += qty
        if sold_dt >= _ts(three_ago):
            raw[pid]['last_3'] += qty
        elif sold_dt >= _ts(six_ago):
            raw[pid]['prev_3'] += qty

    metrics = {}
    for pid, v in raw.items():
        metrics[pid] = {
            'last_7_days_sales': v['last_7'],
            'avg_last_7': v['last_7'] / 7.0,
            'avg_last_3': v['last_3'] / 3.0,
            'avg_prev_3': v['prev_3'] / 3.0,
        }
    return metrics

def get_revenue_summary(user_id: str) -> dict:
    """Today, this week, and previous week revenue totals."""
    since = days_ago(14)
    sales = get_sales_since(user_id, since)

    t_start = _ts(today_start())
    w_start = _ts(days_ago(7))
    pw_start = _ts(days_ago(14))

    today_rev = week_rev = prev_week_rev = 0.0

    for s in sales:
        sold_dt = _ts(s.get('_sold_at_dt'))
        if not sold_dt:
            continue
        price = s.get('total_price', 0)

        if sold_dt >= t_start:
            today_rev += price
        if sold_dt >= w_start:
            week_rev += price
        elif sold_dt >= pw_start:
            prev_week_rev += price

    return {'today': today_rev, 'week': week_rev, 'prev_week': prev_week_rev}

def get_sales_graph(user_id: str, days: int = 7) -> dict:
    """Returns {labels, revenue, units} dicts for the last N days."""
    since = days_ago(days)
    sales = get_sales_since(user_id, since)

    daily = {}
    for s in sales:
        sold_dt = _ts(s.get('_sold_at_dt'))
        if not sold_dt:
            continue
        label = sold_dt.strftime('%d-%m-%Y')
        raw_date = sold_dt.strftime('%Y-%m-%d')
        if label not in daily:
            daily[label] = {'revenue': 0.0, 'units': 0, 'raw_date': raw_date}
        daily[label]['revenue'] += s.get('total_price', 0)
        daily[label]['units'] += s.get('quantity', 0)

    sorted_days = sorted(daily.items(), key=lambda x: x[1]['raw_date'])
    return {
        'labels':  [d[0] for d in sorted_days],
        'revenue': [round(d[1]['revenue'], 2) for d in sorted_days],
        'units':   [d[1]['units'] for d in sorted_days],
    }

def get_category_revenue(user_id: str, days: int = 30) -> list:
    """Revenue breakdown by product category."""
    since = days_ago(days)
    sales = get_sales_since(user_id, since)

    cat_rev = {}
    for s in sales:
        cat = s.get('category', 'general').lower()
        cat_rev[cat] = cat_rev.get(cat, 0) + s.get('total_price', 0)

    return [{'category': c, 'revenue': round(r, 2)}
            for c, r in sorted(cat_rev.items(), key=lambda x: -x[1])]

def get_top_products_by_qty(user_id: str, limit: int = 5, days: int = 30) -> list:
    """Return top-selling products by quantity in last N days."""
    since = days_ago(days)
    sales = get_sales_since(user_id, since)

    prod_qty = {}
    prod_name = {}
    for s in sales:
        pid = s['product_id']
        prod_qty[pid] = prod_qty.get(pid, 0) + s.get('quantity', 0)
        prod_name[pid] = s.get('product_name', pid)

    top = sorted(prod_qty.items(), key=lambda x: -x[1])[:limit]
    return [{'product_id': pid, 'name': prod_name.get(pid, ''), 'total_qty': qty}
            for pid, qty in top]

def get_revenue_all_time(user_id: str) -> dict:
    """Total revenue, category breakdown, and active sales days (for tax)."""
    sales = get_all_sales(user_id)

    total_rev = 0.0
    category_rev = {}
    sales_days = set()

    for s in sales:
        total_rev += s.get('total_price', 0)
        cat = s.get('category', 'general').lower()
        category_rev[cat] = category_rev.get(cat, 0) + s.get('total_price', 0)
        sold_dt = s.get('_sold_at_dt')
        if sold_dt:
            sales_days.add(_ts(sold_dt).strftime('%Y-%m-%d'))

    return {
        'total_revenue': total_rev,
        'category_revenue': category_rev,
        'active_sales_days': len(sales_days) or 1,
    }

def get_active_sales_days(user_id: str, days: int = 7) -> int:
    """Count distinct days with at least one sale in last N days."""
    sales = get_sales_since(user_id, days_ago(days))
    day_set = set()
    for s in sales:
        sold_dt = s.get('_sold_at_dt')
        if sold_dt:
            day_set.add(_ts(sold_dt).strftime('%Y-%m-%d'))
    return len(day_set)

def count_bills(user_id: str, days: int = 7) -> int:
    """Count bills created in last N days."""
    since = days_ago(days)
    docs = bills_col(user_id)\
        .where(filter=FieldFilter('created_at', '>=', _ts(since)))\
        .stream()
    return sum(1 for _ in docs)


# ── Demo user seed ─────────────────────────────────────────────────────

DEMO_PRODUCTS = [
    ('Tata Salt (1kg)',          'grocery',       28.0,  100),
    ('Aashirvaad Atta (5kg)',    'grocery',       245.0,  50),
    ('Fortune Sunflower Oil',   'grocery',       145.0,  40),
    ('Sugar (1kg)',              'grocery',        48.0,  80),
    ('Parle-G Biscuits',        'packaged_food',  20.0, 120),
    ('Haldiram Namkeen (400g)', 'snacks',        120.0,  60),
    ('Amul Butter (500g)',      'dairy',         270.0,  25),
    ('Dettol Handwash (200ml)', 'personal_care', 115.0,  50),
    ('Colgate Toothpaste',      'personal_care',  95.0,  45),
    ('Syska LED Bulb 9W',       'electronics',    89.0,  30),
    ('Toor Dal (1kg)',           'grocery',       140.0,  50),
    ('Coconut Oil (500ml)',      'grocery',       130.0,  35),
]

def seed_demo_user():
    """Seed demo user with sample products if the collection is empty."""
    existing = list(products_col('demo').limit(1).stream())
    if existing:
        return
    for name, category, price, stock in DEMO_PRODUCTS:
        insert_product('demo', name, category, price, stock)
