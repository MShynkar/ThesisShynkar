"""Synthetic-but-coherent corpus for the diploma measurements (point 1).

Each document has a hand-written, topic-specific CORE (so embeddings are
semantically distinct and the annotated quality queries map to real targets),
plus standard policy sections generated from real English sentence templates
parameterised by the document subject. This is how genuine corporate documents
read (Purpose / Scope / Responsibilities / Procedure / Compliance / Review),
and keeps every document coherent English >= ~800 words — unlike Lorem ipsum,
which would give meaningless embeddings.

`access_level` values: public | internal | confidential | restricted.
"""
from __future__ import annotations

# (title, access_level, category, tags, subject_phrase, core_paragraphs)
RAW: list[tuple] = [
    # ---------------- PUBLIC (10 new) ----------------
    (
        "Working Hours and Remote Work Policy", "public", "HR",
        ["remote", "hours", "policy"], "flexible working hours and remote work",
        [
            "This policy describes how and when employees are expected to work. The company "
            "operates on a flexible-hours model: core collaboration hours are 11:00 to 16:00 "
            "in each employee's local time zone, and the remaining hours may be arranged to "
            "suit personal circumstances as long as deliverables and meetings are respected.",
            "Remote work is fully supported. Employees may work from home, from a co-working "
            "space, or from an office, and most teams are distributed across several countries. "
            "Asynchronous communication is the default; decisions and context are written down "
            "in shared documents so that nobody is blocked waiting for a colleague in another "
            "time zone. Managers schedule recurring meetings inside core hours only.",
            "Employees who work remotely receive a one-time home-office stipend and a monthly "
            "internet allowance. Attendance is measured by output, not by hours logged. "
            "Overtime is discouraged; sustained overwork should be raised with a manager so "
            "that scope or staffing can be adjusted.",
        ],
    ),
    (
        "Paid Time Off and Vacation Policy", "public", "HR",
        ["vacation", "pto", "leave"], "paid time off, vacation and leave",
        [
            "Every full-time employee is entitled to 25 days of paid vacation per calendar "
            "year, in addition to national public holidays observed in their country of "
            "residence. Vacation accrues monthly and up to 5 unused days may be carried over "
            "into the first quarter of the following year.",
            "Sick leave is unlimited and trust-based: employees do not need a doctor's note "
            "for short absences and are asked to rest rather than work while unwell. Parental "
            "leave is 16 weeks fully paid for the primary caregiver and 6 weeks for the "
            "secondary caregiver, and can be taken flexibly during the first year.",
            "To request vacation, submit the dates in the HR portal at least two weeks in "
            "advance for absences longer than three days. Managers approve requests within "
            "five working days and ensure adequate coverage. Bereavement leave, jury duty and "
            "marriage leave are granted separately and do not count against the vacation "
            "balance.",
        ],
    ),
    (
        "Code of Conduct and Anti-Harassment Policy", "public", "HR",
        ["conduct", "harassment", "ethics"], "professional conduct and anti-harassment",
        [
            "All employees, contractors and visitors are expected to behave with respect, "
            "honesty and integrity. Discrimination or harassment based on gender, race, "
            "religion, age, disability, sexual orientation or any other protected "
            "characteristic is strictly prohibited and is grounds for disciplinary action up "
            "to and including immediate termination.",
            "Harassment includes unwelcome verbal, written or physical conduct that creates an "
            "intimidating or hostile environment. Retaliation against anyone who reports a "
            "concern in good faith is itself a serious violation. Reports can be made to a "
            "manager, to People Operations, or anonymously through the ethics hotline, and are "
            "investigated promptly and confidentially.",
            "Conflicts of interest, bribery, and acceptance of inappropriate gifts are not "
            "tolerated. Employees must disclose any outside activity that could compete with "
            "or influence their work for the company.",
        ],
    ),
    (
        "Employee Benefits and Health Insurance Overview", "public", "HR",
        ["benefits", "insurance", "health"], "employee benefits and health insurance",
        [
            "The company provides comprehensive health insurance covering medical, dental and "
            "vision care for every employee, with the option to add dependents at a "
            "subsidised rate. Coverage begins on the first day of employment with no waiting "
            "period, and includes mental-health support and an annual preventive check-up.",
            "Additional benefits include a retirement savings plan with employer matching up "
            "to 5 percent of salary, life and disability insurance, an annual learning and "
            "development budget, and a wellness allowance that can be spent on gym "
            "memberships, equipment or counselling.",
            "Open enrolment runs every November, and employees may change their elections "
            "after qualifying life events such as marriage or the birth of a child. Questions "
            "about claims or coverage are handled by the benefits team.",
        ],
    ),
    (
        "Expense Reimbursement Policy", "public", "Finance",
        ["expenses", "reimbursement", "travel"], "business expense reimbursement",
        [
            "Employees are reimbursed for reasonable and necessary business expenses, "
            "including work-related travel, accommodation, client meals and software "
            "subscriptions approved by a manager. Expenses must be submitted through the "
            "finance portal within 30 days, with an itemised receipt attached for every line "
            "item above 25 dollars.",
            "Air travel should be booked in economy class for flights under six hours; "
            "accommodation has a nightly cap that varies by city. Personal expenses, fines, "
            "and alcohol beyond a modest amount at client dinners are not reimbursable. "
            "Mileage for personal-car use is reimbursed at the standard national rate.",
            "Reimbursements are paid with the next payroll cycle after manager approval. "
            "Repeated submission of non-compliant or inflated claims may lead to loss of the "
            "corporate card and disciplinary review.",
        ],
    ),
    (
        "IT Acceptable Use Policy", "public", "IT",
        ["it", "acceptable-use", "devices"], "acceptable use of IT systems and devices",
        [
            "Company laptops, accounts and networks are provided for work purposes. Limited "
            "personal use is acceptable as long as it does not interfere with duties, consume "
            "excessive resources, or break the law. Employees must lock their screens when "
            "away, use the company password manager, and enable full-disk encryption.",
            "Multi-factor authentication is mandatory for all corporate accounts. Employees "
            "must not install unapproved software, disable security agents, or connect "
            "untrusted USB devices. Confidential data must never be copied to personal cloud "
            "storage or emailed to personal addresses.",
            "Lost or stolen devices must be reported to IT immediately so they can be wiped "
            "remotely. Violations of this policy may result in revoked access and "
            "disciplinary action.",
        ],
    ),
    (
        "Customer Privacy Policy", "public", "Legal",
        ["privacy", "gdpr", "customers"], "customer data privacy and protection",
        [
            "We collect only the personal data needed to provide and improve our services, "
            "such as account details, usage analytics and support correspondence. We never "
            "sell personal data. Customers can access, correct, export or delete their data at "
            "any time through their account settings or by contacting our privacy team.",
            "Personal data is processed lawfully under applicable regulations including the "
            "GDPR, with a documented legal basis for each processing activity. Data is "
            "encrypted in transit and at rest, and access is restricted to staff who need it. "
            "We retain personal data only as long as necessary for the stated purpose.",
            "If a data breach affects customers, we notify the relevant supervisory authority "
            "within 72 hours and inform affected individuals without undue delay. Third-party "
            "processors are bound by contractual data-protection obligations.",
        ],
    ),
    (
        "New Hire Onboarding FAQ", "public", "HR",
        ["onboarding", "faq", "newhire"], "new-hire onboarding and frequently asked questions",
        [
            "Welcome to the team. On your first day you will receive your laptop, accounts and "
            "an onboarding buddy who will help you settle in during the first month. Your "
            "manager will walk you through the team's goals, tools and rituals, and set "
            "expectations for the first 30, 60 and 90 days.",
            "Frequently asked questions: payroll runs on the last working day of each month; "
            "you can find your payslips in the HR portal. Equipment requests go through the IT "
            "help desk. To set up your development environment, follow the engineering "
            "onboarding guide. Your benefits are active from day one.",
            "If you are unsure who owns something, ask in the general help channel — nobody is "
            "expected to know everything in their first weeks, and questions are always "
            "welcome.",
        ],
    ),
    (
        "Workplace Health and Safety Guidelines", "public", "HR",
        ["safety", "health", "office"], "workplace health and safety",
        [
            "The company is committed to providing a safe and healthy working environment, "
            "whether employees work in an office or from home. Offices are equipped with "
            "first-aid kits, clearly marked fire exits and trained fire wardens, and "
            "evacuation drills are held twice a year.",
            "Employees working from home are encouraged to set up an ergonomic workstation; "
            "the wellness allowance can be used for a suitable chair or desk. Report any "
            "hazard, injury or near-miss to the facilities team so it can be addressed. "
            "Electrical equipment is inspected periodically.",
            "Mental health is treated with the same seriousness as physical health. The "
            "employee assistance program offers free, confidential counselling, and managers "
            "are trained to support team members who are struggling.",
        ],
    ),
    (
        "Diversity, Equity and Inclusion Statement", "public", "HR",
        ["diversity", "inclusion", "dei"], "diversity, equity and inclusion",
        [
            "We believe diverse teams build better products. The company is committed to "
            "fair hiring, equal pay for equal work, and an inclusive culture where everyone "
            "can do their best work regardless of background. We set measurable goals for "
            "representation and review pay equity annually.",
            "Recruiting uses structured interviews and diverse panels to reduce bias. Employee "
            "resource groups provide community and a voice to under-represented colleagues, "
            "and the company sponsors mentorship and scholarship programs. Accessibility is "
            "considered in our offices, events and products.",
            "Inclusion is everyone's responsibility. We expect all employees to challenge "
            "bias respectfully and to help create an environment where different perspectives "
            "are heard and valued.",
        ],
    ),

    # ---------------- INTERNAL (11 new) ----------------
    (
        "Engineering Best Practices and Code Review Standards", "internal", "Engineering",
        ["engineering", "code-review", "quality"], "engineering best practices and code review",
        [
            "Every change to production code requires at least one approving review from a "
            "peer before it is merged. Reviews focus on correctness, security, readability and "
            "maintainability rather than personal style; formatting is enforced automatically "
            "by linters so reviewers can concentrate on substance.",
            "Authors keep pull requests small and focused, write a clear description of what "
            "changed and why, and include tests. Reviewers respond within one working day and "
            "are explicit about which comments are blocking. Large or risky changes are "
            "discussed in a design document before implementation begins.",
            "All new features must ship with unit tests, and API endpoints additionally "
            "require integration tests. The target line coverage is 80 percent or higher. "
            "Secrets must never be committed; credentials live in the vault and are referenced "
            "by configuration.",
        ],
    ),
    (
        "Git Branching and Release Management Process", "internal", "Engineering",
        ["git", "release", "branching"], "git branching and release management",
        [
            "We use trunk-based development: short-lived feature branches are cut from main, "
            "kept in sync daily, and merged back through a reviewed pull request. The main "
            "branch is always releasable and protected — direct pushes are disabled and "
            "continuous integration must pass before merging.",
            "Releases are continuous and automated from main. Each deployment is blue-green so "
            "that traffic can be shifted gradually and rolled back within sixty seconds from "
            "the rollback dashboard if error rates rise. Database migrations are written to be "
            "backward compatible so that the old and new versions can run side by side.",
            "Hotfixes follow the same review and CI process but are expedited. Release notes "
            "are generated from commit messages, so commits must be descriptive and reference "
            "the relevant issue.",
        ],
    ),
    (
        "Incident Response Runbook", "internal", "Engineering",
        ["incident", "oncall", "runbook"], "production incident response and on-call",
        [
            "When a production incident is detected, the on-call engineer becomes the incident "
            "commander and is responsible for coordinating the response, not necessarily for "
            "fixing the problem alone. The first priority is to mitigate customer impact — for "
            "example by rolling back the last deployment or failing over — before doing a root "
            "cause analysis.",
            "Severity is classified from SEV1 (full outage or data loss) to SEV3 (minor, "
            "limited impact). SEV1 and SEV2 incidents require an incident channel, a status-"
            "page update within fifteen minutes, and regular communication to stakeholders. "
            "The on-call rotation is weekly and compensated, with a documented escalation path "
            "to secondary on-call and engineering leadership.",
            "Within three working days of resolution, the team writes a blameless postmortem "
            "describing the timeline, contributing factors and concrete action items to "
            "prevent recurrence.",
        ],
    ),
    (
        "API Design Guidelines", "internal", "Engineering",
        ["api", "rest", "design"], "REST API design guidelines",
        [
            "Our HTTP APIs are resource-oriented and use predictable, plural nouns for "
            "collections. Standard methods map to GET for reads, POST to create, PUT or PATCH "
            "to update and DELETE to remove. Endpoints return appropriate status codes and a "
            "consistent JSON error envelope with a machine-readable code and a human-readable "
            "message.",
            "APIs are versioned under a path prefix such as /api/v1 so that breaking changes "
            "never affect existing clients. List endpoints support pagination, filtering and "
            "sorting through query parameters. Authentication uses bearer tokens, and every "
            "endpoint enforces authorization on the server side — never trust the client.",
            "Backward compatibility is a contract: fields are added, not removed or repurposed, "
            "and deprecations are announced with a migration window. All endpoints are "
            "documented with examples in the OpenAPI specification.",
        ],
    ),
    (
        "Database Schema and Migration Guide", "internal", "Engineering",
        ["database", "migration", "schema"], "database schema design and migrations",
        [
            "Schema changes are applied exclusively through versioned migration files managed "
            "by Alembic, never by hand on a live database. Each migration is reviewed, has a "
            "working downgrade where feasible, and is tested against a copy of production data "
            "before release. Migrations must be backward compatible so they can run while the "
            "previous application version is still serving traffic.",
            "Add columns as nullable or with a default first, backfill data in batches, and "
            "only then enforce constraints in a later migration. Large index builds use the "
            "concurrent option to avoid locking. Foreign keys, sensible indexes and explicit "
            "naming conventions are required for every table.",
            "Personally identifiable information is isolated and access-controlled, and "
            "destructive migrations are coordinated with a backup and a maintenance window.",
        ],
    ),
    (
        "Testing and Quality Assurance Standards", "internal", "Engineering",
        ["testing", "qa", "coverage"], "testing and quality assurance",
        [
            "The testing strategy follows a pyramid: many fast unit tests, a moderate number "
            "of integration tests that exercise real database and service boundaries, and a "
            "small set of end-to-end tests for critical user journeys. Tests run automatically "
            "on every pull request and must pass before merging.",
            "Unit tests are deterministic and isolated, avoiding network calls through mocking. "
            "Integration tests run against ephemeral containers so they reflect production "
            "behaviour. Coverage is tracked with a target of 80 percent, but reviewers value "
            "meaningful assertions over coverage numbers alone.",
            "Flaky tests are quarantined and fixed quickly because they erode trust in the "
            "suite. Performance-sensitive code paths include benchmarks, and security-relevant "
            "changes include negative tests that prove access is denied when it should be.",
        ],
    ),
    (
        "Security Engineering Standards", "internal", "Security",
        ["security", "secrets", "rotation"], "security engineering, secrets and key rotation",
        [
            "Secrets such as API keys, database passwords and signing keys are never committed "
            "to source control or hard-coded. They are stored in the secrets vault and "
            "injected at runtime through configuration. Access to the vault is least-privilege "
            "and fully audited.",
            "All credentials and API keys are rotated on a fixed schedule of every 90 days, "
            "and immediately if a compromise is suspected or an employee with access leaves. "
            "Dependencies are scanned for known vulnerabilities weekly, and critical patches "
            "are applied within a defined service-level window. Multi-factor authentication is "
            "enforced for all administrative access.",
            "Encryption is required in transit (TLS) and at rest. The principle of least "
            "privilege governs every system: services and people receive the minimum access "
            "needed, and access reviews are conducted quarterly.",
        ],
    ),
    (
        "Cloud Infrastructure and Deployment Guide", "internal", "Engineering",
        ["cloud", "deployment", "infrastructure"], "cloud infrastructure and deployment",
        [
            "Infrastructure is defined as code and provisioned through reviewed, version-"
            "controlled templates so that environments are reproducible and auditable. "
            "Workloads run in containers orchestrated across multiple availability zones for "
            "resilience, with automatic scaling based on load.",
            "The standard pipeline builds an immutable container image, runs the full test "
            "suite, scans for vulnerabilities, and promotes the same artifact through staging "
            "to production. Configuration differs between environments only through "
            "environment variables and secrets, never through separate code.",
            "Production access is restricted and logged, monitoring and alerting are wired "
            "into every service, and backups are taken automatically and tested by periodic "
            "restore drills.",
        ],
    ),
    (
        "Data Retention and Deletion Policy", "internal", "Legal",
        ["data-retention", "deletion", "compliance"], "data retention, archival and deletion",
        [
            "This policy defines how long each category of data is kept and when it is "
            "securely deleted. The company's principle is to retain data only as long as there "
            "is a clear business or legal reason, and then to remove it. Retention periods are "
            "documented per data type and reviewed annually.",
            "Operational application data is retained for the life of the customer account and "
            "deleted within 30 days of account closure. Audit and security logs are retained "
            "for 12 months. Financial records are retained for 7 years to satisfy tax and "
            "accounting obligations. Backups follow a rolling 35-day window and are encrypted.",
            "When a retention period expires, data is deleted or irreversibly anonymised "
            "through an automated job, and deletion is logged. Legal holds override normal "
            "retention: data subject to litigation or investigation is preserved until the "
            "hold is lifted.",
        ],
    ),
    (
        "Logging, Monitoring and Observability Standards", "internal", "Engineering",
        ["logging", "monitoring", "observability"], "logging, monitoring and observability",
        [
            "Every service emits structured, machine-readable logs with a consistent set of "
            "fields including a request identifier that allows a single request to be traced "
            "across services. Logs never contain secrets or raw personal data; sensitive "
            "values are redacted at the source.",
            "Services expose metrics for request rate, error rate and latency, and define "
            "service-level objectives with alerts that fire before customers are affected. "
            "Dashboards make the health of each system visible at a glance, and distributed "
            "tracing links slow requests to the specific component responsible.",
            "Alerts are actionable and tied to a runbook; noisy or non-actionable alerts are "
            "tuned or removed so on-call engineers can trust their pager. Log retention "
            "follows the data retention policy.",
        ],
    ),
    (
        "Engineering Onboarding Guide", "internal", "Engineering",
        ["onboarding", "engineering", "setup"], "engineering environment setup and onboarding",
        [
            "This guide gets a new engineer from a fresh laptop to a merged change in the "
            "first week. Start by installing the toolchain, cloning the monorepo, and running "
            "the bootstrap script, which sets up the local database, seeds sample data and "
            "starts the services with one command.",
            "Read the architecture overview and the code review standards before opening your "
            "first pull request. A good starter task is a small, well-scoped bug with a clear "
            "definition of done; your onboarding buddy will pair with you on it. Run the test "
            "suite locally before pushing, and ask for review early.",
            "Access to staging and production is granted progressively as you complete the "
            "security training. By the end of the first month you should be comfortable "
            "deploying, reading logs, and responding to a low-severity alert with support.",
        ],
    ),

    # ---------------- CONFIDENTIAL (7 new) ----------------
    (
        "Q3 Strategic Plan and OKRs", "confidential", "Strategy",
        ["strategy", "okr", "q3"], "Q3 strategic objectives and key results",
        [
            "CONFIDENTIAL — managers and above only. The third-quarter strategy concentrates "
            "the company on three objectives: ship the enterprise edition of the platform to "
            "general availability, grow net revenue retention above 115 percent, and reduce "
            "infrastructure cost per customer by 20 percent.",
            "Key results for the enterprise objective include completing SOC 2 Type II "
            "certification, delivering single sign-on and audit logging, and signing five "
            "lighthouse customers. The revenue objective is measured by expansion bookings and "
            "a churn rate below 1.5 percent monthly. Cost efficiency is tracked through gross "
            "margin, which must stay above 70 percent.",
            "Each department maps its own key results to these company objectives, and "
            "progress is reviewed every two weeks. Hiring is prioritised for security, "
            "platform reliability and enterprise sales.",
        ],
    ),
    (
        "Annual Operating Budget and Financial Forecast", "confidential", "Finance",
        ["budget", "forecast", "finance"], "annual operating budget and financial forecast",
        [
            "CONFIDENTIAL. The annual operating budget allocates spending across engineering, "
            "sales and marketing, and general and administrative functions, against a revenue "
            "forecast of 18 million dollars in annual recurring revenue by year end. Personnel "
            "is the largest line item at roughly 65 percent of total operating expense.",
            "The forecast assumes 40 percent year-over-year revenue growth, a blended gross "
            "margin of 72 percent, and a path to break-even within eight quarters at the "
            "current burn rate. The board has approved an engineering headcount increase of "
            "twelve senior hires weighted toward infrastructure and security.",
            "Cash runway is modelled monthly under base, upside and downside scenarios. The "
            "downside scenario triggers predefined spending controls. Quarterly reforecasts "
            "adjust the plan as bookings and churn data come in.",
        ],
    ),
    (
        "Product Roadmap (Next 12 Months)", "confidential", "Product",
        ["roadmap", "product", "planning"], "twelve-month product roadmap",
        [
            "CONFIDENTIAL. Over the next twelve months the product roadmap moves the platform "
            "from a strong single-team tool to an enterprise-ready system. The first half "
            "focuses on security and administration: role-based access control, audit logs, "
            "single sign-on, and data residency options for European customers.",
            "The second half emphasises scale and intelligence: a redesigned ingestion "
            "pipeline for larger document corpora, hybrid retrieval improvements, and "
            "analytics that show customers how their teams use the system. A public API and a "
            "marketplace for integrations are planned for the fourth quarter.",
            "Each initiative has a rough size, an owning team and a measurable success metric. "
            "The roadmap is reviewed monthly and is deliberately less specific further out to "
            "preserve flexibility as we learn from customers.",
        ],
    ),
    (
        "Sales Pipeline and Revenue Targets", "confidential", "Sales",
        ["sales", "pipeline", "revenue"], "sales pipeline and quarterly revenue targets",
        [
            "CONFIDENTIAL. The sales organisation carries a quarterly new-business target of "
            "4.5 million dollars in annual contract value, supported by a qualified pipeline "
            "of roughly 3 times coverage. The enterprise segment is the primary growth engine, "
            "with an average deal size of 80 thousand dollars and a sales cycle of about "
            "ninety days.",
            "Pipeline is managed through defined stages from discovery to closed-won, with "
            "exit criteria at each stage and a weekly forecast call. Win rates, average deal "
            "size and sales-cycle length are tracked by segment and by representative. "
            "Expansion within existing accounts is expected to contribute 40 percent of net "
            "new revenue.",
            "Discounting beyond standard thresholds requires approval, and every closed deal "
            "is handed to customer success with a documented onboarding plan to protect "
            "retention.",
        ],
    ),
    (
        "Competitive Analysis and Market Positioning", "confidential", "Strategy",
        ["competition", "market", "positioning"], "competitive analysis and positioning",
        [
            "CONFIDENTIAL. This analysis compares the company against three categories of "
            "competitor: large cloud platforms bundling retrieval features, well-funded "
            "horizontal startups, and open-source frameworks. Our differentiation rests on "
            "fine-grained access control, on-premise and private-cloud deployment, and a "
            "lower total cost of ownership for mid-market customers.",
            "The large platforms win on breadth and existing relationships but are weak on "
            "data residency and per-document permissions. Open-source frameworks are flexible "
            "but require significant engineering to operate securely; we position ourselves as "
            "the secure, supported path. Pricing is set to undercut enterprise incumbents "
            "while protecting margin.",
            "Risks include platform vendors closing the access-control gap and pricing "
            "pressure from open source. The recommended response is to deepen the security and "
            "compliance moat and to publish reference architectures.",
        ],
    ),
    (
        "Customer Churn Analysis and Retention Strategy", "confidential", "Strategy",
        ["churn", "retention", "customers"], "customer churn analysis and retention",
        [
            "CONFIDENTIAL. Monthly logo churn currently runs at 2.1 percent, above the target "
            "of 1.5 percent, and is concentrated in small accounts that adopted only a single "
            "use case. Revenue churn is lower because larger accounts expand, but the analysis "
            "shows that time-to-first-value is the strongest predictor of retention.",
            "Accounts that reach an activation milestone within the first two weeks churn at "
            "less than half the rate of those that do not. The retention strategy therefore "
            "invests in guided onboarding, proactive customer success outreach for at-risk "
            "accounts identified by a health score, and removing friction in the first-run "
            "experience.",
            "A win-back program targets recently churned customers with targeted improvements. "
            "Success is measured by net revenue retention and by the share of accounts "
            "reaching activation on time.",
        ],
    ),
    (
        "Vendor Contracts and Procurement Summary", "confidential", "Finance",
        ["vendor", "procurement", "contracts"], "vendor contracts and procurement",
        [
            "CONFIDENTIAL. This summary lists the company's material vendor relationships, "
            "their annual cost, renewal dates and contractual risk. The largest commitments "
            "are cloud infrastructure, the observability platform, and the customer-"
            "relationship-management suite, which together account for most third-party spend.",
            "Procurement policy requires competitive evaluation for any new commitment above a "
            "defined threshold, a security review for vendors that process company or customer "
            "data, and a signed data-processing agreement where applicable. Auto-renewing "
            "contracts are flagged ninety days before renewal so they can be renegotiated.",
            "Concentration risk is monitored: where a single vendor is critical, a documented "
            "contingency or second source is required. Payment terms are standardised and "
            "early-payment discounts are taken where they beat the cost of capital.",
        ],
    ),

    # ---------------- RESTRICTED (4 new) ----------------
    (
        "Executive Compensation and Equity Grants", "restricted", "HR",
        ["compensation", "executive", "equity"], "executive compensation and equity",
        [
            "RESTRICTED — admin only. This document records the compensation of the executive "
            "team. The Chief Executive Officer has a base salary of 450,000 dollars with a "
            "target bonus of 100 percent of base and an equity grant of 50,000 restricted "
            "stock units vesting over four years.",
            "The Chief Technology Officer has a base salary of 400,000 dollars with an 80 "
            "percent target bonus and 40,000 restricted stock units. The Chief Financial "
            "Officer has a base salary of 380,000 dollars, and the board approved an "
            "additional retention grant of 20,000 units subject to a three-year cliff. All "
            "packages are benchmarked against the 75th percentile of comparable companies.",
            "Bonus payout is tied to company performance against the annual operating plan. "
            "Any change to executive compensation requires approval of the board's "
            "compensation committee and is strictly confidential.",
        ],
    ),
    (
        "M&A Due Diligence — Project Atlas", "restricted", "Strategy",
        ["m&a", "acquisition", "diligence"], "Project Atlas acquisition due diligence",
        [
            "RESTRICTED — admin only. Project Atlas is the codename for the proposed "
            "acquisition of SmallCo, a competitor with complementary technology and a strong "
            "engineering team. The indicative purchase price is approximately 15 million "
            "dollars, structured as a mix of cash and equity, with a target close at the end "
            "of November.",
            "Due diligence is underway across finance, legal, technology and people. Financial "
            "review confirms SmallCo's revenue and modest burn; legal review is examining "
            "intellectual property assignment and outstanding liabilities; technical review "
            "assesses code quality and integration effort. Key-employee retention packages are "
            "being prepared as a condition of close.",
            "The integration plan folds SmallCo's product into our platform over two quarters. "
            "This information is highly market-sensitive and must not be disclosed outside the "
            "deal team.",
        ],
    ),
    (
        "Confidential Board Meeting Minutes", "restricted", "Strategy",
        ["board", "minutes", "governance"], "board of directors meeting minutes",
        [
            "RESTRICTED — admin only. At the most recent board meeting the directors reviewed "
            "financial performance against plan, approved the annual operating budget, and "
            "discussed the Project Atlas acquisition. The company reported being modestly "
            "ahead of its revenue plan with gross margin holding above 70 percent.",
            "The board approved the twelve senior-hire engineering expansion and the executive "
            "retention grants recommended by the compensation committee. It directed "
            "management to complete SOC 2 Type II certification before pursuing larger "
            "enterprise deals, and asked for a detailed cash-runway analysis under a downside "
            "scenario at the next meeting.",
            "A confidential discussion covered a preliminary inbound interest from a strategic "
            "investor. No decision was taken, and management was asked to keep the board "
            "informed. The meeting closed with the standard legal and compliance update.",
        ],
    ),
    (
        "Workforce Reduction and Restructuring Plan", "restricted", "HR",
        ["restructuring", "layoff", "rif"], "workforce reduction and restructuring",
        [
            "RESTRICTED — admin only. This contingency plan describes a potential workforce "
            "reduction to be executed only if the downside financial scenario materialises. "
            "It identifies roles that could be consolidated, the associated severance cost, "
            "and the legal notice requirements in each country where the company employs "
            "staff.",
            "The plan prioritises protecting customer-facing reliability and revenue functions "
            "while reducing duplicated or speculative work. Affected employees would receive "
            "severance above the statutory minimum, extended benefits, and outplacement "
            "support. Communication would be handled with dignity and in compliance with local "
            "employment law.",
            "This document is highly sensitive: premature disclosure would harm morale and the "
            "company's reputation. It is shared strictly on a need-to-know basis and is not an "
            "indication that a reduction has been decided.",
        ],
    ),
]


