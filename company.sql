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

DELETE FROM users WHERE user_email = "henrylundbergnavntoft@gmail.com";

UPDATE users SET user_deleted_at = 0 WHERE user_email = "customer@company.com";

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


SELECT * FROM item_images 
        INNER JOIN items ON item_images.item_fk = items.item_pk 
        WHERE items.item_is_blocked = 0 
        ORDER BY item_created_at











































