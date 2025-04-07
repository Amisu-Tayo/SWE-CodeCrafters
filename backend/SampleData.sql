USE fabric_inventory;

-- Insert roles
INSERT INTO role_access (role_name, permissions) VALUES
('Admin', 'all'),
('Inventory Manager', 'view,add,edit'),
('Staff Member', 'view'),
('Business Owner', 'view,reports');

-- Insert users
INSERT INTO users (username, password_hash, role) VALUES
('admin_user', 'hashedpass1', 'Admin'),
('manager1', 'hashedpass2', 'Inventory Manager'),
('staff1', 'hashedpass3', 'Staff Member');

-- Insert suppliers
INSERT INTO suppliers (supplier_name, contact_info, address, rating) VALUES
('Silk Central', 'silk@example.com', '123 Silk Rd', 4.5),
('Cotton Co.', 'cotton@example.com', '456 Cotton Ln', 4.2);

-- Insert fabric inventory
INSERT INTO fabric_inventory (fabric_type, color, quantity, price_per_unit, supplier_id, restock_threshold) VALUES
('Cotton', 'White', 25, 4.50, 2, 10),
('Silk', 'Blue', 10, 8.75, 1, 5);

-- Insert stock transactions
INSERT INTO stock_transactions (fabric_id, transaction_type, quantity_changed, user_id) VALUES
(1, 'Addition', 25, 2),
(2, 'Addition', 10, 1);

-- Insert restock alerts
INSERT INTO restock_alerts (fabric_id, current_stock) VALUES
(2, 10);

-- Insert orders
INSERT INTO orders (supplier_id, fabric_id, quantity) VALUES
(1, 2, 20),
(2, 1, 50);

-- Insert sales report
INSERT INTO sales_reports (generated_by, report_data) VALUES
(1, '{"sales": [{"fabric": "Cotton", "qty": 12}]}');

SELECT * FROM users;
SELECT * FROM fabric_inventory;

