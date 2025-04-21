CREATE DATABASE IF NOT EXISTS fabric_inventory;
USE fabric_inventory;

-- 1. Suppliers Table (others depend on this)
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_name VARCHAR(100) NOT NULL,
    contact_info VARCHAR(255) NOT NULL,
    address TEXT NOT NULL,
    rating DECIMAL(3,2) DEFAULT NULL
);

-- 2. Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL, 
    password_hash VARCHAR(255) NOT NULL,
    is_confirmed TINYINT(1) DEFAULT 0,
    role ENUM('Admin', 'Inventory Manager', 'Staff Member', 'Business Owner') NOT NULL
);

-- 3. Fabric Inventory Table
CREATE TABLE IF NOT EXISTS fabric_inventory (
    fabric_id INT AUTO_INCREMENT PRIMARY KEY,
    fabric_type VARCHAR(100) NOT NULL,
    color VARCHAR(50) NOT NULL,
    quantity INT NOT NULL,
    price_per_unit DECIMAL(10,2) NOT NULL,
    supplier_id INT,
    restock_threshold INT NOT NULL,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
);

-- 4. Stock Transactions Table
CREATE TABLE IF NOT EXISTS stock_transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    fabric_id INT,
    transaction_type ENUM('Addition', 'Removal', 'Update') NOT NULL,
    quantity_changed INT NOT NULL,
    user_id INT,
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (fabric_id) REFERENCES fabric_inventory(fabric_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 5. Restock Alerts Table
CREATE TABLE IF NOT EXISTS restock_alerts (
    alert_id INT AUTO_INCREMENT PRIMARY KEY,
    fabric_id INT,
    current_stock INT NOT NULL,
    alert_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('Pending', 'Resolved') DEFAULT 'Pending',
    FOREIGN KEY (fabric_id) REFERENCES fabric_inventory(fabric_id)
);

-- 6. Orders Table
CREATE TABLE IF NOT EXISTS orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_id INT,
    fabric_id INT,
    quantity INT NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('Pending', 'Completed', 'Cancelled') DEFAULT 'Pending',
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
    FOREIGN KEY (fabric_id) REFERENCES fabric_inventory(fabric_id)
);

-- 7. Sales Reports Table
CREATE TABLE IF NOT EXISTS sales_reports (
    report_id INT AUTO_INCREMENT PRIMARY KEY,
    generated_by INT,
    report_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    report_data TEXT NOT NULL,
    FOREIGN KEY (generated_by) REFERENCES users(user_id)
);

-- 8. Role-Based Access Table
CREATE TABLE IF NOT EXISTS role_access (
    role_id INT AUTO_INCREMENT PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL,
    permissions TEXT NOT NULL
);
