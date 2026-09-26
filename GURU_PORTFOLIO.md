# Guru portfolio entries

Portfolio descriptions for the sample projects in [ihsan-yasir/python-web-portfolio](https://github.com/ihsan-yasir/python-web-portfolio).

## Northline — Python Business Website

A working sample business website for a fictional consulting brand. Built with Python's standard library and SQLite, the application includes service sections, responsive layouts and a contact form with server-side validation. Valid submissions are stored locally and a confirmation is displayed.

**Features:** service cards, navigation, desktop/mobile layout rules, enquiry validation, SQLite storage, CSRF protection.

**Technology:** Python, SQLite, Python-generated HTML and CSS. No JavaScript or third-party packages.

**Scope:** Independent, AI-assisted portfolio demo. No email service is connected.

**Source:** `https://github.com/ihsan-yasir/python-web-portfolio/blob/main/business_website.py`

## Forma — Python Store with Shopping Cart

A working sample homeware storefront featuring a searchable catalogue, browser-session shopping cart, quantity updates, item removal and simulated checkout. Order totals are calculated on the server using integer cents, and completed demo orders are stored with their line items in SQLite.

**Features:** product search, isolated carts, quantity validation, cart totals, order persistence and confirmation.

**Technology:** Python, SQLite, Python-generated HTML and CSS. No JavaScript or third-party packages.

**Scope:** Independent, AI-assisted portfolio demo. Checkout is simulated; payments, shipping, taxes and inventory integrations are not connected.

**Source:** `https://github.com/ihsan-yasir/python-web-portfolio/blob/main/online_store.py`

## Taskboard — Python Task Management Dashboard

A working task dashboard with a persistent SQLite database. Users can add tasks, assign project names and due dates, change status, delete tasks, and filter by text or status. Summary cards and a completion bar update from the stored task data.

**Features:** task creation, status changes, deletion, search, filtering, overdue count, completion percentage and persistent data.

**Technology:** Python, SQLite, Python-generated HTML and CSS. No JavaScript or third-party packages.

**Scope:** Independent, AI-assisted portfolio demo for local use. The workspace is shared and does not include user authentication.

**Source:** `https://github.com/ihsan-yasir/python-web-portfolio/blob/main/management_dashboard.py`

## Presentation notes

- Use screenshots of the running applications, not the earlier AI-generated concept mockups, as evidence of the completed implementation.
- Each launcher imports the implementation from `app.py`; include that shared file when publishing any individual project.
- The supplied test suite contains nine automated tests covering the core workflows and validation. They passed locally on Python 3.12. See the repository Actions tab for hosted checks.
- Browser visual verification remains pending.
- Repository links show source code. A public live demo requires separate Python hosting and production hardening.
