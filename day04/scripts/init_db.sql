-- init_db.sql — Day 04 eComBot seed schema

CREATE TABLE IF NOT EXISTS orders (
    order_id       VARCHAR(20) PRIMARY KEY,
    customer_name  VARCHAR(100) NOT NULL,
    status         VARCHAR(20) NOT NULL,
    eta            DATE NOT NULL,
    carrier        VARCHAR(50) NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS products (
    product_id     VARCHAR(20) PRIMARY KEY,
    name           VARCHAR(120) NOT NULL,
    category       VARCHAR(80) NOT NULL,
    price_inr      NUMERIC(10,2) NOT NULL,
    in_stock       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS session_history (
    id          BIGSERIAL PRIMARY KEY,
    session_id  VARCHAR(100) NOT NULL,
    user_id     VARCHAR(100) NOT NULL,
    role        VARCHAR(20) NOT NULL,
    content     TEXT NOT NULL,
    tool_calls  JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_sh_session ON session_history (session_id, created_at);

INSERT INTO orders (order_id, customer_name, status, eta, carrier)
VALUES
    ('ORD-001', 'Priya Sharma', 'Shipped', '2026-06-20', 'BlueDart'),
    ('ORD-002', 'Ravi Patel', 'Processing', '2026-06-22', 'DTDC'),
    ('ORD-003', 'Aisha Mehta', 'Delivered', '2026-06-14', 'FedEx'),
    ('ORD-004', 'James Liu', 'Confirmed', '2026-06-24', 'Delhivery'),
    ('ORD-005', 'Maria Santos', 'Cancelled', '2026-06-25', 'Ecom Express')
ON CONFLICT (order_id) DO NOTHING;

INSERT INTO products (product_id, name, category, price_inr, in_stock)
VALUES
    ('PRD-101', 'Pixel 8a', 'phone', 39999.00, TRUE),
    ('PRD-102', 'Galaxy A55', 'phone', 35999.00, TRUE),
    ('PRD-103', 'Redmi Note 13', 'phone', 17999.00, TRUE),
    ('PRD-201', 'OnePlus Buds 3', 'earbuds', 5499.00, TRUE),
    ('PRD-202', 'Sony WH-CH520', 'headphones', 4499.00, FALSE)
ON CONFLICT (product_id) DO NOTHING;
