# dakshjasoliya.github.io
My cybersecurity portfolio showcasing penetration testing, bug bounty disclosures, and digital forensics case work..

# Construction PM App — Intentionally Vulnerable VAPT Lab

A Django-based construction project-management application, built from scratch and deliberately reintroduced with common web vulnerabilities — designed as a self-contained lab for practicing Vulnerability Assessment & Penetration Testing (VAPT).

> ⚠️ **Disclaimer:** This application is intentionally vulnerable. It is built strictly for educational and security-research purposes. Do **not** deploy this on a public server or use it in production.

## Why this exists

Most VAPT practice happens on apps someone else built. This one I designed and coded myself — admin panel, client panel, database, the works — so I could control exactly which flaws to introduce and document the full exploitation path end to end, the way a real assessment report would.

## Vulnerabilities covered

| Vulnerability | Where |
|---|---|
| SQL Injection | Login & search forms |
| IDOR (Insecure Direct Object Reference) | Client project access endpoints |
| XSS (Cross-Site Scripting) | Comment / project update fields |
| CSRF | State-changing admin actions |
| Privilege Escalation | Client → Admin panel boundary |
| File Upload Abuse | Project document upload |
| User Enumeration | Login & password reset flow |

## Tech stack

- Python / Django
- SQLite
- HTML/CSS (Django templates)

## Setup

```bash
git clone https://github.com/dekx1840-oss/dakshjasoliya.github.io
cd dakshjasoliya.github.io
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
password and all
python manage.py runserver
```

Visit `http://127.0.0.1:8000` in your browser.

## How it's tested

All exploitation was carried out using **Burp Suite** as a local intercepting proxy, working through each vulnerability class systematically — confirming the flaw, documenting the request/response, and recording the impact.

## Status

Actively maintained — new vulnerability classes and a written exploitation walkthrough are being added.

## Author

**Daksh Jasoliya** — B.Tech Cyber Security, Gandhinagar University
[LinkedIn](https://www.linkedin.com/in/jasoliya-daksh)
