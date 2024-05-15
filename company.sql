-- Hashed passsword is: $2b$12$V/cXqWN/M2vTnYUcXMB9oODcNBX/QorJekmaDkq1Z7aeD3I5ZAjfu
-- Password for admin is: password
------------------------------------------------------------

DROP TABLE IF EXISTS users;

CREATE TABLE users(
    user_pk                 TEXT,
    user_username           TEXT,
    user_first_name         TEXT,
    user_last_name          TEXT,
    user_email              TEXT UNIQUE,
    user_password           TEXT,
    user_role               TEXT,
    user_created_at         INTEGER,
    user_updated_at         INTEGER,
    user_deleted_at         INTEGER,
    user_is_verified        INTEGER,
    user_is_blocked         INTEGER,
    PRIMARY KEY(user_pk)
) WITHOUT ROWID;

INSERT INTO users VALUES(
    "d11854217ecc42b2bb17367fe33dc8f4",
    "admin",
    "Admin",
    "Company",
    "admin@company.com",
    "$2b$12$V/cXqWN/M2vTnYUcXMB9oODcNBX/QorJekmaDkq1Z7aeD3I5ZAjfu",
    "admin",
    1,
    0,
    0,
    1,
    0
);

INSERT INTO users VALUES(
    "d11854217ecc42b2bb17367fe33dc8f5",
    "Customer",
    "Customer",
    "Customer",
    "customer@company.com",
    "$2b$12$V/cXqWN/M2vTnYUcXMB9oODcNBX/QorJekmaDkq1Z7aeD3I5ZAjfu",
    "customer",
    1,
    0,
    0,
    1,
    0
);

SELECT * FROM users;

------------------------------------------------------------

DROP TABLE IF EXISTS items;

CREATE TABLE items(
    item_pk                 TEXT,
    item_name               TEXT,
    item_description        TEXT,
    item_splash_image       TEXT,
    item_lat                TEXT,
    item_lon                TEXT,
    item_stars              REAL,
    item_price_per_night    REAL,
    item_created_at         INTEGER,
    item_updated_at         INTEGER,
    item_deleted_at         INTEGER,
    item_is_blocked         INTEGER,
    item_is_booked          INTEGER,
    item_owner_fk           TEXT,
    FOREIGN KEY(item_owner_fk) REFERENCES users(user_pk),
    PRIMARY KEY(item_pk)
) WITHOUT ROWID;

INSERT INTO items VALUES
("5dbce622fa2b4f22a6f6957d07ff4951", "Christiansborg Palace", "", "5dbce622fa2b4f22a6f6957d07ff4951.webp", 55.6761, 12.5770, 5, 2541, 1, 0, 0, 0, 0, "5dbce622fa2b4f22a6f6957d07ff4951"),
("5dbce622fa2b4f22a6f6957d07ff4952", "Tivoli Gardens", "", "5dbce622fa2b4f22a6f6957d07ff4952.webp", 55.6736, 12.5681, 4.97, 985, 2, 0, 0, 0, 0, "5dbce622fa2b4f22a6f6957d07ff4952");

SELECT * FROM items;



------------------------------------------------------------

DROP TABLE IF EXISTS item_images;

CREATE TABLE item_images (
    item_fk           TEXT,
    image_url         TEXT,
    FOREIGN KEY(item_fk) REFERENCES items(item_pk)
    PRIMARY KEY (item_fk, image_url)
) WITHOUT ROWID;

SELECT * FROM item_images;



------------------------------------------------------------ 






SELECT * FROM users WHERE user_email = "henrylnavntoft@gmail.com" LIMIT 1

UPDATE users SET user_deleted_at = 0 WHERE user_pk = "aa57400551044c3d8c0bd1f794a1468a"




INSERT INTO item_images (item_fk, image_url) VALUES
("5dbce622fa2b4f22a6f6957d07ff4951", "5dbce622fa2b4f22a6f6957d07ff4951_image1.webp"),
("5dbce622fa2b4f22a6f6957d07ff4951", "5dbce622fa2b4f22a6f6957d07ff4951_image2.webp"),
("5dbce622fa2b4f22a6f6957d07ff4951", "5dbce622fa2b4f22a6f6957d07ff4951_image3.webp");







SELECT items.item_pk, items.item_name, item_images.image_url
FROM items
JOIN item_images ON items.item_pk = item_images.item_fk
WHERE items.item_pk = "57dad0858a6648d58d764efa072751dd";





















-- (page_number - 1) * items_per_page
-- (1 - 1) * 3 = 10 1 2
-- (2 - 1) * 3 = 3 4 5
-- (3 - 1) * 3 = 6 7 8


-- Page 4
-- 0 3 6 9
SELECT * FROM items 
ORDER BY item_created_at
LIMIT 9,3;


-- offset = (currentPage - 1) * itemsPerPage
-- page 1 = 1 2 3+
-- page 2 = 4 5 6
-- page 3 = 7 8 9
-- page 4 = 10
SELECT * FROM items 
ORDER BY item_created_at
LIMIT 3 OFFSET 9;

















