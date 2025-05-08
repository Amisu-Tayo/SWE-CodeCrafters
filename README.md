# 🧵 Fabric Inventory Management System

## Team Members
| Name                 | Role      |
|----------------------|-----------|
| Haleemah Amisu       | Developer |
| Joseph Frishkorn     | TBD       |
| Aastha Bhatt         | TBD       |
| Bhuvan Angiraa       | TBD       |
| Sai Manaswini Utla   | TBD       |

---

## Project Overview
FIMS is a full-stack web application that helps a small fabric business track inventory, sales, orders, usage trends, and restock alerts.  
The user-facing dashboard and chat widget are served as static pages (hosted at [fims.store](https://fims.store)), while the back end provides a RESTful API (AWS SAM + Lambda locally, MySQL) for inventory, orders, usage, AI suggestions, and advanced reports.

---

##  Features
- **Dashboard**  
  - Total items by fabric  
  - Pending orders count  
  - Low-stock alert count  
  - Monthly usage  
  - AI-powered trend suggestions and chat bot

- **API Endpoints**  
  - **Inventory** (`GET`, `POST`, `PUT`, `DELETE`)  
  - **Orders** (`GET`, `POST`, `PUT`, `DELETE`)  
  - **Usage** (`GET` total usage over last 30 days)  
  - **Reports** (multiple charts: current inventory, sales by fabric, pending orders, usage trend, restock alerts)  
  - **FIMAI** (`/api/fimai` for suggestions, `/api/fimai/chat` for conversational queries)

- **AI Time Series**  
  - Pretrained Prophet models per fabric (`.pkl`) for next-month forecasting  
  - Trends data in `models/trends.json`

- **Tech Stack**  
  - Front-end: HTML/CSS/JS + Bootstrap + Chart.js  
  - Back-end: Python 3.9, Flask (Lambda), AWS SAM, Mangum, MySQL (via `db_config.py`)  
  - AI: Facebook Prophet models, pickled  



## 📁 Folder Structure

/
├── lambda_src/               # AWS SAM–based back end
│   ├── api/                  # “native” Lambda handlers (inventory, orders, usage, reports…)
│   │   ├── inventory.py
│   │   ├── inventory_item.py
│   │   ├── orders.py
│   │   ├── order_item.py
│   │   ├── usage.py
│   │   └── reports.py
│   ├── fimai/                # FIMAI Flask app (forecast + chat)
│   │   ├── fimai.py
│   │   ├── db_config.py
│   │   └── models/           # pickled Prophet models + trends.json
│   ├── template.yaml         # AWS SAM template
│   └── requirements.txt
├── public/                   # Static front-end (dashboard.html, reports.html, etc.)
├── run.py                    # Local development entry point
├── db_config.py              # Shared MySQL connection logic
├── requirements.txt          # Top-level Python dependencies
└── .env                      # Environment variables (DB_*, etc.; available on request to Dr. Akshita)

## Prerequisites

- **Python 3.9+**  
- **MySQL** database matching the schema (`fabric_inventory`, `stock_transactions`, etc.)  
- **Node.js** (only if you wish to rebuild the front-end assets)  

## Local Setup

1. **Environment**  
   Create a `.env` file at the project root (this contains your `DB_HOST`, `DB_USER`, `DB_PASS`, `DB_NAME`).  
   > _Note: the `.env` file is not committed; I can provide it upon request._

2. **Install dependencies**  
Run your SQL schema scripts (e.g. those in SqlTables/) against your MySQL instance.

4.	Start the application
# From project root
python run.py
or visit the website at https://fims.store

5. link to video demo:
https://drive.google.com/file/d/1TZxM5vs0A3uKS2NJhl5_JYpyaQ73rtf6/view?usp=sharing


