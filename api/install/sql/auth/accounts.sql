CREATE TABLE accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password VARCHAR(200) NOT NULL,  -- Store hashed password
    joined DATETIME DEFAULT CURRENT_TIMESTAMP,  -- Timestamp of when the account was created
    last_login DATETIME DEFAULT NULL,  -- Timestamp of the last login
    online TINYINT(1) DEFAULT 0  -- 0 for offline, 1 for online
);

