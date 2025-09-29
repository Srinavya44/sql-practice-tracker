-- seed.sql: sample data for departments, employees, orders
INSERT INTO departments (id, dept_name, location) VALUES
(1, 'IT', 'Pune'),
(2, 'HR', 'Bengaluru'),
(3, 'Finance', 'Mumbai'),
(4, 'Sales', 'Delhi'),
(5, 'Support', 'Chennai');

INSERT INTO employees (id, name, dept_id, salary, hire_date, email) VALUES
(1, 'Riya', 1, 50000, '2021-06-10', 'riya@example.com'),
(2, 'Kabir', 4, 42000, '2020-01-20', 'kabir@example.com'),
(3, 'Sneha', 3, 60000, '2019-11-05', 'sneha@example.com'),
(4, 'Arjun', 1, 75000, '2018-03-15', 'arjun@example.com'),
(5, 'Meera', 2, 38000, '2022-08-25', 'meera@example.com'),
(6, 'Vikram', 4, 47000, '2023-01-03', 'vikram@example.com'),
(7, 'Latha', 5, 35000, '2021-12-12', 'latha@example.com'),
(8, 'Aditya', 1, 82000, '2017-05-30', 'aditya@example.com'),
(9, 'Priya', 3, 61000, '2020-09-19', 'priya@example.com'),
(10,'Karan', 4, 45000, '2022-03-03', 'karan@example.com');

INSERT INTO orders (order_id, customer_name, order_date, amount, employee_id, status) VALUES
(1001, 'Alpha Corp', '2024-01-10', 1200.50, 2, 'Completed'),
(1002, 'Beta LLC', '2024-02-01', 540.00, 6, 'Completed'),
(1003, 'Gamma Ltd', '2024-02-15', 2300.00, 8, 'Completed'),
(1004, 'Delta Inc', '2024-03-12', 80.00, 7, 'Cancelled'),
(1005, 'Epsilon Co', '2024-04-05', 760.00, 2, 'Completed'),
(1006, 'Zeta Pvt', '2024-04-23', 420.75, 10, 'Pending'),
(1007, 'Eta Group', '2024-05-01', 150.00, 6, 'Completed'),
(1008, 'Theta Traders', '2024-05-14', 980.00, 3, 'Completed'),
(1009, 'Iota Services', '2024-05-20', 1299.99, 8, 'Completed'),
(1010, 'Kappa Works', '2024-06-02', 60.00, NULL, 'Pending');
