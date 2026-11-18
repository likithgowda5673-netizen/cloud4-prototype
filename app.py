import os
import sqlite3
from contextlib import contextmanager
from datetime import date
from functools import wraps
from urllib.parse import urlparse
from uuid import uuid4

from flask import Flask, abort, flash, jsonify, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "local-prototype-secret")
app.config["CERTIFICATE_DATABASE"] = os.environ.get(
    "CERTIFICATE_DATABASE",
    os.path.join(app.instance_path, "certificates.sqlite3"),
)

COURSES = [
    {
        "id": "cloud-foundations",
        "title": "Cloud Foundations",
        "category": "Cloud",
        "level": "Beginner",
        "duration": "4 weeks",
        "lessons": 12,
        "icon": "☁",
        "accent": "blue",
        "description": "Build a confident foundation in cloud concepts, services, and architecture.",
        "tag": "Popular",
    },
    {
        "id": "aws-solutions",
        "title": "AWS Solutions Architect",
        "category": "Cloud",
        "level": "Intermediate",
        "duration": "6 weeks",
        "lessons": 18,
        "icon": "⌘",
        "accent": "orange",
        "description": "Design secure, resilient, and cost-aware solutions on AWS.",
        "tag": "Certification prep",
    },
    {
        "id": "azure-administrator",
        "title": "Azure Administrator",
        "category": "Cloud",
        "level": "Intermediate",
        "duration": "5 weeks",
        "lessons": 16,
        "icon": "◈",
        "accent": "cyan",
        "description": "Manage identities, storage, compute, and networks in Microsoft Azure.",
        "tag": "Hands-on labs",
    },
    {
        "id": "ai-playground",
        "title": "AI & Machine Learning",
        "category": "Artificial intelligence",
        "level": "Beginner",
        "duration": "3 weeks",
        "lessons": 10,
        "icon": "✳",
        "accent": "purple",
        "description": "Explore practical AI and machine learning workflows through guided labs.",
        "tag": "New",
    },
    {
        "id": "devops-practice",
        "title": "DevOps in Practice",
        "category": "DevOps",
        "level": "Intermediate",
        "duration": "4 weeks",
        "lessons": 14,
        "icon": "⌘",
        "accent": "green",
        "description": "Connect source control, automation, containers, and delivery pipelines.",
        "tag": "Project-based",
    },
    {
        "id": "google-cloud",
        "title": "Google Cloud Essentials",
        "category": "Cloud",
        "level": "Beginner",
        "duration": "3 weeks",
        "lessons": 11,
        "icon": "G",
        "accent": "yellow",
        "description": "Get started with core Google Cloud products and deployment patterns.",
        "tag": "Self-paced",
    },
]

SAMPLE_COURSE_ID = "cloud-foundations"
SAMPLE_LESSONS = [
    "What is cloud computing?",
    "IaaS, PaaS, and SaaS",
    "Public, private, and hybrid cloud",
    "Regions and availability zones",
    "Cloud compute essentials",
    "Storage and object storage",
    "Virtual networks and subnets",
    "Identity and access management",
    "The shared responsibility model",
    "Security and compliance basics",
    "Cloud cost management",
    "Putting it all together",
]