STANDARD_SECTIONS = [
    ("Background and Rationale",
     "The company adopted a formal position on {subject} because consistent, written guidance "
     "reduces ambiguity, protects employees and customers, and lets teams move quickly without "
     "re-litigating the same questions. In the absence of a shared standard, individuals make "
     "well-intentioned but divergent choices, which over time create risk, rework and "
     "inconsistency. This document captures the agreed approach so that the organisation can "
     "act predictably and explain its decisions, both internally and to external auditors or "
     "regulators when that is required."),
    ("Purpose and Scope",
     "The purpose of this document is to set clear, consistent expectations for {subject} "
     "across the organisation. It applies to all employees, contractors and, where relevant, "
     "third parties acting on the company's behalf, regardless of location, seniority or team. "
     "The guidance here should be read together with the company's other policies and "
     "standards; where two documents appear to conflict, raise it with the owning function "
     "rather than choosing one arbitrarily. Where a more specific local legal requirement "
     "exists, that requirement takes precedence over the general guidance below."),
    ("Roles and Responsibilities",
     "Managers are responsible for ensuring their teams understand and follow the rules "
     "described here for {subject}, for modelling the expected behaviour themselves, and for "
     "raising questions or exceptions through the appropriate channel rather than working "
     "around them. Individual employees are responsible for acting in good faith, asking when "
     "something is unclear, completing any required training, and reporting concerns promptly "
     "and without fear of retaliation. The owning function maintains this document, answers "
     "questions of interpretation, tracks exceptions, and keeps the guidance aligned with "
     "regulation and business reality."),
    ("Procedure",
     "Day-to-day handling of {subject} follows a simple, repeatable procedure. First, identify "
     "what part of this guidance applies to your situation. Then follow the documented steps, "
     "record the relevant details in the appropriate system of record, and seek approval at "
     "the points where this document requires it. Keep enough of a trail that a colleague or "
     "auditor could later understand what was done and why. When a situation is genuinely not "
     "covered, use good judgement, write down your reasoning, and consult the owning function "
     "rather than inventing an undocumented exception that others cannot see or learn from."),
    ("Compliance and Exceptions",
     "Compliance with this document is mandatory. Deviations are permitted only when explicitly "
     "approved in writing by the owning function, and every approved exception is recorded with "
     "its justification, its owner and an expiry date so that it can be revisited rather than "
     "becoming a permanent silent carve-out. The company monitors adherence through normal "
     "management oversight and, where appropriate, periodic audits. Repeated or deliberate "
     "non-compliance regarding {subject} may lead to corrective action, up to and including "
     "termination of employment or contract, and where the law has been broken, referral to "
     "the appropriate authorities."),
    ("Definitions and Related Documents",
     "Unless stated otherwise, the terms used here carry their ordinary business meaning, and "
     "any role names refer to the function rather than to a specific individual. This document "
     "on {subject} should be read alongside the company handbook, the information-security "
     "policy, the privacy policy and the relevant team runbooks, which together form the "
     "company's policy framework. Where this document references another policy, the "
     "referenced policy governs the detail of that adjacent topic, and this one governs only "
     "the matters set out in its scope."),
    ("Review and Maintenance",
     "This document is reviewed at least once a year, and sooner if regulations, tools or "
     "business needs change materially, if an incident reveals a gap, or if employees report "
     "that the guidance is unclear in practice. Feedback is welcome at any time and should be "
     "sent to the owning function, which evaluates suggestions and publishes updates together "
     "with a short changelog so readers can see what changed. Keeping guidance on {subject} "
     "accurate, proportionate and practical is a shared responsibility, and everyone is "
     "encouraged to flag anything that is unclear, outdated or contradictory."),
    ("Effective Date and Ownership",
     "This version of the {subject} guidance is effective from the date of publication and "
     "supersedes any previous version. It is owned by the function named above, approved by "
     "the relevant leadership, and stored in the company's central policy repository where the "
     "current version always takes precedence over any cached or printed copy. Employees are "
     "notified of material changes through the usual internal communication channels."),
]


def build_content(subject: str, core_paragraphs: list[str]) -> str:
    """Compose a coherent >=800-word document from the core plus standard sections."""
    parts: list[str] = list(core_paragraphs)
    for heading, template in STANDARD_SECTIONS:
        parts.append(f"{heading}\n{template.format(subject=subject)}")
    return "\n\n".join(parts)


def documents() -> list[dict]:
    docs = []
    for title, level, category, tags, subject, core in RAW:
        content = build_content(subject, core)
        docs.append(
            {
                "title": title,
                "access_level": level,
                "category": category,
                "tags": tags,
                "content": content,
                "word_count": len(content.split()),
            }
        )
    return docs


if __name__ == "__main__":
    ds = documents()
    print(f"{len(ds)} documents")
    by_level: dict[str, int] = {}
    total_words = 0
    for d in ds:
        by_level[d["access_level"]] = by_level.get(d["access_level"], 0) + 1
        total_words += d["word_count"]
    print("by level:", by_level)
    print("avg words:", round(total_words / len(ds)))
    print("min words:", min(d["word_count"] for d in ds))
    print("max words:", max(d["word_count"] for d in ds))
