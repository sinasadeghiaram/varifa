# Varifa — Business Management Suite for Small Businesses

**Varifa** is a desktop business-management suite (accounting, inventory, manufacturing, payroll, invoicing, CRM) built for small and mid-sized businesses in Iran. I designed and built it end to end as founder and lead developer.

🌐 Website: [varifa.ir](https://varifa.ir)

> The source code is private. This repository is a technical overview of the product and how it is built.

<!-- Screenshots: add 3–4 images to /screenshots and uncomment
![Dashboard](screenshots/dashboard.png)
![Invoice](screenshots/invoice.png)
-->

## What it does

- **Accounting** — transactions, accounts, customers & suppliers, cheque management, fixed debts
- **Invoicing** — proforma → invoice conversion, PDF invoice generation
- **Inventory** — multiple warehouses, stock levels and low-stock alerts
- **Manufacturing** — bills of materials, production orders, overhead allocation into product cost
- **Payroll** — salary, social-security insurance, tax tables, severance and year-end bonus; all rates configurable because regulations change every year
- **CRM** — sales opportunities and activities
- **Reports & dashboard** — daily overview of the business
- **Multi-workstation** — any number of PCs on a local network share one company database
- **WooCommerce sync** — online-store orders flow into the desktop app automatically
- **Optional AI assistant** — bring-your-own-key, off by default
- **Licensing** — trial management, license bound to the company installation (not to each PC), signed online checks with a long offline grace period

## Tech stack

| Layer | Technology |
|---|---|
| Desktop app | Python, PySide6 (Qt), right-to-left (Persian) UI, Jalali calendar |
| Database | PostgreSQL with automatic schema migrations on start-up |
| Backend API | FastAPI, Nginx, Ubuntu server |
| Website | Server-rendered pages (Jinja2) with a custom block-based CMS |
| Payments | Online payment-gateway integration |
| Integrations | WooCommerce sync plugin (WordPress) |
| Packaging | PyInstaller + Inno Setup Windows installer that also sets up PostgreSQL |

## Architecture (high level)

```
Desktop app (PySide6) ──► PostgreSQL (auto-migrations, shared on LAN)
        │
        └──► FastAPI backend ──► licensing, cloud backup, store sync
                                     │
Website (varifa.ir) ◄────────────────┘   payments, customer panel & downloads
```

- 30,000+ lines of Python in the desktop app
- Shared invoice engine module used across screens
- Migration-first start-up so every install has the full schema

## Code samples

The [`samples/`](samples) folder has two small standalone modules with tests: Jalali calendar conversion and the migration-first start-up runner. See [samples/README.md](samples/README.md).

## Roadmap

- Web version of Varifa
- E-invoicing integration with the national tax system
- In-app auto-update
- Voice-to-invoice

## About me

I'm Sina Sadeghiaram, a web developer and product builder (Python, WordPress, WooCommerce, PHP, Node.js).
[LinkedIn](https://www.linkedin.com/in/sina-sadeghiaram-49319996) · [hamberweb.com](https://hamberweb.com)
