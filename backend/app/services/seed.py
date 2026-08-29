from datetime import datetime, timedelta, timezone
from random import Random

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import (
    Activity,
    ActivityCompetency,
    Assessment,
    AssessmentItem,
    AssessmentQuestion,
    Competency,
    CompetencyDomain,
    CompetencyEvidence,
    CompetencyLevel,
    Course,
    Department,
    EmployeeCompetency,
    EmployeeRole,
    FutureSkillDemand,
    LearningProgress,
    Position,
    PositionRole,
    PublishedQuiz,
    Role,
    RoleActivity,
    RoleCompetencyRequirement,
    SkillForecast,
    TrainingProgramme,
    User,
)


DEPARTMENTS = [
    ("National Statistical Office", "NSO", "National-level statistical production and coordination."),
    ("Survey Division", "SURVEY", "Large-scale sample surveys and field operations."),
    ("Data Analytics Division", "ANALYTICS", "Data engineering, visualisation, and analytical services."),
    ("Economic Statistics Division", "ECON", "Economic, industrial, and price statistics."),
    ("Social Statistics Division", "SOCIAL", "Population, labour, and social-sector statistics."),
]

COMPETENCIES = [
    ("SURVEY_DESIGN", "Survey Design", "Statistical", "Designing fit-for-purpose statistical surveys.", "Can describe survey objectives and basic instruments.", "Can design sampling and collection workflows with review.", "Can lead complex survey design and quality assurance.", 4, 1.0),
    ("SAMPLING", "Sampling", "Statistical", "Selecting representative samples and estimating uncertainty.", "Recognises common sampling approaches.", "Applies probability sampling and interprets error.", "Designs efficient multi-stage sampling strategies.", 4, 1.0),
    ("NATIONAL_ACCOUNTS", "National Accounts", "Statistical", "Compiling and interpreting national accounts.", "Understands core aggregates.", "Applies compilation concepts to official datasets.", "Leads reconciliation and methodological improvement.", 3, 0.9),
    ("PRICE_STATISTICS", "Price Statistics", "Statistical", "Producing price indices and inflation measures.", "Explains price index purpose.", "Works with index construction and validation.", "Leads advanced price measurement programmes.", 3, 0.9),
    ("LABOUR_STATISTICS", "Labour Statistics", "Statistical", "Measuring employment, labour force, and work conditions.", "Identifies key labour indicators.", "Interprets labour survey estimates.", "Leads labour-statistics methodology and dissemination.", 3, 0.9),
    ("AGRICULTURAL_STATISTICS", "Agricultural Statistics", "Statistical", "Producing reliable agriculture and crop statistics.", "Recognises agricultural data sources.", "Analyses crop and input datasets.", "Designs integrated agricultural-statistics systems.", 3, 0.8),
    ("INDUSTRIAL_STATISTICS", "Industrial Statistics", "Statistical", "Measuring industrial activity and performance.", "Understands basic industrial indicators.", "Validates industrial data and classifications.", "Leads industrial-statistics programmes.", 3, 0.8),
    ("SDG_INDICATORS", "SDG Indicators", "Statistical", "Producing and interpreting Sustainable Development Goal indicators.", "Can identify common SDG indicators.", "Maps sources and metadata to indicator frameworks.", "Leads cross-domain SDG reporting and quality review.", 4, 1.0),
    ("METADATA_STANDARDS", "Metadata Standards", "Statistical", "Maintaining structured metadata for official statistics.", "Recognises metadata fields.", "Creates usable metadata and classifications.", "Designs metadata governance across systems.", 4, 1.0),
    ("DATA_QUALITY", "Data Quality Frameworks", "Statistical", "Applying quality dimensions and improvement cycles.", "Names quality dimensions.", "Runs quality checks and documents findings.", "Leads organisation-wide quality assurance.", 4, 1.0),
    ("PYTHON", "Python", "Technical", "Using Python for reproducible statistical and data workflows.", "Can edit and run basic scripts.", "Builds data transformations and analyses.", "Designs maintainable analytical packages and pipelines.", 4, 1.2),
    ("R", "R", "Technical", "Using R for statistical analysis and reporting.", "Runs basic R commands.", "Builds reproducible statistical analyses.", "Leads advanced R workflows and packages.", 3, 0.9),
    ("SQL", "SQL", "Technical", "Querying and managing structured data.", "Writes basic SELECT queries.", "Joins, aggregates, and validates datasets.", "Optimises analytical data models and queries.", 4, 1.1),
    ("STATA", "Stata", "Technical", "Using Stata for applied official-statistics analysis.", "Runs basic commands.", "Builds survey analyses and do-files.", "Maintains advanced reproducible Stata workflows.", 3, 0.7),
    ("SPSS", "SPSS", "Technical", "Using SPSS for applied statistical analysis.", "Navigates basic procedures.", "Runs and interprets common procedures.", "Designs robust analysis templates.", 2, 0.6),
    ("SAS", "SAS", "Technical", "Using SAS for statistical processing.", "Recognises SAS workflow concepts.", "Builds data steps and procedures.", "Leads production SAS environments.", 2, 0.6),
    ("GIS", "GIS", "Technical", "Using geospatial methods for regional and field analysis.", "Reads basic maps and layers.", "Performs joins, spatial queries, and thematic mapping.", "Designs advanced geospatial analytical systems.", 4, 1.2),
    ("DATA_VISUALIZATION", "Data Visualization", "Technical", "Communicating evidence through clear visual analysis.", "Selects simple chart types.", "Builds informative dashboards and reports.", "Leads visual analytics standards and storytelling.", 4, 1.0),
    ("ARTIFICIAL_INTELLIGENCE", "Artificial Intelligence", "Technical", "Understanding responsible AI applications in official statistics.", "Explains common AI concepts.", "Evaluates practical AI use cases and risks.", "Leads responsible AI adoption and governance.", 4, 1.2),
    ("MACHINE_LEARNING", "Machine Learning", "Technical", "Applying machine learning to statistical problems.", "Recognises supervised learning concepts.", "Trains and evaluates suitable models.", "Designs robust ML programmes and validation.", 3, 1.0),
    ("CLOUD_COMPUTING", "Cloud Computing", "Technical", "Using cloud platforms for reliable data workloads.", "Understands basic cloud services.", "Deploys governed workloads with support.", "Architects secure, scalable cloud platforms.", 3, 0.9),
    ("APIS", "APIs", "Technical", "Designing and consuming interoperable data services.", "Can explain an API request.", "Consumes and documents secure APIs.", "Designs versioned interoperable API ecosystems.", 3, 0.9),
    ("OPEN_DATA", "Open Data", "Technical", "Publishing data responsibly for reuse.", "Recognises open-data principles.", "Prepares documented, usable releases.", "Leads open-data policy and quality governance.", 3, 0.8),
    ("DATA_ENGINEERING", "Data Engineering", "Technical", "Building dependable pipelines and data platforms.", "Understands pipeline stages.", "Builds monitored transformation workflows.", "Architects resilient enterprise data platforms.", 3, 1.0),
    ("CYBERSECURITY", "Cybersecurity", "Digital Governance", "Protecting data, systems, and users from cyber risk.", "Recognises common threats.", "Applies secure handling and controls.", "Leads risk-based cyber governance.", 3, 0.9),
    ("DATA_PRIVACY", "Data Privacy", "Digital Governance", "Applying privacy-by-design and responsible data use.", "Recognises personal-data principles.", "Applies minimisation and access controls.", "Leads privacy governance and impact assessments.", 4, 1.0),
    ("DIGITAL_SIGNATURES", "Digital Signatures", "Digital Governance", "Using trusted digital signing and verification.", "Explains what a digital signature does.", "Uses signing workflows safely.", "Designs trusted digital transaction processes.", 2, 0.5),
    ("GOVERNMENT_CLOUD", "Government Cloud", "Digital Governance", "Understanding governed public-sector cloud environments.", "Recognises government-cloud concepts.", "Selects compliant workload patterns.", "Leads secure public-sector cloud architecture.", 3, 0.8),
    ("DIGITAL_PUBLIC_INFRASTRUCTURE", "Digital Public Infrastructure", "Digital Governance", "Understanding interoperable public digital rails.", "Names common DPI concepts.", "Assesses DPI-aligned services.", "Leads policy and architecture for DPI adoption.", 3, 0.8),
    ("LEADERSHIP", "Leadership", "Behavioural & Managerial", "Leading people and decisions in public service.", "Contributes constructively to a team.", "Coordinates teams and makes evidence-based decisions.", "Builds high-trust, high-performance organisations.", 4, 0.9),
    ("COMMUNICATION", "Communication", "Behavioural & Managerial", "Communicating statistical evidence to varied audiences.", "Explains work clearly with support.", "Adapts messages to stakeholders.", "Shapes trusted public communication strategies.", 4, 0.9),
    ("PROJECT_MANAGEMENT", "Project Management", "Behavioural & Managerial", "Planning and delivering multi-stakeholder work.", "Tracks assigned tasks.", "Manages scope, dependencies, and risks.", "Leads complex programmes with measurable outcomes.", 3, 0.9),
    ("ETHICS", "Ethics", "Behavioural & Managerial", "Applying integrity and impartiality in official statistics.", "Recognises ethical responsibilities.", "Identifies and manages common dilemmas.", "Leads ethical culture and public trust safeguards.", 4, 1.0),
    ("DECISION_MAKING", "Decision Making", "Behavioural & Managerial", "Making transparent, evidence-informed decisions.", "Uses provided evidence.", "Balances evidence, uncertainty, and impact.", "Leads complex decisions under uncertainty.", 4, 0.9),
    ("CHANGE_MANAGEMENT", "Change Management", "Behavioural & Managerial", "Guiding people and systems through evidence-led change.", "Recognises why change may be needed.", "Plans adoption steps and manages resistance.", "Leads sustained organisational transformation.", 4, 0.9),
]


