DROP TABLE IF EXISTS products;

CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    price INTEGER NOT NULL
);

INSERT INTO products (name, price) VALUES ('محصول 1', 1000);
INSERT INTO products (name, price) VALUES ('محصول 2', 2000);
INSERT INTO products (name, price) VALUES ('محصول 3', 3000);