COURSE_LESSONS = {
    SAMPLE_COURSE_ID: SAMPLE_LESSONS,
    "aws-solutions": [
        "AWS global infrastructure and Well-Architected basics",
        "Accounts, IAM users, roles, and policies",
        "VPCs, subnets, and route tables",
        "Security groups and network access control lists",
        "EC2 instance types and right-sizing",
        "Auto Scaling and Elastic Load Balancing",
        "S3 storage classes and lifecycle rules",
        "EBS, EFS, and shared file storage",
        "RDS and Aurora high availability",
        "DynamoDB partitioning and scaling",
        "Lambda and API Gateway patterns",
        "SQS, SNS, and EventBridge messaging",
        "Route 53, DNS, and CloudFront",
        "Multi-AZ and multi-region resilience",
        "Backup, recovery, and disaster planning",
        "Encryption, secrets, and key management",
        "Monitoring and observability with CloudWatch",
        "Cost optimization architecture review",
    ],
    "azure-administrator": [
        "Azure regions, subscriptions, and resource groups",
        "Microsoft Entra ID and identity basics",
        "Role-based access control and governance",
        "Virtual networks and subnet design",
        "Network security groups and connectivity",
        "Virtual machine deployment and sizing",
        "Availability sets, zones, and scale sets",
        "Blob storage and access tiers",
        "Managed disks and file shares",
        "Azure SQL and database options",
        "Backup and site recovery",
        "Azure Monitor and Log Analytics",
        "Key Vault and platform security",
        "Policy, tags, and resource locks",
        "Cost management and budgets",
        "Administrator skills review lab",
    ],
    "ai-playground": [
        "AI, machine learning, and generative AI",
        "How supervised learning works",
        "Preparing and exploring a dataset",
        "Training and evaluating a first model",
        "Overfitting, validation, and model quality",
        "Neural networks in plain language",
        "Prompting and responsible generative AI",
        "Embeddings and semantic search",
        "AI safety, privacy, and bias",
        "Build a small end-to-end AI project",
    ],
    "devops-practice": [
        "DevOps principles and team workflows",
        "Git branches, commits, and pull requests",
        "Automated testing in a CI pipeline",
        "Build and package an application",
        "Containers and Docker images",
        "Deploy with a continuous delivery pipeline",
        "Infrastructure as code fundamentals",
        "Configuration and secrets management",
        "Kubernetes workloads and services",
        "Release strategies and rollbacks",
        "Logs, metrics, and tracing",
        "Reliability and incident response",
        "Pipeline security and dependency checks",
        "Ship a complete DevOps project",
    ],
    "google-cloud": [
        "Google Cloud projects and resource hierarchy",
        "IAM roles, service accounts, and policies",
        "Compute Engine and machine types",
        "Cloud Run and serverless applications",
        "Cloud Storage buckets and lifecycle",
        "VPC networks and firewall rules",
        "Cloud SQL and managed databases",
        "BigQuery and data analytics basics",
        "Cloud monitoring and logging",
        "Security, budgets, and cost controls",
        "Deploy a small Google Cloud solution",
    ],
}

COURSE_CERTIFICATE_PREFIXES = {
    "cloud-foundations": "CLOUD",
    "aws-solutions": "AWS",
    "azure-administrator": "AZURE",
    "ai-playground": "AI",
    "devops-practice": "DEVOPS",
    "google-cloud": "GCP",
}