def _get_or_create(db: Session, model, field, value, **values):
    item = db.scalar(select(model).where(field == value))
    if item is None:
        item = model(**values)
        db.add(item)
        db.flush()
    return item


def seed_database(db: Session) -> dict[str, int]:
    rng = Random(26101)
    roles = {}
    for name, description in [
        ("EMPLOYEE", "Official learning and competency workspace"),
        ("ADMIN", "Workforce analytics and programme administration"),
        ("TRAINER", "Learning material and assessment authoring"),
    ]:
        roles[name] = _get_or_create(db, Role, Role.name, name, name=name, description=description)

    departments = {}
    for name, code, description in DEPARTMENTS:
        departments[code] = _get_or_create(db, Department, Department.code, code, name=name, code=code, description=description)

    competency_by_code = {}
    for row in COMPETENCIES:
        code, name, category, description, beginner, intermediate, advanced, required_level, weight = row
        competency_by_code[code] = _get_or_create(
            db, Competency, Competency.code, code,
            code=code, name=name, category=category, competency_type=("Domain" if category == "Statistical" else "Behavioural" if category == "Behavioural & Managerial" else "Functional"), description=description,
            beginner_definition=beginner, intermediate_definition=intermediate,
            advanced_definition=advanced, required_level=required_level, weight=weight,
            associated_roles=["EMPLOYEE", "TRAINER", "ADMIN"], associated_courses=[], associated_assessments=[],
        )
        competency_by_code[code].competency_type = "Domain" if category == "Statistical" else "Behavioural" if category == "Behavioural & Managerial" else "Functional"

    if db.scalar(select(func.count()).select_from(User)) == 0:
        demo_users = [
            ("EMP-0001", "employee.demo@aistatgrowth.gov.in", "Dr. Ananya Sharma", "Assistant Director", "Statistical Capacity Building", "Regional data quality and evidence systems", 5.0, "M.A. Economics; PG Diploma in Statistics", "Official Statistics", "Assistant Director", "Lead a modern regional statistics programme", "NSO", roles["EMPLOYEE"]),
            ("ADM-0001", "admin.demo@aistatgrowth.gov.in", "Rohan Mehta", "Deputy Director, Workforce Analytics", "Competency Intelligence Cell", "Organisation-wide capability planning", 12.0, "M.Stat; Public Policy", "Workforce Strategy", "Administrator", "Build a future-ready statistical workforce", "NSO", roles["ADMIN"]),
            ("TRN-0001", "trainer.demo@aistatgrowth.gov.in", "Meera Iyer", "Senior Training Specialist", "Learning Design and Assessment", "Capacity-building programme design", 9.0, "M.Sc. Statistics; Learning Sciences", "Training Delivery", "Trainer", "Scale evidence-based learning programmes", "ANALYTICS", roles["TRAINER"]),
        ]
        for employee_id, email, full_name, designation, division, assignment, years, qualification, domain, current_role, career_goal, dept_code, role in demo_users:
            db.add(User(
                employee_id=employee_id, email=email, full_name=full_name, designation=designation,
                division=division, current_assignment=assignment, years_experience=years,
                educational_qualification=qualification, domain=domain, current_role=current_role,
                career_goal=career_goal, password_hash=hash_password("Demo@123"), role_id=role.id,
                department_id=departments[dept_code].id, is_demo=True,
            ))
        db.flush()

        for i in range(2, 49):
            dept_code = DEPARTMENTS[(i - 2) % len(DEPARTMENTS)][1]
            role = roles["EMPLOYEE"]
            db.add(User(
                employee_id=f"EMP-{i:04d}", email=f"official{i:02d}.demo@aistatgrowth.gov.in",
                full_name=f"{['Aarav','Kavya','Vikram','Nisha','Arjun','Sana','Rahul','Ishita'][i % 8]} {['Patil','Reddy','Das','Khan','Nair','Joshi','Singh','Rao'][i % 8]}",
                designation=["Statistical Officer", "Assistant Statistical Officer", "Research Officer", "Section Officer"][i % 4],
                division="Synthetic Demonstration Workforce", current_assignment="Official statistics delivery and analysis",
                years_experience=float((i % 14) + 1), educational_qualification="Postgraduate qualification in a relevant discipline",
                domain=["Survey Operations", "Economic Statistics", "Social Statistics", "Data Analytics"][i % 4],
                current_role="Official Statistics Professional", career_goal="Strengthen evidence-led public service",
                password_hash=hash_password("Demo@123"), role_id=role.id, department_id=departments[dept_code].id, is_demo=True,
            ))
        db.flush()

    # FRAC-compatible reference data is additive to the existing Phase 2 model.
    domain_descriptions = {
        "Statistical": "Domain competencies used in official-statistics production.",
        "Technical": "Functional technical competencies for data and digital work.",
        "Digital Governance": "Trust, security, privacy, and interoperable public digital capability.",
        "Behavioural & Managerial": "Behaviours and management capabilities for public service delivery.",
    }
    for name, description in domain_descriptions.items():
        _get_or_create(db, CompetencyDomain, CompetencyDomain.name, name, code=name.upper().replace(" ", "_"), name=name, description=description)
    level_rows = [
        (1, "Beginner", "Recognises core concepts with guidance.", "Can explain basic terms and follow a worked example.", "Performs a bounded task with close support."),
        (2, "Elementary", "Applies simple techniques in familiar contexts.", "Can complete a routine task using a documented method.", "Produces a basic output and asks for review appropriately."),
        (3, "Intermediate", "Works independently on recurring professional tasks.", "Can choose and apply an appropriate method.", "Delivers a reliable output and documents assumptions."),
        (4, "Advanced", "Handles complex work and supports others.", "Can evaluate trade-offs, quality, and risk.", "Leads a workstream and coaches colleagues."),
        (5, "Expert", "Shapes standards, strategy, and capability at scale.", "Can set direction under uncertainty.", "Creates reusable practice and improves the system."),
    ]
    for number, name, description, criteria, behaviour in level_rows:
        _get_or_create(db, CompetencyLevel, CompetencyLevel.level_number, number, level_number=number, name=name, description=description, assessment_criteria=criteria, observable_behaviour=behaviour)
    db.flush()
    domain_by_name = {row.name: row for row in db.scalars(select(CompetencyDomain)).all()}
    level_by_number = {row.level_number: row for row in db.scalars(select(CompetencyLevel)).all()}
    for competency in competency_by_code.values():
        competency.domain_id = domain_by_name.get(competency.category).id if domain_by_name.get(competency.category) else None
        competency.required_level_id = level_by_number.get(competency.required_level).id if level_by_number.get(competency.required_level) else None

    activities = {}
    for code, name, description, criticality in [
        ("SURVEY_DATA_ANALYSIS", "Survey Data Analysis", "Analyse survey microdata, estimates, and regional patterns.", 92),
        ("STATISTICAL_VALIDATION", "Statistical Validation", "Validate quality, metadata, and reproducibility of statistical outputs.", 88),
        ("DATA_VISUALIZATION", "Data Visualization", "Communicate official evidence through clear visual products.", 76),
        ("ANALYTICAL_REPORTING", "Analytical Reporting", "Prepare transparent, evidence-led reports for policy stakeholders.", 80),
    ]:
        activities[code] = _get_or_create(db, Activity, Activity.code, code, code=code, name=name, description=description, criticality=criticality)

    position_roles = {}
    for dept_name, dept_code, _ in DEPARTMENTS:
        position = _get_or_create(db, Position, Position.code, f"POSITION_{dept_code}", department_id=departments[dept_code].id, code=f"POSITION_{dept_code}", name=f"{dept_name} Statistical Operations Position", description=f"Synthetic FRAC position for {dept_name}.")
        position_roles[dept_code] = _get_or_create(db, PositionRole, PositionRole.code, f"ROLE_{dept_code}_STATISTICS", position_id=position.id, code=f"ROLE_{dept_code}_STATISTICS", name="Assistant Director — Statistical Analysis" if dept_code == "NSO" else f"{dept_name} Statistical Professional", description="Synthetic role mapping for the prototype; not an official FRAC catalogue record.")

    activity_requirements = {
        "SURVEY_DATA_ANALYSIS": [("SURVEY_DESIGN", 4, 1.0), ("SAMPLING", 4, 1.0), ("PYTHON", 4, 1.0), ("SQL", 3, 0.9), ("GIS", 4, 0.9), ("STATISTICAL_VALIDATION", 0, 0)],
        "STATISTICAL_VALIDATION": [("DATA_QUALITY", 4, 1.0), ("METADATA_STANDARDS", 4, 0.9), ("SQL", 3, 0.8), ("ARTIFICIAL_INTELLIGENCE", 3, 0.6)],
        "DATA_VISUALIZATION": [("DATA_VISUALIZATION", 4, 1.0), ("COMMUNICATION", 4, 0.8), ("OPEN_DATA", 3, 0.6)],
        "ANALYTICAL_REPORTING": [("DATA_VISUALIZATION", 4, 0.9), ("COMMUNICATION", 4, 0.9), ("ARTIFICIAL_INTELLIGENCE", 4, 0.8), ("DATA_QUALITY", 4, 0.7)],
    }
    for dept_code, role in position_roles.items():
        for activity_code, activity in activities.items():
            role_activity = db.scalar(select(RoleActivity).where(RoleActivity.role_id == role.id, RoleActivity.activity_id == activity.id))
            if role_activity is None:
                db.add(RoleActivity(role_id=role.id, activity_id=activity.id, criticality=activity.criticality))
            for competency_code, required_level, importance in activity_requirements[activity_code]:
                if required_level == 0:
                    continue
                competency = competency_by_code[competency_code]
                existing = db.scalar(select(ActivityCompetency).where(ActivityCompetency.activity_id == activity.id, ActivityCompetency.competency_id == competency.id))
                if existing is None:
                    db.add(ActivityCompetency(activity_id=activity.id, competency_id=competency.id, required_level=required_level, importance=importance))
                    db.flush()
                role_requirement = db.scalar(select(RoleCompetencyRequirement).where(RoleCompetencyRequirement.role_id == role.id, RoleCompetencyRequirement.competency_id == competency.id))
                if role_requirement is None:
                    db.add(RoleCompetencyRequirement(role_id=role.id, competency_id=competency.id, required_level=required_level, importance=importance))
                    db.flush()
                elif required_level > role_requirement.required_level:
                    role_requirement.required_level = required_level
                    role_requirement.importance = max(role_requirement.importance, importance)
        if dept_code == "NSO":
            # The demo position's role target preserves the Phase 2 baseline
            # contract (SQL and other core analysis skills target Advanced).
            for competency_code in ("SURVEY_DESIGN", "SAMPLING", "DATA_QUALITY", "PYTHON", "SQL", "GIS", "DATA_VISUALIZATION", "ARTIFICIAL_INTELLIGENCE"):
                competency = competency_by_code[competency_code]
                requirement = db.scalar(select(RoleCompetencyRequirement).where(RoleCompetencyRequirement.role_id == role.id, RoleCompetencyRequirement.competency_id == competency.id))
                if requirement:
                    requirement.required_level = max(requirement.required_level, competency.required_level)
    db.flush()

    user_by_email = {u.email: u for u in db.scalars(select(User)).all()}
    for user in db.scalars(select(User)).all():
        existing = {ec.competency_id for ec in db.scalars(select(EmployeeCompetency).where(EmployeeCompetency.user_id == user.id)).all()}
        for idx, competency in enumerate(competency_by_code.values()):
            if competency.id in existing:
                continue
            if user.email == "employee.demo@aistatgrowth.gov.in":
                baseline = {"STATISTICAL": 82, "TECHNICAL": 45, "DIGITAL GOVERNANCE": 52, "BEHAVIOURAL & MANAGERIAL": 68}.get(competency.category, 50)
                overrides = {"PYTHON": 45, "SQL": 64, "GIS": 31, "ARTIFICIAL_INTELLIGENCE": 38, "DATA_VISUALIZATION": 72, "SURVEY_DESIGN": 82, "SAMPLING": 78}
                score = overrides.get(competency.code, baseline)
            elif user.role_id == roles["ADMIN"].id:
                score = 70 + (idx % 5) * 4
            elif user.role_id == roles["TRAINER"].id:
                score = 62 + (idx % 6) * 5
            else:
                score = 35 + ((user.id * 7 + idx * 11) % 56)
            level = min(5, max(1, round(score / 20)))
            employee_competency = EmployeeCompetency(user_id=user.id, competency_id=competency.id, score=score, level=level, source="seeded_baseline", confidence=0.65, evidence_count=1)
            db.add(employee_competency)
        db.flush()
        department = db.get(Department, user.department_id)
        role = position_roles.get(department.code if department else "NSO")
        if role and db.scalar(select(EmployeeRole).where(EmployeeRole.employee_id == user.id, EmployeeRole.role_id == role.id)) is None:
            db.add(EmployeeRole(employee_id=user.id, role_id=role.id, is_primary=True))
        for employee_competency in db.scalars(select(EmployeeCompetency).where(EmployeeCompetency.user_id == user.id)).all():
            evidence = db.scalar(select(CompetencyEvidence).where(CompetencyEvidence.employee_id == user.id, CompetencyEvidence.competency_id == employee_competency.competency_id, CompetencyEvidence.source_type == "SELF_DECLARATION"))
            if evidence is None:
                db.add(CompetencyEvidence(employee_id=user.id, competency_id=employee_competency.competency_id, source_type="SELF_DECLARATION", source_id="seeded_baseline", score=employee_competency.score, confidence=0.65, metadata_json={"label": "Synthetic seeded baseline"}))
        db.flush()

    course_templates = [
        ("Python for Statistical Analysis", "Python", ["PYTHON", "DATA_ENGINEERING"], "Technical"),
        ("Applied GIS for Statistical Analysis", "GIS", ["GIS", "DATA_VISUALIZATION"], "Technical"),
        ("Responsible AI in Public Data Systems", "AI", ["ARTIFICIAL_INTELLIGENCE", "DATA_PRIVACY"], "Technical"),
        ("SQL for Statistical Data Operations", "SQL", ["SQL", "DATA_ENGINEERING"], "Technical"),
        ("Data Visualisation for Decision Makers", "Visualization", ["DATA_VISUALIZATION", "COMMUNICATION"], "Technical"),
        ("Foundations of Sampling and Survey Design", "Survey", ["SURVEY_DESIGN", "SAMPLING"], "Statistical"),
        ("Metadata and Data Quality Essentials", "Quality", ["METADATA_STANDARDS", "DATA_QUALITY"], "Statistical"),
        ("SDG Indicator Production", "SDG", ["SDG_INDICATORS", "METADATA_STANDARDS"], "Statistical"),
        ("Cyber Hygiene for Government Officials", "Cyber", ["CYBERSECURITY", "DATA_PRIVACY"], "Digital Governance"),
        ("Cloud Concepts for Statistical Workloads", "Cloud", ["CLOUD_COMPUTING", "GOVERNMENT_CLOUD"], "Digital Governance"),
        ("Interoperability and Secure APIs", "APIs", ["APIS", "OPEN_DATA"], "Technical"),
        ("Machine Learning for Survey Quality", "ML", ["MACHINE_LEARNING", "PYTHON", "DATA_QUALITY"], "Technical"),
    ]
    if db.scalar(select(func.count()).select_from(Course)) == 0:
        for i in range(35):
            title, tag, codes, category = course_templates[i % len(course_templates)]
            comp_ids = [competency_by_code[c].id for c in codes]
            db.add(Course(
                course_id=f"IGOT-PROT-{i+1:03d}", title=f"{title}{f' — Cohort {i//len(course_templates)+1}' if i >= len(course_templates) else ''}",
                description=f"Prototype iGOT-style learning resource on {tag.lower()} for officials working with official statistics.",
                source="iGOT (prototype dataset)", duration_hours=float(2 + (i % 8)), difficulty=["beginner", "intermediate", "advanced"][i % 3],
                language="English", skills=[tag, "Official Statistics"], competency_ids=comp_ids,
                role_tags=["EMPLOYEE", "TRAINER"], department_tags=[d[1] for d in DEPARTMENTS],
                url="https://example.gov.in/igot-prototype", completion_status="not_started", is_prototype=True,
                localizations=(
                    {
                        "en": {
                            "title": "Python for Statistical Analysis",
                            "description": "Learn Python techniques used in statistical data analysis.",
                            "reason": "Python is prioritised because it is required for Survey Data Analysis and your role has a 35-point gap.",
                            "expected_outcome": "Build Python toward the Advanced target and reduce the current competency gap.",
                        },
                        "hi": {
                            "title": "सांख्यिकीय विश्लेषण के लिए पायथन",
                            "description": "सांख्यिकीय डेटा विश्लेषण में उपयोग की जाने वाली पायथन तकनीकों को सीखें।",
                            "reason": "पायथन को प्राथमिकता दी गई है क्योंकि यह सर्वेक्षण डेटा विश्लेषण के लिए आवश्यक है और आपकी भूमिका में 35 अंकों का अंतर है।",
                            "expected_outcome": "पायथन को उन्नत स्तर के लक्ष्य की ओर विकसित करें और वर्तमान दक्षता अंतर को कम करें।",
                        },
                        "label": "Prototype multilingual content",
                    }
                    if i == 0 else {}
                ),
            ))
        db.flush()

    bilingual_course = db.scalar(select(Course).where(Course.course_id == "IGOT-PROT-001"))
    if bilingual_course is not None:
        bilingual_course.title = "Python for Statistical Analysis"
        bilingual_course.description = "Learn Python techniques used in statistical data analysis."
        bilingual_course.localizations = {
            "en": {
                "title": "Python for Statistical Analysis",
                "description": "Learn Python techniques used in statistical data analysis.",
                "reason": "Python is prioritised because it is required for Survey Data Analysis and your role has a 35-point gap.",
                "expected_outcome": "Build Python toward the Advanced target and reduce the current competency gap.",
            },
            "hi": {
                "title": "सांख्यिकीय विश्लेषण के लिए पायथन",
                "description": "सांख्यिकीय डेटा विश्लेषण में उपयोग की जाने वाली पायथन तकनीकों को सीखें।",
                "reason": "पायथन को प्राथमिकता दी गई है क्योंकि यह सर्वेक्षण डेटा विश्लेषण के लिए आवश्यक है और आपकी भूमिका में 35 अंकों का अंतर है।",
                "expected_outcome": "पायथन को उन्नत स्तर के लक्ष्य की ओर विकसित करें और वर्तमान दक्षता अंतर को कम करें।",
            },
            "label": "Prototype multilingual content",
        }
        db.flush()

    if db.scalar(select(func.count()).select_from(TrainingProgramme)) == 0:
        programmes = [
            ("TPAC-SURVEY-01", "Advanced Survey Design and Estimation", "Survey methodology and estimation clinic for official-statistics professionals.", "Survey Methodology", 5, ["SURVEY_DESIGN", "SAMPLING"], "Survey Division"),
            ("NSSTA-DATA-02", "Data Quality Frameworks for Official Statistics", "Practice-led programme on quality dimensions, validation, and improvement cycles.", "Data Quality", 3, ["DATA_QUALITY", "METADATA_STANDARDS"], "National Statistical Office"),
            ("TPAC-GIS-03", "Geospatial Methods for Regional Statistics", "Hands-on training in spatial data, mapping, and regional evidence.", "Geospatial Analytics", 4, ["GIS", "DATA_VISUALIZATION"], "Survey Division"),
            ("NSSTA-AI-04", "Responsible AI for Public Data", "Governance, evaluation, and safe adoption of AI-assisted statistical workflows.", "Emerging Technologies", 3, ["ARTIFICIAL_INTELLIGENCE", "DATA_PRIVACY"], "Data Analytics Division"),
            ("TPAC-PM-05", "Leading Statistical Transformation", "Programme leadership, communication, and change management for statistical systems.", "Leadership", 2, ["LEADERSHIP", "PROJECT_MANAGEMENT", "COMMUNICATION"], "All departments"),
            ("NSSTA-CLOUD-06", "Cloud Readiness for Government Analytics", "Architecture patterns and controls for public-sector analytical workloads.", "Digital Governance", 3, ["CLOUD_COMPUTING", "GOVERNMENT_CLOUD"], "Data Analytics Division"),
            ("TPAC-OPEN-07", "Open Data and Statistical Dissemination", "Publishing trusted statistical products for reuse and policy support.", "Dissemination", 2, ["OPEN_DATA", "APIS", "COMMUNICATION"], "National Statistical Office"),
            ("NSSTA-LABOUR-08", "Modern Labour Statistics Production", "Concepts and operational practice for labour-statistics programmes.", "Domain Statistics", 4, ["LABOUR_STATISTICS", "SURVEY_DESIGN"], "Social Statistics Division"),
            ("TPAC-PRICE-09", "Price Index Compilation Clinic", "Applied methods for price collection, validation, and index production.", "Domain Statistics", 3, ["PRICE_STATISTICS", "DATA_QUALITY"], "Economic Statistics Division"),
            ("NSSTA-PIPE-10", "Data Engineering for Official Statistics", "Reliable data pipelines, lineage, and monitoring for statistical processing.", "Data Engineering", 4, ["DATA_ENGINEERING", "SQL", "PYTHON"], "Data Analytics Division"),
            ("TPAC-ETHICS-11", "Ethics and Impartiality in Official Statistics", "Strengthening integrity and public trust in statistical production.", "Professional Practice", 2, ["ETHICS", "DECISION_MAKING"], "All departments"),
            ("NSSTA-SDG-12", "SDG Indicator Metadata Lab", "Aligning indicator sources, metadata, and dissemination requirements.", "SDG Reporting", 2, ["SDG_INDICATORS", "METADATA_STANDARDS"], "Social Statistics Division"),
            ("TPAC-CYBER-13", "Cybersecurity for Statistical Operations", "Threat awareness, access controls, and incident readiness.", "Cybersecurity", 2, ["CYBERSECURITY", "DATA_PRIVACY"], "All departments"),
            ("NSSTA-ML-14", "Machine Learning Evaluation for Survey Teams", "Model evaluation, bias checks, and responsible experimentation.", "Machine Learning", 4, ["MACHINE_LEARNING", "PYTHON", "DATA_QUALITY"], "Survey Division"),
            ("TPAC-DPI-15", "Digital Public Infrastructure and Interoperability", "Understanding interoperable public digital services and APIs.", "Digital Governance", 3, ["DIGITAL_PUBLIC_INFRASTRUCTURE", "APIS"], "National Statistical Office"),
        ]
        for pid, name, desc, category, duration, codes, recommended_for in programmes:
            db.add(TrainingProgramme(
                programme_id=pid, programme_name=name, description=desc, category=category,
                duration_days=duration, target_group="Officials in India's Official Statistical System",
                competency_ids=[competency_by_code[c].id for c in codes], role_tags=["EMPLOYEE", "TRAINER"],
                recommended_for=[recommended_for], schedule="Prototype calendar — schedule to be confirmed",
                url="https://example.gov.in/nssta-tpac-prototype", source="NSSTA / TPAC (prototype dataset)", is_prototype=True,
            ))
        db.flush()

    if db.scalar(select(func.count()).select_from(Assessment)) == 0:
        assessments = [
            ("Competency Intelligence Baseline", "Cross-domain baseline across statistical, technical, digital-governance, and behavioural capabilities.", "Cross-domain", ["SURVEY_DESIGN", "SAMPLING", "DATA_QUALITY", "PYTHON", "SQL", "GIS", "ARTIFICIAL_INTELLIGENCE", "CYBERSECURITY", "DATA_PRIVACY", "LEADERSHIP"]),
            ("Official Statistics Foundations", "Baseline check across statistical concepts.", "Statistical", ["SURVEY_DESIGN", "SAMPLING", "DATA_QUALITY"]),
            ("Technical Readiness Pulse", "Baseline check across practical technical skills.", "Technical", ["PYTHON", "SQL", "DATA_VISUALIZATION"]),
            ("Digital Governance Essentials", "Baseline check across trusted digital work.", "Digital Governance", ["CYBERSECURITY", "DATA_PRIVACY", "APIS"]),
            ("Leadership for Evidence Systems", "Baseline check across managerial practice.", "Behavioural", ["LEADERSHIP", "COMMUNICATION", "DECISION_MAKING"]),
            ("AI and Emerging Technology Awareness", "Baseline check across future-oriented capability.", "Emerging Skills", ["ARTIFICIAL_INTELLIGENCE", "MACHINE_LEARNING", "CLOUD_COMPUTING"]),
            ("Survey Operations Quality", "Practice check for reliable survey delivery.", "Statistical", ["SURVEY_DESIGN", "SAMPLING", "DATA_QUALITY"]),
            ("Data Dissemination Readiness", "Practice check for communicating official evidence.", "Technical", ["DATA_VISUALIZATION", "OPEN_DATA", "COMMUNICATION"]),
            ("Metadata and Interoperability", "Practice check for reusable statistical data.", "Technical", ["METADATA_STANDARDS", "APIS", "OPEN_DATA"]),
            ("Privacy and Security at Work", "Practice check for safe data handling.", "Governance", ["DATA_PRIVACY", "CYBERSECURITY", "ETHICS"]),
            ("Project Delivery in Statistics", "Practice check for dependable programme execution.", "Managerial", ["PROJECT_MANAGEMENT", "LEADERSHIP", "DECISION_MAKING"]),
        ]
        for idx, (title, desc, category, codes) in enumerate(assessments, 1):
            comp_ids = [competency_by_code[c].id for c in codes]
            assessment = Assessment(title=title, description=desc, category=category, competency_ids=comp_ids, question_count=len(codes) * 2, is_published=True)
            db.add(assessment)
            db.flush()
            for q_index, code in enumerate(codes * 2):
                competency = competency_by_code[code]
                options = [
                    "A structured, evidence-based approach",
                    "An informal choice without validation",
                    "A process that ignores metadata",
                    "A process that cannot be reviewed",
                ]
                db.add(AssessmentQuestion(
                    assessment_id=assessment.id, competency_id=competency.id,
                    question=f"Which statement best reflects sound practice in {competency.name.lower()}?",
                    options=options, correct_answer=options[0], difficulty=["easy", "medium", "hard"][q_index % 3],
                    explanation=f"Sound {competency.name.lower()} practice is structured, evidence-based, and open to review.",
                ))

    bilingual = db.scalar(select(Assessment).where(Assessment.title == "Bilingual Python Learning Check"))
    if bilingual is None:
        python = competency_by_code["PYTHON"]
        bilingual = Assessment(
            title="Bilingual Python Learning Check",
            description="A curated English/Hindi demonstration of language-independent assessment scoring.",
            category="Technical",
            competency_ids=[python.id],
            question_count=2,
            is_published=True,
        )
        db.add(bilingual)
        db.flush()
        bilingual_questions = [
            (
                "Which practice supports reproducible statistical analysis?",
                "सांख्यिकीय विश्लेषण को पुनरुत्पाद्य बनाने में कौन-सी पद्धति सहायक है?",
                ["Documented Python code", "Unrecorded manual edits", "Ignoring data checks", "Deleting source notes"],
                ["दस्तावेजित पायथन कोड", "बिना दर्ज किए गए मैनुअल बदलाव", "डेटा जाँच को अनदेखा करना", "स्रोत टिप्पणियाँ हटाना"],
                "Use documented Python code so the analysis can be repeated and reviewed.",
                "दस्तावेजित पायथन कोड का उपयोग करें ताकि विश्लेषण को दोहराया और जाँचा जा सके।",
            ),
            (
                "What should a statistical data workflow preserve?",
                "सांख्यिकीय डेटा कार्यप्रवाह में क्या सुरक्षित रखा जाना चाहिए?",
                ["Lineage and assumptions", "Only the final number", "Unverified changes", "Hidden calculations"],
                ["डेटा वंशावली और धारणाएँ", "केवल अंतिम संख्या", "असत्यापित बदलाव", "छिपी हुई गणनाएँ"],
                "Lineage and assumptions make a statistical workflow transparent and reviewable.",
                "डेटा वंशावली और धारणाएँ सांख्यिकीय कार्यप्रवाह को पारदर्शी और जाँच योग्य बनाती हैं।",
            ),
        ]
        for question_en, question_hi, options_en, options_hi, explanation_en, explanation_hi in bilingual_questions:
            db.add(AssessmentQuestion(
                assessment_id=bilingual.id,
                competency_id=python.id,
                question=question_en,
                options=options_en,
                correct_answer=options_en[0],
                difficulty="easy",
                explanation=explanation_en,
                localizations={"hi": {"question": question_hi, "options": options_hi, "explanation": explanation_hi}, "label": "Prototype multilingual content"},
            ))

    python = competency_by_code["PYTHON"]
    bilingual_item = db.scalar(select(AssessmentItem).where(AssessmentItem.topic == "Bilingual Python Demo"))
    if bilingual_item is None:
        bilingual_item = AssessmentItem(
            document_id=None,
            competency_id=python.id,
            question="Which practice supports reproducible statistical analysis?",
            options=["Documented Python code", "Unrecorded manual edits", "Ignoring data checks", "Deleting source notes"],
            correct_index=0,
            explanation="Use documented Python code so the analysis can be repeated and reviewed.",
            topic="Bilingual Python Demo",
            difficulty="easy",
            source={"source_type": "curated_demo", "label": "Prototype multilingual content"},
            status="PUBLISHED",
            confidence=0.98,
            generated_by="curated_prototype",
            localizations={"hi": {"question": "सांख्यिकीय विश्लेषण को पुनरुत्पाद्य बनाने में कौन-सी पद्धति सहायक है?", "options": ["दस्तावेजित पायथन कोड", "बिना दर्ज किए गए मैनुअल बदलाव", "डेटा जाँच को अनदेखा करना", "स्रोत टिप्पणियाँ हटाना"], "explanation": "दस्तावेजित पायथन कोड का उपयोग करें ताकि विश्लेषण को दोहराया और जाँचा जा सके।"}, "label": "Prototype multilingual content"},
        )
        db.add(bilingual_item)
        db.flush()
    else:
        bilingual_item.status = "PUBLISHED"
        bilingual_item.localizations = {"hi": {"question": "सांख्यिकीय विश्लेषण को पुनरुत्पाद्य बनाने में कौन-सी पद्धति सहायक है?", "options": ["दस्तावेजित पायथन कोड", "बिना दर्ज किए गए मैनुअल बदलाव", "डेटा जाँच को अनदेखा करना", "स्रोत टिप्पणियाँ हटाना"], "explanation": "दस्तावेजित पायथन कोड का उपयोग करें ताकि विश्लेषण को दोहराया और जाँचा जा सके।"}, "label": "Prototype multilingual content"}
    bilingual_quiz = db.scalar(select(PublishedQuiz).where(PublishedQuiz.title == "Bilingual Python Demo Quiz"))
    if bilingual_quiz is None:
        trainer_user = user_by_email.get("trainer.demo@aistatgrowth.gov.in")
        if trainer_user:
            bilingual_quiz = PublishedQuiz(title="Bilingual Python Demo Quiz", document_id=None, item_ids=[bilingual_item.id], created_by=trainer_user.id, status="PUBLISHED")
            db.add(bilingual_quiz)
            db.flush()

    if db.scalar(select(func.count()).select_from(SkillForecast)) == 0:
        forecast_codes = {"ARTIFICIAL_INTELLIGENCE": (58, 88), "CLOUD_COMPUTING": (51, 79), "GIS": (49, 76), "DATA_ENGINEERING": (54, 84), "CYBERSECURITY": (64, 86), "PYTHON": (62, 82), "MACHINE_LEARNING": (44, 74)}
        for code, (current, projected) in forecast_codes.items():
            competency = competency_by_code[code]
            db.add(SkillForecast(
                competency_id=competency.id, current_demand=current, projected_demand=projected,
                growth_rate=round((projected-current) / current * 100, 1), affected_departments=[d[0] for d in DEPARTMENTS],
                training_priority="high" if projected-current >= 25 else "medium", period="2026-2030", source="prototype_seed", confidence=0.45, is_prototype=True,
            ))

    if db.scalar(select(func.count()).select_from(FutureSkillDemand)) == 0:
        forecast_codes = {"ARTIFICIAL_INTELLIGENCE": (58, 88), "CLOUD_COMPUTING": (51, 79), "GIS": (49, 76), "DATA_ENGINEERING": (54, 84), "CYBERSECURITY": (64, 86), "PYTHON": (62, 82), "MACHINE_LEARNING": (44, 74)}
        for code, (current, projected) in forecast_codes.items():
            competency = competency_by_code[code]
            db.add(FutureSkillDemand(
                competency_id=competency.id, current_demand=current, projected_demand=projected,
                growth_rate=round((projected-current) / current * 100, 1), priority="high" if projected-current >= 25 else "medium",
                period="2026-2030", source="prototype_seed", confidence=0.45, affected_departments=[d[0] for d in DEPARTMENTS],
            ))

    if db.scalar(select(func.count()).select_from(LearningProgress)) == 0:
        employee = user_by_email.get("employee.demo@aistatgrowth.gov.in")
        courses = db.scalars(select(Course).limit(6)).all()
        for index, course in enumerate(courses):
            db.add(LearningProgress(
                user_id=employee.id, resource_type="course", resource_id=course.id,
                status="completed" if index < 2 else "in_progress", completion_percent=100 if index < 2 else 48,
                learning_hours=course.duration_hours if index < 2 else course.duration_hours * 0.48,
                last_activity_at=datetime.now(timezone.utc) - timedelta(days=index + 1),
            ))

    db.commit()
    return {
        "roles": db.scalar(select(func.count()).select_from(Role)) or 0,
        "departments": db.scalar(select(func.count()).select_from(Department)) or 0,
        "users": db.scalar(select(func.count()).select_from(User)) or 0,
        "competencies": db.scalar(select(func.count()).select_from(Competency)) or 0,
        "courses": db.scalar(select(func.count()).select_from(Course)) or 0,
        "training_programmes": db.scalar(select(func.count()).select_from(TrainingProgramme)) or 0,
        "assessments": db.scalar(select(func.count()).select_from(Assessment)) or 0,
        "skill_forecasts": db.scalar(select(func.count()).select_from(SkillForecast)) or 0,
        "frac_positions": db.scalar(select(func.count()).select_from(Position)) or 0,
        "frac_roles": db.scalar(select(func.count()).select_from(PositionRole)) or 0,
        "frac_activities": db.scalar(select(func.count()).select_from(Activity)) or 0,
        "baseline_evidence": db.scalar(select(func.count()).select_from(CompetencyEvidence)) or 0,
        "future_skill_demand": db.scalar(select(func.count()).select_from(FutureSkillDemand)) or 0,
    }
