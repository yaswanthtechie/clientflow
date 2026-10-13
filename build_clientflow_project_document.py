from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_BREAK


OUT = "ClientFlow_One_Month_Project_Plan.docx"
NAVY = "4F6D7A"
MID_BLUE = "E1EAED"
PALE_BLUE = "F4F7F8"
LIGHT_GRAY = "D9D9D9"
TEXT = "2F3A40"


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)
    shd.set(qn("w:val"), "clear")


def set_cell_border(cell, color=LIGHT_GRAY, size="6"):
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = tc_pr.first_child_found_in("w:tcBorders")
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tc_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = qn(f"w:{edge}")
        element = borders.find(tag)
        if element is None:
            element = OxmlElement(f"w:{edge}")
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), size)
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), color)


def set_cell_margins(cell, top=90, start=100, bottom=90, end=100):
    tc_pr = cell._tc.get_or_add_tcPr()
    mar = tc_pr.first_child_found_in("w:tcMar")
    if mar is None:
        mar = OxmlElement("w:tcMar")
        tc_pr.append(mar)
    for side, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = mar.find(qn(f"w:{side}"))
        if node is None:
            node = OxmlElement(f"w:{side}")
            mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def keep_with_next(paragraph):
    p_pr = paragraph._p.get_or_add_pPr()
    p_pr.append(OxmlElement("w:keepNext"))


def prevent_row_split(row):
    tr_pr = row._tr.get_or_add_trPr()
    tr_pr.append(OxmlElement("w:cantSplit"))


def set_repeat_table_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    marker = OxmlElement("w:tblHeader")
    marker.set(qn("w:val"), "true")
    tr_pr.append(marker)


def add_page_number(paragraph):
    run = paragraph.add_run("Page ")
    fld_char1 = OxmlElement("w:fldChar")
    fld_char1.set(qn("w:fldCharType"), "begin")
    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = "PAGE"
    fld_char2 = OxmlElement("w:fldChar")
    fld_char2.set(qn("w:fldCharType"), "end")
    run._r.append(fld_char1)
    run._r.append(instr_text)
    run._r.append(fld_char2)


def set_run_font(run, size=None, bold=None, color=TEXT, italic=None):
    run.font.name = "Candara"
    run._element.rPr.rFonts.set(qn("w:ascii"), "Candara")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "Candara")
    run.font.color.rgb = RGBColor.from_string(color)
    if size:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic


def add_text(paragraph, text, size=10.5, bold=False, color=TEXT, italic=False):
    run = paragraph.add_run(text)
    set_run_font(run, size, bold, color, italic)
    return run


def add_bullet(doc, text, level=0):
    p = doc.add_paragraph(style="List Bullet" if level == 0 else "List Bullet 2")
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.12
    add_text(p, text)
    return p


def add_numbered(doc, text):
    p = doc.add_paragraph(style="List Number")
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.12
    add_text(p, text)
    return p


def add_section_heading(doc, title, level=1):
    p = doc.add_paragraph(style=f"Heading {level}")
    p.paragraph_format.space_before = Pt(15 if level == 1 else 9)
    p.paragraph_format.space_after = Pt(6)
    keep_with_next(p)
    add_text(p, title, 15 if level == 1 else 11.5, True, "000000")
    return p


def add_body(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(7)
    p.paragraph_format.line_spacing = 1.15
    add_text(p, text)
    return p


def add_table(doc, headers, rows, widths=None, font_size=9):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    header = table.rows[0]
    prevent_row_split(header)
    set_repeat_table_header(header)
    for i, header_text in enumerate(headers):
        cell = header.cells[i]
        if widths:
            cell.width = Inches(widths[i])
        set_cell_shading(cell, NAVY)
        set_cell_border(cell)
        set_cell_margins(cell)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0)
        add_text(p, header_text, font_size, True, "FFFFFF")
    for r_index, values in enumerate(rows):
        row = table.add_row()
        prevent_row_split(row)
        for i, value in enumerate(values):
            cell = row.cells[i]
            if widths:
                cell.width = Inches(widths[i])
            set_cell_shading(cell, "FFFFFF" if r_index % 2 == 0 else PALE_BLUE)
            set_cell_border(cell)
            set_cell_margins(cell)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.05
            add_text(p, str(value), font_size)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    return table