COURSE_HELP_TOPICS = {
    "cloud-foundations": [
        {
            "question": "What is cloud computing?",
            "keywords": ("cloud computing", "what is cloud", "define cloud"),
            "answer": (
                "Cloud computing is on-demand access to computing resources—such as "
                "servers, storage, and databases—over a network. You can provision "
                "them when needed instead of owning all the physical infrastructure."
            ),
        },
        {
            "question": "How are IaaS, PaaS, and SaaS different?",
            "keywords": ("iaas", "paas", "saas", "service model"),
            "answer": (
                "IaaS gives you building blocks such as virtual machines, PaaS gives "
                "you a managed platform for building and running apps, and SaaS is a "
                "complete application you use over the internet. A quick memory aid: "
                "infrastructure, platform, software."
            ),
        },
        {
            "question": "What is the difference between a region and an availability zone?",
            "keywords": ("region", "availability zone", "availability zones", "zone"),
            "answer": (
                "A region is a geographic area where a cloud provider operates. It "
                "contains multiple, separate availability zones. Spreading a workload "
                "across zones can improve resilience if one zone has an outage."
            ),
        },
        {
            "question": "What does shared responsibility mean?",
            "keywords": ("shared responsibility", "responsibility model"),
            "answer": (
                "The cloud provider secures the cloud infrastructure; you secure what "
                "you put in the cloud. The exact split depends on the service: with a "
                "virtual machine you manage more, while a managed application service "
                "shifts more maintenance to the provider."
            ),
        },
        {
            "question": "When should I use object storage?",
            "keywords": ("object storage", "storage", "bucket"),
            "answer": (
                "Object storage keeps data as objects with metadata and a unique key, "
                "rather than as files on a traditional disk. It works well for "
                "unstructured data such as images, backups, and logs."
            ),
        },
        {
            "question": "How do virtual networks and subnets work?",
            "keywords": ("subnet", "virtual network", "vpc", "network"),
            "answer": (
                "A virtual network is an isolated network space you configure in the "
                "cloud. Subnets divide its IP address range into smaller segments, "
                "often to separate public-facing resources from private services."
            ),
        },
        {
            "question": "How can I keep cloud costs under control?",
            "keywords": ("cost", "pricing", "save money", "expensive", "budget"),
            "answer": (
                "Cloud costs are easier to manage when you right-size resources, turn "
                "off unused environments, set budgets and alerts, and review usage "
                "regularly. Start with the resource's actual workload rather than its "
                "maximum capacity."
            ),
        },
    ],
    "aws-solutions": [
        {
            "question": "How do IAM roles and policies work?",
            "keywords": ("iam", "role", "policy", "least privilege"),
            "answer": (
                "An IAM policy states which actions are allowed or denied on which "
                "resources. Attach policies to a role, then let a trusted user or AWS "
                "service assume that role for temporary credentials. Grant only the "
                "permissions needed for the task."
            ),
        },
        {
            "question": "How should I divide a VPC into subnets?",
            "keywords": ("vpc", "subnet", "route table", "security group", "nacl"),
            "answer": (
                "A VPC defines your private IP space. Place internet-facing resources "
                "in public subnets with a route to an internet gateway, and keep "
                "application or data tiers in private subnets. Use security groups "
                "for resource-level traffic rules and route tables to direct traffic."
            ),
        },
        {
            "question": "When should I use S3 instead of EBS?",
            "keywords": ("s3", "ebs", "object storage", "storage class"),
            "answer": (
                "S3 is durable object storage, a good fit for files, backups, and "
                "data accessed through an API. EBS provides block storage attached "
                "to an EC2 instance, like a disk for an operating system or database. "
                "Choose based on how the application needs to access the data."
            ),
        },
        {
            "question": "How can I design for high availability in AWS?",
            "keywords": ("availability", "multi-az", "multi-region", "resilience", "load balancer"),
            "answer": (
                "Run redundant application capacity across multiple Availability "
                "Zones and place a load balancer in front of it. Add health checks, "
                "automated recovery, and tested backups. Use multiple Regions when "
                "the recovery goals justify the extra complexity and cost."
            ),
        },
        {
            "question": "When is Lambda a good choice?",
            "keywords": ("lambda", "serverless", "api gateway", "eventbridge"),
            "answer": (
                "Lambda runs code in response to events without you managing servers. "
                "It works well for short-lived APIs, scheduled jobs, and event "
                "processing. Check execution time, concurrency, and downstream limits "
                "when designing the workflow."
            ),
        },
        {
            "question": "How do I right-size AWS resources?",
            "keywords": ("cost", "right-size", "right size", "cost optimization", "pricing"),
            "answer": (
                "Start from measured CPU, memory, storage, and network usage instead "
                "of selecting the largest instance by default. Review utilization "
                "over representative periods, scale elastically where possible, and "
                "set budgets and cost alerts."
            ),
        },
    ],
    "azure-administrator": [
        {
            "question": "How do Entra ID and Azure RBAC differ?",
            "keywords": ("entra", "identity", "rbac", "role assignment"),
            "answer": (
                "Microsoft Entra ID handles identities and sign-in. Azure RBAC "
                "controls what an identity can do to Azure resources. Assign a "
                "built-in or custom role at the narrowest practical scope, such as "
                "one resource group, and follow least privilege."
            ),
        },
        {
            "question": "How do virtual networks and network security groups work?",
            "keywords": ("virtual network", "vnet", "subnet", "network security group", "nsg"),
            "answer": (
                "An Azure virtual network provides an isolated IP address space, "
                "which you divide into subnets. Network security group rules filter "
                "inbound and outbound traffic for subnets or network interfaces. "
                "Allow only the required ports and sources."
            ),
        },
        {
            "question": "When should I use an availability zone for a VM?",
            "keywords": ("virtual machine", "vm", "availability zone", "availability set", "scale set"),
            "answer": (
                "Availability zones are physically separate locations within a "
                "region, so distributing VMs across zones can protect against a "
                "single-zone outage. Availability sets spread VMs across fault and "
                "update domains within a datacenter. Choose based on your resilience "
                "needs and supported region."
            ),
        },
        {
            "question": "What is Azure Blob Storage best for?",
            "keywords": ("blob", "storage", "access tier", "lifecycle"),
            "answer": (
                "Blob Storage is Azure object storage for unstructured data such as "
                "documents, images, and backups. Access tiers trade retrieval cost "
                "against storage cost. Use lifecycle rules to move or expire data "
                "according to how often it is accessed and how long it must be kept."
            ),
        },
        {
            "question": "How do I monitor and control Azure costs?",
            "keywords": ("monitor", "log analytics", "cost", "budget", "alert"),
            "answer": (
                "Azure Monitor collects metrics and logs; Log Analytics lets you "
                "query log data. For spending, create budgets and alerts in Cost "
                "Management, tag resources for ownership, and review usage regularly. "
                "A budget alerts you but does not automatically cap spending."
            ),
        },
    ],
    "ai-playground": [
        {
            "question": "How does supervised machine learning work?",
            "keywords": ("supervised", "labeled data", "labelled data", "training data"),
            "answer": (
                "Supervised learning uses examples paired with known answers. A model "
                "learns patterns from the training set, then you evaluate it on "
                "separate data it did not train on. Classification predicts categories; "
                "regression predicts numeric values."
            ),
        },
        {
            "question": "Why split data into training and validation sets?",
            "keywords": ("validation", "overfitting", "train test", "training set", "evaluation"),
            "answer": (
                "Training data teaches the model; validation data helps compare "
                "choices while developing it; a held-out test set estimates final "
                "performance. If training performance is strong but validation "
                "performance is weak, the model may be overfitting."
            ),
        },
        {
            "question": "What are embeddings and semantic search?",
            "keywords": ("embedding", "semantic search", "vector", "similarity"),
            "answer": (
                "An embedding represents text or another item as a numeric vector. "
                "Items with similar meaning tend to have nearby vectors, so semantic "
                "search can retrieve conceptually related content even when the exact "
                "keywords differ."
            ),
        },
        {
            "question": "How can I make a generative AI prompt clearer?",
            "keywords": ("prompt", "generative ai", "large language model", "llm"),
            "answer": (
                "State the task, provide relevant context, specify the audience and "
                "desired format, and include constraints. For important outputs, "
                "verify facts and test examples. A clear prompt improves consistency "
                "but does not guarantee a correct answer."
            ),
        },
        {
            "question": "What should I check for AI bias and privacy?",
            "keywords": ("bias", "fairness", "privacy", "responsible ai", "safety"),
            "answer": (
                "Check whether the data represents the people affected, compare "
                "error rates across relevant groups, and review how outputs will be "
                "used. Minimize personal data, respect consent and retention rules, "
                "and provide human review for consequential decisions."
            ),
        },
    ],
    "devops-practice": [
        {
            "question": "What happens in a CI/CD pipeline?",
            "keywords": ("ci/cd", "pipeline", "continuous integration", "continuous delivery", "deployment"),
            "answer": (
                "A CI pipeline builds each change and runs automated checks so "
                "problems are found early. A delivery or deployment stage packages "
                "and releases a verified artifact. Keep stages repeatable and promote "
                "the same artifact between environments."
            ),
        },
        {
            "question": "How do branches and pull requests help a team?",
            "keywords": ("git", "branch", "pull request", "merge", "commit"),
            "answer": (
                "A branch isolates a set of changes while the main branch stays "
                "stable. A pull request lets teammates review the diff and automated "
                "checks before merging. Keep changes focused and resolve feedback "
                "before integrating."
            ),
        },
        {
            "question": "What is the difference between an image and a container?",
            "keywords": ("docker", "container", "image", "containerization"),
            "answer": (
                "A container image is an immutable package containing an application "
                "and its runtime dependencies. A container is a running instance of "
                "that image. Build small, versioned images and avoid putting secrets "
                "inside them."
            ),
        },
        {
            "question": "Why use infrastructure as code?",
            "keywords": ("infrastructure as code", "iac", "terraform", "declarative"),
            "answer": (
                "Infrastructure as code describes environments in versioned files, "
                "so they can be reviewed, repeated, and changed consistently. Preview "
                "the proposed changes before applying them, and protect state and "
                "credentials."
            ),
        },
        {
            "question": "How should I handle a failed deployment?",
            "keywords": ("rollback", "release strategy", "deployment failure", "failed deployment", "blue green", "canary"),
            "answer": (
                "Use health checks and deployment metrics to detect regressions "
                "quickly. Keep a known-good artifact available and define a rollback "
                "or roll-forward procedure before release. Canary and blue-green "
                "strategies reduce the impact of a bad change."
            ),
        },
        {
            "question": "What should I monitor in production?",
            "keywords": ("monitor", "monitoring", "logs", "metrics", "tracing", "observability"),
            "answer": (
                "Use metrics to track service health and trends, logs to inspect "
                "events, and traces to follow a request across components. Connect "
                "alerts to user-impacting symptoms and include enough context to "
                "investigate without exposing secrets."
            ),
        },
    ],
    "google-cloud": [
        {
            "question": "How do projects and IAM work in Google Cloud?",
            "keywords": ("project", "iam", "service account", "role", "resource hierarchy"),
            "answer": (
                "A Google Cloud project groups resources and provides an administration "
                "boundary. IAM roles grant permissions to users or service accounts "
                "on resources. Grant only the needed role at the narrowest useful "
                "scope, and avoid long-lived service account keys where possible."
            ),
        },
        {
            "question": "When should I use Compute Engine or Cloud Run?",
            "keywords": ("compute engine", "cloud run", "serverless", "virtual machine", "vm"),
            "answer": (
                "Compute Engine gives you configurable virtual machines and more "
                "control over the operating system. Cloud Run runs containerized "
                "services without you managing servers and can scale based on "
                "requests. Choose based on control, workload shape, and operational needs."
            ),
        },
        {
            "question": "What is a Cloud Storage bucket?",
            "keywords": ("cloud storage", "bucket", "object storage", "lifecycle"),
            "answer": (
                "A Cloud Storage bucket holds objects such as files and backups. "
                "Choose location, access controls, and a storage class based on "
                "availability and access patterns. Lifecycle rules can transition "
                "or delete objects when they meet conditions."
            ),
        },
        {
            "question": "How do VPC networks and firewall rules work?",
            "keywords": ("vpc", "network", "firewall", "subnet", "connectivity"),
            "answer": (
                "A VPC network provides private connectivity for Google Cloud "
                "resources. Subnets define IP ranges in regions, and firewall rules "
                "control traffic to or from instances. Start with restrictive rules "
                "and allow only the required sources, targets, and ports."
            ),
        },
        {
            "question": "When should I use BigQuery?",
            "keywords": ("bigquery", "analytics", "data warehouse", "sql"),
            "answer": (
                "BigQuery is a managed analytics data warehouse designed for SQL "
                "queries over large datasets. It is a good fit for analytical "
                "workloads rather than as a general-purpose transactional database. "
                "Partitioning and filtering data can help control query cost."
            ),
        },
        {
            "question": "How do I monitor Google Cloud costs?",
            "keywords": ("cost", "budget", "billing", "monitoring", "logging"),
            "answer": (
                "Use Cloud Billing reports and budgets to understand spend and set "
                "alerts. Budgets notify you; they do not automatically stop usage. "
                "Use Cloud Monitoring for service metrics and Cloud Logging for "
                "events, and review resource labels to identify ownership."
            ),
        },
    ],
}

