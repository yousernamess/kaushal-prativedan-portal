# AI_RULES.md

These rules must always be followed during development.

## General

* Read PROJECT_SPEC.md before implementing anything.
* Do not invent new features unless explicitly requested.
* Prefer maintainability over clever code.
* Keep code modular.

---

## Backend

* Use FastAPI.
* Use SQLAlchemy ORM.
* Use Alembic migrations.
* Use Pydantic models.
* Use dependency injection where appropriate.
* Keep routes thin.
* Put business logic into service classes.
* Never place OpenCV logic inside API routes.

---

## Database

* Never change the schema without an Alembic migration.
* Use foreign keys correctly.
* Use indexes where appropriate.
* Prefer soft deletes for Assessments.
* Student IDs are the internal primary keys.

---

## Frontend

* Use React + TypeScript.
* Use shadcn/ui components.
* Use TailwindCSS.
* Use TanStack Query for server state.
* Use React Hook Form for forms.
* Build responsive pages.

### Master Data

* Master Data is a single page (`/master-data`) with tabs: Schools, Academic Years, Sections, Students.
* Schools and Academic Years use the generic `CrudPage` component.
* Sections uses a custom page with bulk creation dialog.
* Students uses a custom page with add/edit forms, cascading dropdowns, and CSV import dialog.
* Never expose raw database IDs in the UI.
* Use dropdowns for foreign key fields (school, class, section).
* Use `customDeleteDialog` prop on `CrudPage` when the default delete dialog is insufficient (e.g., Schools with students).

### Components

* `CrudPage` — generic CRUD page with table, create/edit/delete dialogs.
* `FormDialog` — modal form with validation, required indicators, loading state.
* `DeleteConfirmationDialog` — confirmation dialog with custom title/message.
* `DataTable` — table with columns and optional actions.
* `PageHeader` — page title with optional action button.
* `SearchBar` — search input.
* `Toast` — toast notification provider.

---

## OMR

* Treat the OMR engine as a black box.
* Assume it returns JSON.
* Never rewrite the OMR algorithm.
* Delete uploaded images after processing.

---

## Reports

* Reports are generated on demand.
* Reports are never stored.
* PDFs are generated only when requested.

---

## Code Quality

* Use type hints.
* Use meaningful names.
* Write reusable components.
* Avoid duplicated code.
* Document public functions.

---

## Git

Every milestone should result in a working application.

Commit after every completed feature.

Never leave the project in a broken state.

---

## Development Order

Always follow the milestones defined in TASKS.md.

Do not skip ahead.

Complete one milestone before beginning the next.
