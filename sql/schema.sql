-- schema.sql: create tables
CREATE TABLE IF NOT EXISTS departments (
  id INTEGER PRIMARY KEY,
  dept_name TEXT NOT NULL,
  location TEXT
);

CREATE TABLE IF NOT EXISTS employees (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  dept_id INTEGER,
  salary INTEGER,
  hire_date TEXT,
  email TEXT,
  FOREIGN KEY(dept_id) REFERENCES departments(id)
);

CREATE TABLE IF NOT EXISTS orders (
  order_id INTEGER PRIMARY KEY,
  customer_name TEXT,
  order_date TEXT,
  amount REAL,
  employee_id INTEGER,
  status TEXT
);

CREATE TABLE IF NOT EXISTS practice_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  topic TEXT,
  question_title TEXT,
  query_text TEXT,
  user_note TEXT,
  rows_returned INTEGER,
  exec_time_ms INTEGER
);