def make_doc():
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.72)
    section.bottom_margin = Inches(0.65)
    section.left_margin = Inches(0.78)
    section.right_margin = Inches(0.78)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Candara"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Candara")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Candara")
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = RGBColor.from_string(TEXT)
    for name, size in (("Title", 28), ("Heading 1", 15), ("Heading 2", 11.5)):
        style = styles[name]
        style.font.name = "Trebuchet MS" if name == "Title" else "Candara"
        style._element.rPr.rFonts.set(qn("w:ascii"), style.font.name)
        style._element.rPr.rFonts.set(qn("w:hAnsi"), style.font.name)
        style.font.size = Pt(size)
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.font.bold = True
    for list_name in ("List Bullet", "List Bullet 2", "List Number"):
        styles[list_name].font.name = "Candara"
        styles[list_name].font.size = Pt(10.5)

    footer = section.footer
    footer_p = footer.paragraphs[0]
    footer_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    footer_p.paragraph_format.space_before = Pt(4)
    add_text(footer_p, "ClientFlow One Month Project Plan   |   ", 8.5, False, "666666")
    add_page_number(footer_p)
    for run in footer_p.runs:
        set_run_font(run, 8.5, color="666666")

    # Cover page
    doc.add_paragraph().paragraph_format.space_after = Pt(44)
    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    title.paragraph_format.space_after = Pt(10)
    add_text(title, "ClientFlow", 28, True, "000000")
    subtitle = doc.add_paragraph()
    subtitle.paragraph_format.space_after = Pt(20)
    add_text(subtitle, "One Month Project Plan", 18, False, "000000")
    intro = doc.add_paragraph()
    intro.paragraph_format.space_after = Pt(22)
    intro.paragraph_format.line_spacing = 1.2
    add_text(intro, "A medium to hard full stack project for one developer: build a secure platform with a FastAPI backend and React JavaScript frontend for freelancers to manage clients, projects, time entries, invoices, and financial reporting.", 12, False, TEXT)
    cover_table = add_table(doc, ["Project facts", ""], [
        ["Duration", "4 weeks"],
        ["Team", "One developer"],
        ["Primary stack", "React JavaScript, FastAPI, PostgreSQL, SQLAlchemy, Docker"],
        ["Primary outcome", "A tested, deployable application with a working demo"],
    ], widths=[1.55, 4.85], font_size=9.5)
    # make title-like first table header seamless but still legible
    for c in cover_table.rows[0].cells:
        c.text = ""
        set_cell_shading(c, "FFFFFF")
        set_cell_border(c, "FFFFFF", "0")
    doc.add_paragraph().paragraph_format.space_after = Pt(18)
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    add_text(p, "Prepared for", 9, True, "666666")
    p = doc.add_paragraph()
    add_text(p, "Solo Developer Project Assignment", 11, False)
    p = doc.add_paragraph()
    add_text(p, "Version 1.0 | October 2026", 9, False, "666666")
    doc.add_page_break()

    # Overview
    add_section_heading(doc, "1 Project Overview")
    add_body(doc, "ClientFlow is a web application for freelancers who need one place to manage client work and billing. The system will let a registered user store clients, organize their work into projects and tasks, record billable time, generate invoices, and understand income and outstanding payments from a dashboard.")
    add_body(doc, "The goal is not to build a complete commercial product in four weeks. The goal is to deliver a focused, reliable core product that demonstrates sound API design, relational data modelling, authentication, testing, containerization, and professional documentation.")
    add_section_heading(doc, "1.1 Project Objectives", 2)
    for item in [
        "Build a working FastAPI application that is useful from end to end.",
        "Apply secure user authentication and resource ownership checks.",
        "Model connected business data in PostgreSQL using SQLAlchemy and Alembic migrations.",
        "Implement clear invoice and project status workflows with validation.",
        "Deliver automated tests, Docker setup, seeded demo data, and a clear README.",
    ]:
        add_bullet(doc, item)
    add_section_heading(doc, "1.2 Success Criteria", 2)
    add_table(doc, ["Area", "Successful when"], [
        ["Product", "A user can complete the full journey from registration to a downloadable invoice."],
        ["Security", "Protected data is visible only to its owner and invalid state changes are rejected."],
        ["Quality", "Core routes have passing automated tests and useful error responses."],
        ["Delivery", "The project runs with Docker Compose from documented steps."],
        ["Demonstration", "A five minute demo can show the primary workflow and dashboard."],
    ], widths=[1.25, 5.15])

    # Scope
    add_section_heading(doc, "2 Scope and Boundaries")
    add_body(doc, "The feature list is deliberately split into a required core and optional stretch work. The core must be complete before any stretch feature is started. This protects the final demo and keeps the four-week schedule realistic for a single developer.")
    add_section_heading(doc, "2.1 Required Core Scope", 2)
    add_table(doc, ["Module", "Required capability"], [
        ["Accounts", "Register, log in, hash passwords, issue JWT access tokens, and protect routes."],
        ["Clients", "Create, view, edit, and archive a client with contact details and hourly rate."],
        ["Projects", "Create projects for a client and move them through planned, active, completed, and archived states."],
        ["Tasks", "Create tasks inside a project, set due dates and estimates, and manage todo, in progress, and done statuses."],
        ["Time tracking", "Create manual time entries linked to a task; show billable hours and prevent invalid entries."],
        ["Invoices", "Create an invoice from unbilled entries, calculate totals, and manage draft, sent, paid, and overdue statuses."],
        ["Reporting", "Show monthly income, work by project, open invoices, and overdue invoice counts."],
        ["Delivery", "Provide Docker Compose, sample data, tests, Swagger documentation, and README setup instructions."],
    ], widths=[1.35, 5.05])
    add_section_heading(doc, "2.2 Explicitly Out of Scope", 2)
    for item in [
        "Real payment processing, bank integrations, and credit card handling.",
        "Multi-user teams, client accounts, invitations, or live collaboration.",
        "Complex accounting rules, multiple currencies, or legally compliant tax calculations.",
        "A mobile application or a separate React frontend.",
        "Production email delivery; reminders may be logged or displayed in the interface instead.",
    ]:
        add_bullet(doc, item)

    # Users & stories
    add_section_heading(doc, "3 User Experience and Core Workflow")
    add_body(doc, "The application has one primary user: an independent freelancer. All data belongs to the authenticated user. The frontend will be a React application written in JavaScript. It will call the FastAPI REST API through Axios and use React Router for navigation. Bootstrap or a small custom CSS layer can keep the interface polished without adding unnecessary design complexity.")
    add_section_heading(doc, "3.1 Primary User Journey", 2)
    workflow = [
        "Register an account and sign in.",
        "Create a client and set an hourly rate.",
        "Create an active project and break it into tasks.",
        "Record time against completed or active work.",
        "Select unbilled time entries and generate a draft invoice.",
        "Mark the invoice as sent, later as paid, and view its totals on the dashboard.",
    ]
    for item in workflow:
        add_numbered(doc, item)
    add_section_heading(doc, "3.2 Key User Stories", 2)
    add_table(doc, ["As a freelancer", "I want", "So that"], [
        ["a freelancer", "to record clients and their rates", "billing information is ready when I log time."],
        ["a freelancer", "to organize tasks inside projects", "I can see what work is unfinished."],
        ["a freelancer", "to add billable time entries", "the invoice reflects the work performed."],
        ["a freelancer", "to generate and download an invoice", "I can bill a client professionally."],
        ["a freelancer", "to see unpaid and overdue invoices", "I can follow up on cash flow."],
    ], widths=[1.45, 2.4, 2.55])

    # Technical design
    add_section_heading(doc, "4 Technical Design")
    add_section_heading(doc, "4.1 Recommended Stack", 2)
    add_table(doc, ["Layer", "Technology", "Purpose"], [
        ["Backend", "Python 3.12 and FastAPI", "REST API routes, validation, authentication, documentation, and CORS configuration."],
        ["Data", "PostgreSQL and SQLAlchemy", "Persistent relational data and ORM models."],
        ["Migrations", "Alembic", "Versioned, repeatable database schema changes."],
        ["Security", "JWT and password hashing", "Authentication and ownership enforcement."],
        ["Frontend", "React with JavaScript, Vite, React Router, Axios, and Bootstrap", "Single page application for login, dashboard, CRUD forms, and reports."],
        ["Quality", "pytest and FastAPI TestClient", "Route, service, and authorization checks."],
        ["Packaging", "Docker and Docker Compose", "Repeatable local run environment."],
    ], widths=[1.1, 2.0, 3.3])
    add_section_heading(doc, "4.2 Suggested Application Structure", 2)
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.left_indent = Inches(0.15)
    p.paragraph_format.line_spacing = 1.05
    code = "backend/\n  app/\n    main.py  config.py  database.py  dependencies.py\n    models/  schemas/  routers/  services/\n  tests/  alembic/\nfrontend/\n  src/\n    api/  components/  pages/  hooks/  styles/\n  package.json\nDockerfile  docker-compose.yml  README.md"
    run = p.add_run(code)
    run.font.name = "Consolas"
    run._element.rPr.rFonts.set(qn("w:ascii"), "Consolas")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "Consolas")
    run.font.size = Pt(9.3)
    run.font.color.rgb = RGBColor.from_string(TEXT)
    add_section_heading(doc, "4.3 Data Model", 2)
    add_table(doc, ["Entity", "Key fields", "Relationship"], [
        ["User", "id, email, password hash, created at", "Owns all client, project, time, and invoice records."],
        ["Client", "name, email, phone, hourly rate, archived", "Belongs to User; has many Projects."],
        ["Project", "name, status, start date, due date", "Belongs to Client; has many Tasks."],
        ["Task", "title, status, estimated hours", "Belongs to Project; has many TimeEntries."],
        ["TimeEntry", "date, duration, note, billed flag", "Belongs to Task and is optionally linked to an Invoice."],
        ["Invoice", "number, status, issue date, due date, totals", "Belongs to User and contains InvoiceItems."],
        ["InvoiceItem", "description, quantity, unit rate, amount", "Belongs to Invoice; may represent a TimeEntry."],
    ], widths=[1.2, 2.55, 2.65])

    # Plan
    add_section_heading(doc, "5 Four Week Delivery Plan")
    add_body(doc, "The plan uses five focused workdays each week. Reserve the sixth and seventh day for catch-up, documentation, or rest. Do not move to a later milestone while the previous week is broken or untested.")
    add_section_heading(doc, "Week 1 Foundations and Authentication", 2)
    add_table(doc, ["Day", "Work", "Evidence of completion"], [
        ["1", "Create repository, project board, FastAPI backend, React JavaScript frontend with Vite, and README.", "Backend opens at /docs; React starter page runs; repository has initial commit."],
        ["2", "Add Docker Compose, PostgreSQL connection, SQLAlchemy base, and first Alembic migration.", "Database starts and migration applies."],
        ["3", "Create User model, registration endpoint, password hashing, and validation.", "New user is persisted; duplicate email is rejected."],
        ["4", "Implement login, JWT creation, current-user dependency, and protected sample route.", "Valid login reaches protected route; invalid token fails."],
        ["5", "Add React login and registration screens, authentication tests, and setup instructions.", "Tests pass; the browser client can sign in to the API."],
    ], widths=[0.45, 3.75, 2.2], font_size=8.6)
    add_section_heading(doc, "Week 2 Clients Projects and Tasks", 2)
    add_table(doc, ["Day", "Work", "Evidence of completion"], [
        ["6", "Implement Client model, migration, schemas, and protected CRUD routes.", "User can manage only their own clients."],
        ["7", "Implement Project model and connect projects to clients.", "Projects appear under the selected client."],
        ["8", "Add Task model, CRUD, due dates, estimates, and task statuses.", "Tasks can be created and updated inside a project."],
        ["9", "Build React client, project, and task pages with reusable forms and lists.", "Core workflow is usable outside Swagger."],
        ["10", "Test ownership and status validations; improve error handling.", "Unauthorized and invalid actions have tests."],
    ], widths=[0.45, 3.75, 2.2], font_size=8.6)
    add_section_heading(doc, "Week 3 Time Tracking and Invoices", 2)
    add_table(doc, ["Day", "Work", "Evidence of completion"], [
        ["11", "Add TimeEntry model and manual time entry workflow.", "Entries calculate duration and belong to a task."],
        ["12", "Show project totals and reject invalid or duplicate timer data.", "Billable hours are summarized correctly."],
        ["13", "Add Invoice and InvoiceItem models with subtotal, tax, discount, and total calculation service.", "Invoice calculations have unit tests."],
        ["14", "Generate an invoice from unbilled entries and implement status transitions.", "Selected entries become linked and cannot be billed twice."],
        ["15", "Create PDF invoice download and CSV export for time entries.", "Downloaded files match displayed totals."],
    ], widths=[0.45, 3.75, 2.2], font_size=8.6)
    add_section_heading(doc, "Week 4 Reporting Quality and Demonstration", 2)
    add_table(doc, ["Day", "Work", "Evidence of completion"], [
        ["16", "Build dashboard metrics for monthly income, active projects, unpaid invoices, and overdue invoices.", "Dashboard is accurate with seeded data."],
        ["17", "Add project-hours and income-by-month reports; add overdue invoice check.", "Reports have clear responses or pages."],
        ["18", "Increase test coverage for core user flow and error cases.", "Core happy path and permissions are covered."],
        ["19", "Add seed data, refine Docker setup, and run through a clean installation.", "Another machine can follow the README successfully."],
        ["20", "Complete README, architecture notes, screenshots, and five minute demo recording.", "Project is ready to present or submit."],
    ], widths=[0.45, 3.75, 2.2], font_size=8.6)

    # Standards
    add_section_heading(doc, "6 Development Workflow")
    add_section_heading(doc, "6.1 Git Branching and Pull Requests", 2)
    add_body(doc, "Use main only for runnable, tested work. Create a short-lived branch for each feature. Even for a solo project, open a pull request before merging so the diff can be reviewed, understood, and documented.")
    add_table(doc, ["Branch", "Purpose"], [
        ["feature/project-setup", "Foundation, database, and Docker."],
        ["feature/authentication", "Registration, login, JWT, and tests."],
        ["feature/clients-projects", "Client and project modules."],
        ["feature/tasks-time-tracking", "Task workflow and time entries."],
        ["feature/invoices", "Invoice generation, states, PDF, and exports."],
        ["feature/dashboard-quality", "Reporting, test coverage, documentation, and polish."],
    ], widths=[2.35, 4.05])
    add_section_heading(doc, "6.2 Commit Convention", 2)
    for item in [
        "Use focused commits: feat(auth): add JWT login endpoint.",
        "Use fix for defects, test for test-only changes, docs for documentation, and chore for maintenance.",
        "Do not mix refactors, new features, generated files, and unrelated formatting in one commit.",
        "Before committing, run the project tests and check git diff for accidental changes.",
    ]:
        add_bullet(doc, item)
    add_section_heading(doc, "6.3 Working with Antigravity", 2)
    add_body(doc, "Antigravity should be used as a pair programmer and reviewer, not as a one-command project generator. Give it one scoped backend or frontend feature at a time, require it to name the files it will change, and personally inspect every change before committing.")
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.left_indent = Inches(0.15)
    prompt = "Implement the React JavaScript invoice list page for this existing FastAPI and React project. Use Axios through the existing API client and React Router. Show invoice number, client, total, due date, and status. Add loading, empty, and error states. Do not change backend routes or unrelated modules. First list the files to modify, then explain the final changes and test commands."
    r = p.add_run(prompt)
    r.font.name = "Consolas"
    r._element.rPr.rFonts.set(qn("w:ascii"), "Consolas")
    r._element.rPr.rFonts.set(qn("w:hAnsi"), "Consolas")
    r.font.size = Pt(8.6)
    r.font.color.rgb = RGBColor.from_string(TEXT)

    # QA
    add_section_heading(doc, "7 Quality Plan and Definition of Done")
    add_section_heading(doc, "7.1 Required Tests", 2)
    add_table(doc, ["Test type", "Minimum examples"], [
        ["Authentication", "Registration, duplicate email, valid login, invalid password, expired or invalid token."],
        ["Authorization", "A user cannot view, edit, or delete another user’s client, project, task, time entry, or invoice."],
        ["Business rules", "A time entry cannot be billed twice; invalid invoice status changes are rejected; totals are correct."],
        ["Integration", "Complete path from user registration through invoice generation succeeds."],
        ["Manual checks", "Swagger endpoints, React pages, PDF download, CSV export, and clean Docker Compose run."],
    ], widths=[1.3, 5.1])
    add_section_heading(doc, "7.2 Feature Definition of Done", 2)
    for item in [
        "The feature has a clearly named route, schema, model, or service consistent with the project structure.",
        "Input validation and ownership checks are implemented.",
        "The feature works from Swagger and, when applicable, the React web interface.",
        "Relevant automated tests pass.",
        "The change is documented in the README or API documentation if users need to know it.",
        "The work is committed on a feature branch and reviewed before merging into main.",
    ]:
        add_bullet(doc, item)
    add_section_heading(doc, "7.3 Final Submission Checklist", 2)
    add_table(doc, ["Item", "Check"], [
        ["Repository", "Clean main branch with meaningful commits and no secrets committed."],
        ["Documentation", "README includes setup, environment variables, migrations, tests, Docker, and demo steps."],
        ["Database", "Migrations and seed data work on a fresh database."],
        ["Tests", "Core authentication, authorization, invoice, and end-to-end workflow tests pass."],
        ["Demo", "Five minute walkthrough: register, client, project, task, time, invoice, dashboard, export."],
    ], widths=[1.35, 5.05])

    # Risk and extensions
    add_section_heading(doc, "8 Risks and Stretch Features")
    add_section_heading(doc, "8.1 Delivery Risks", 2)
    add_table(doc, ["Risk", "Control"], [
        ["Too many features", "Finish the required core by the end of Week 3; defer all extra work."],
        ["AI-generated code is not understood", "Ask for explanations, review diffs, and write or adjust tests personally."],
        ["Database changes break existing data", "Use Alembic migrations for every schema change and test on a fresh database."],
        ["Frontend consumes too much time", "Use reusable React components and Bootstrap; prioritize the end to end workflow over visual effects."],
        ["Late integration issues", "Run a complete user journey at the end of every week."],
    ], widths=[2.15, 4.25])
    add_section_heading(doc, "8.2 Stretch Features After Core Completion", 2)
    for item in [
        "Automated email-style invoice reminders using a safe development mailbox or on-screen notification log.",
        "Chart.js visualizations for income by month and hours by project.",
        "File attachments for client documents or project briefs.",
        "Refresh tokens and logout token revocation.",
        "Deployment to Render, Railway, or a comparable service with a production database.",
        "GitHub Actions workflow that runs tests on every push and pull request.",
    ]:
        add_bullet(doc, item)

    add_section_heading(doc, "9 Final Presentation Script")
    add_body(doc, "Keep the demo simple and story-driven. Explain that ClientFlow helps a freelancer turn completed work into a clear invoice while tracking work and payment status.")
    for item in [
        "Show the login page and the protected dashboard.",
        "Create or open a client, project, and task.",
        "Add a time entry and show the project total updating.",
        "Generate an invoice from unbilled work and show its calculated total.",
        "Download the invoice PDF or CSV export.",
        "Return to the dashboard to show income, unpaid invoices, and overdue status.",
        "Briefly show the tests, Docker Compose command, and README run instructions.",
    ]:
        add_numbered(doc, item)

    doc.save(OUT)


if __name__ == "__main__":
    make_doc()