CERTIFICATES = {
    "C4G-CLOUD-2026-001": {
        "learner": "Alex Morgan",
        "course": "Cloud Foundations",
        "issued": "October 12, 2026",
    },
    "C4G-AWS-2026-014": {
        "learner": "Maya Chen",
        "course": "AWS Solutions Architect",
        "issued": "September 28, 2026",
    },
}


def certificate_connection():
    database_directory = os.path.dirname(
        os.path.abspath(app.config["CERTIFICATE_DATABASE"])
    )
    os.makedirs(database_directory, exist_ok=True)
    return sqlite3.connect(app.config["CERTIFICATE_DATABASE"])


@contextmanager
def certificate_database():
    connection = certificate_connection()
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_certificate_store():
    with certificate_database() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS certificates (
                code TEXT PRIMARY KEY,
                learner TEXT NOT NULL,
                learner_key TEXT NOT NULL,
                course_id TEXT NOT NULL,
                course TEXT NOT NULL,
                issued TEXT NOT NULL,
                UNIQUE (learner_key, course_id)
            )
            """
        )


def certificate_record(code, learner, course, issued, is_sample=False):
    return {
        "code": code,
        "learner": learner,
        "course": course,
        "issued": issued,
        "is_sample": is_sample,
    }


def get_certificate(code):
    if code in CERTIFICATES:
        record = CERTIFICATES[code]
        return certificate_record(
            code, record["learner"], record["course"], record["issued"], is_sample=True
        )
    with certificate_database() as connection:
        row = connection.execute(
            "SELECT code, learner, course, issued FROM certificates WHERE code = ?",
            (code,),
        ).fetchone()
    if not row:
        return None
    return certificate_record(*row)


def get_learner_certificate(learner, course_id):
    with certificate_database() as connection:
        row = connection.execute(
            "SELECT code, learner, course, issued FROM certificates "
            "WHERE learner_key = ? AND course_id = ?",
            (learner.casefold(), course_id),
        ).fetchone()
    if not row:
        return None
    return certificate_record(*row)


def issue_certificate(learner, course_id, course_title):
    learner_key = learner.casefold()
    existing = get_learner_certificate(learner, course_id)
    if existing:
        return existing

    issued = date.today().strftime("%B %d, %Y")
    prefix = COURSE_CERTIFICATE_PREFIXES[course_id]
    with certificate_database() as connection:
        for _ in range(3):
            code = f"C4G-{prefix}-{date.today().year}-{uuid4().hex[:12].upper()}"
            try:
                connection.execute(
                    """
                    INSERT INTO certificates
                        (code, learner, learner_key, course_id, course, issued)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT (learner_key, course_id) DO NOTHING
                    """,
                    (code, learner, learner_key, course_id, course_title, issued),
                )
            except sqlite3.IntegrityError:
                row = connection.execute(
                    "SELECT code, learner, course, issued FROM certificates "
                    "WHERE learner_key = ? AND course_id = ?",
                    (learner_key, course_id),
                ).fetchone()
                if row:
                    return certificate_record(*row)
                continue
            row = connection.execute(
                "SELECT code, learner, course, issued FROM certificates "
                "WHERE learner_key = ? AND course_id = ?",
                (learner_key, course_id),
            ).fetchone()
            if row:
                return certificate_record(*row)
    raise RuntimeError("Unable to issue a unique course certificate.")


def get_enrolled_courses():
    enrolled_ids = session.get("enrolled_courses", [])
    return [course for course in COURSES if course["id"] in enrolled_ids]


def get_course_progress(course):
    course_id = course["id"]
    total = course["lessons"]
    completed_by_course = session.get("course_completions", {})
    completed_values = (
        completed_by_course.get(course_id, [])
        if isinstance(completed_by_course, dict)
        else []
    )
    if course_id == SAMPLE_COURSE_ID:
        completed_values = [
            *completed_values,
            *session.get("completed_lessons", []),
        ]
    completed = {
        lesson
        for lesson in completed_values
        if isinstance(lesson, int) and 1 <= lesson <= total
    }
    count = len(completed)
    return {
        "completed": count,
        "total": total,
        "percent": round(count / total * 100),
        "points": count * 10,
        "completed_lessons": sorted(completed),
    }


def get_overall_progress():
    enrolled = get_enrolled_courses()
    courses = [
        {"course": course, **get_course_progress(course)}
        for course in enrolled
    ]
    completed = sum(course["completed"] for course in courses)
    total = sum(course["total"] for course in courses)
    milestones = [
        {"icon": "✦", "title": "First steps", "detail": "Complete your first lesson", "required": 1},
        {"icon": "↗", "title": "On a roll", "detail": "Complete 3 lessons", "required": 3},
        {"icon": "◈", "title": "Halfway there", "detail": "Complete 6 lessons", "required": 6},
        {
            "icon": "★",
            "title": "Course finisher",
            "detail": "Complete all lessons in a course",
            "required": None,
        },
    ]
    for milestone in milestones:
        milestone["earned"] = (
            any(course["completed"] == course["total"] for course in courses)
            if milestone["required"] is None
            else completed >= milestone["required"]
        )
    return {
        "completed": completed,
        "total": total,
        "percent": round(completed / total * 100) if total else 0,
        "points": completed * 10,
        "course_count": len(enrolled),
        "milestones": milestones,
        "courses": courses,
    }


def get_completed_course_certificates():
    certificates = []
    for course in get_enrolled_courses():
        progress = get_course_progress(course)
        if progress["completed"] == progress["total"]:
            certificate = get_learner_certificate(
                session["user_name"], course["id"]
            )
            if certificate:
                certificates.append(certificate)
    return certificates


def get_leaderboard():
    progress = get_overall_progress()
    learners = [
        {"name": "Maya Chen", "points": 100, "label": "12 lessons"},
        {"name": "Jordan Lee", "points": 70, "label": "7 lessons"},
        {"name": "Sam Rivera", "points": 40, "label": "4 lessons"},
    ]
    learners = [
        learner
        for learner in learners
        if learner["name"].casefold() != session.get("user_name", "").casefold()
    ]
    learners.append(
        {
            "name": session.get("user_name", "You"),
            "points": progress["points"],
            "label": f'{progress["completed"]} lessons',
            "is_current_user": True,
        }
    )
    learners.sort(key=lambda learner: learner["points"], reverse=True)
    for rank, learner in enumerate(learners, start=1):
        learner["rank"] = rank
    return learners


def safe_referrer(default_endpoint):
    referrer = request.referrer
    if referrer:
        parsed_referrer = urlparse(referrer)
        if (
            parsed_referrer.scheme in {"http", "https"}
            and parsed_referrer.netloc == request.host
            and parsed_referrer.path.startswith("/")
            and not parsed_referrer.path.startswith("//")
        ):
            return referrer
    return url_for(default_endpoint)


def safe_next_url(value, default_endpoint="dashboard"):
    if value:
        parsed_value = urlparse(value)
        if (
            not parsed_value.scheme
            and not parsed_value.netloc
            and parsed_value.path.startswith("/")
            and not parsed_value.path.startswith("//")
            and not parsed_value.path.startswith("/\\")
            and "\\" not in value
        ):
            return value
    return url_for(default_endpoint)


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("user_name"):
            if request.method == "GET":
                next_url = request.full_path
                if next_url.endswith("?"):
                    next_url = next_url[:-1]
            else:
                next_url = safe_referrer("dashboard")
            return redirect(url_for("login", next=next_url))
        return view(*args, **kwargs)

    return wrapped_view


@app.context_processor
def inject_navigation_data():
    return {
        "current_user": session.get("user_name"),
        "enrolled_count": len(session.get("enrolled_courses", [])),
        "progress_summary": get_overall_progress(),
    }


@app.get("/")
def home():
    return render_template("home.html", courses=COURSES[:3])


@app.get("/dashboard")
@login_required
def dashboard():
    enrolled = get_enrolled_courses()
    return render_template(
        "dashboard.html",
        courses=enrolled,
        course_progress={
            course["id"]: get_course_progress(course) for course in enrolled
        },
    )


@app.get("/courses")
def courses():
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "All")
    visible_courses = COURSES
    if category != "All":
        visible_courses = [
            course for course in visible_courses if course["category"] == category
        ]
    if query:
        normalized_query = query.casefold()
        visible_courses = [
            course
            for course in visible_courses
            if normalized_query in course["title"].casefold()
            or normalized_query in course["description"].casefold()
            or normalized_query in course["category"].casefold()
        ]
    categories = sorted({course["category"] for course in COURSES})
    return render_template(
        "courses.html",
        courses=visible_courses,
        categories=categories,
        query=query,
        selected_category=category,
    )


@app.get("/course/<course_id>")
@login_required
def course_detail(course_id):
    course = next((course for course in COURSES if course["id"] == course_id), None)
    if course is None:
        abort(404)
    lessons = COURSE_LESSONS[course_id]
    enrolled = course_id in session.get("enrolled_courses", [])
    progress = get_course_progress(course)
    certificate = (
        get_learner_certificate(session["user_name"], course_id)
        if progress["completed"] == progress["total"]
        else None
    )
    return render_template(
        "course_detail.html",
        course=course,
        lessons=lessons,
        enrolled=enrolled,
        progress=progress,
        certificate=certificate,
        help_topics=COURSE_HELP_TOPICS[course_id],
    )


def save_course_lesson_completion(course_id, lesson_number):
    course = next((course for course in COURSES if course["id"] == course_id), None)
    if course is None:
        abort(404)
    lessons = COURSE_LESSONS[course_id]
    if lesson_number < 1 or lesson_number > len(lessons):
        flash("That lesson could not be found.", "error")
        return redirect(url_for("course_detail", course_id=course_id))
    if course_id not in session.get("enrolled_courses", []):
        flash(f"Enroll in {course['title']} to track lesson progress.", "info")
        return redirect(url_for("course_detail", course_id=course_id))
    completed_by_course = session.get("course_completions", {})
    if not isinstance(completed_by_course, dict):
        completed_by_course = {}
    completed = set(get_course_progress(course)["completed_lessons"])
    completed.add(lesson_number)
    completed_by_course[course_id] = sorted(completed)
    session["course_completions"] = completed_by_course
    session.modified = True
    if course_id == SAMPLE_COURSE_ID:
        session["completed_lessons"] = sorted(completed)
    if len(completed) == len(lessons):
        certificate = issue_certificate(session["user_name"], course_id, course["title"])
        flash(
            f'Course complete! Your certificate is ready ({certificate["code"]}).',
            "success",
        )
    else:
        flash(
            "Lesson marked complete. Your progress and points have been updated.",
            "success",
        )
    return redirect(url_for("course_detail", course_id=course_id))


@app.post("/course/<course_id>/lessons/<int:lesson_number>/complete")
@login_required
def complete_course_lesson(course_id, lesson_number):
    return save_course_lesson_completion(course_id, lesson_number)


@app.get("/progress")
@login_required
def progress():
    return render_template(
        "progress.html",
        progress=get_overall_progress(),
        leaderboard=get_leaderboard(),
        certificates=get_completed_course_certificates(),
    )


@app.route("/certificates/verify", methods=["GET", "POST"])
def verify_certificate():
    code = request.values.get("code", "").strip().upper()
    certificate = get_certificate(code) if code else None
    searched = bool(code)
    return render_template(
        "certificate_verify.html",
        code=code,
        certificate=certificate,
        searched=searched,
    )


@app.get("/certificates/<certificate_code>")
def view_certificate(certificate_code):
    code = certificate_code.strip().upper()
    certificate = get_certificate(code)
    if not certificate:
        return render_template(
            "certificate.html", certificate=None, code=code
        ), 404
    return render_template("certificate.html", certificate=certificate, code=code)


@app.get("/my-learning")
@login_required
def my_learning():
    enrolled = get_enrolled_courses()
    return render_template(
        "my_learning.html",
        courses=enrolled,
        course_progress={
            course["id"]: get_course_progress(course) for course in enrolled
        },
    )


@app.post("/enroll/<course_id>")
@login_required
def enroll(course_id):
    if not any(course["id"] == course_id for course in COURSES):
        flash("That course could not be found.", "error")
        return redirect(url_for("courses"))
    enrolled_ids = session.get("enrolled_courses", [])
    if course_id not in enrolled_ids:
        enrolled_ids.append(course_id)
        session["enrolled_courses"] = enrolled_ids
        flash("You’re enrolled. Your course is ready in My learning.", "success")
    else:
        flash("You’re already enrolled in this course.", "info")
    return redirect(safe_referrer("my_learning"))


@app.post("/unenroll/<course_id>")
@login_required
def unenroll(course_id):
    enrolled_ids = session.get("enrolled_courses", [])
    session["enrolled_courses"] = [
        enrolled_id for enrolled_id in enrolled_ids if enrolled_id != course_id
    ]
    flash("Course removed from My learning.", "info")
    return redirect(url_for("my_learning"))


@app.post("/api/course-help/<course_id>")
@login_required
def course_help(course_id):
    course = next((course for course in COURSES if course["id"] == course_id), None)
    if course is None:
        return jsonify(error="That course could not be found."), 404
    if course_id not in session.get("enrolled_courses", []):
        return jsonify(error=f"Enroll in {course['title']} to use its course assistant."), 403
    payload = request.get_json(silent=True)
    question = payload.get("question", "").strip() if isinstance(payload, dict) else ""
    if not question:
        return jsonify(error=f"Type a question about {course['title']} first."), 400
    if len(question) > 500:
        return jsonify(error="Please keep your question under 500 characters."), 400

    text = question.casefold()
    topics = COURSE_HELP_TOPICS[course_id]
    best_topic = max(
        topics,
        key=lambda topic: sum(
            len(keyword) for keyword in topic["keywords"] if keyword in text
        ),
    )
    match_score = sum(
        len(keyword) for keyword in best_topic["keywords"] if keyword in text
    )
    if match_score:
        answer = best_topic["answer"]
    else:
        available_topics = ", ".join(
            topic["question"].rstrip("?") for topic in topics
        )
        answer = (
            f"I can help with {course['title']} topics such as {available_topics}. "
            "Choose a suggested question or ask about one of those subjects."
        )
    return jsonify(answer=answer, source=f"{course['title']} course guide")


@app.route("/login", methods=["GET", "POST"])
def login():
    next_url = safe_next_url(request.values.get("next"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Enter your name to continue.", "error")
        else:
            session["user_name"] = name
            flash(f"Welcome, {name}!", "success")
            return redirect(next_url)
    elif session.get("user_name"):
        return redirect(next_url)
    return render_template("login.html", next_url=next_url)


@app.post("/logout")
def logout():
    session.pop("user_name", None)
    flash("You’ve been signed out.", "info")
    return redirect(url_for("home"))


initialize_certificate_store()


if __name__ == "__main__":
    app.run(port=5053, debug=os.environ.get("FLASK_DEBUG") == "1")
