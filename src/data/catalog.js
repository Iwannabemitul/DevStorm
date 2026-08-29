/**
 * Static reference data for the SkillGap Intelligence app.
 *
 * This module intentionally contains ONLY data (no logic, no I/O) so it can
 * be imported safely from any layer -- services, routes -- without pulling
 * in side effects. Direct port of the original data/catalog.py.
 */

const JOB_DATA = {
  job_roles: {
    // --- Core Software Engineering ---
    "Software Engineer": {
      required_skills: ["Data Structures & Algorithms", "Python/Java/C++", "Git & Version Control", "System Design", "Debugging & Testing", "Object-Oriented Design", "Code Review Practices", "Unit Testing"],
      experience_level: "Entry to Senior",
    },
    "Full Stack Developer": {
      required_skills: ["JavaScript", "React", "Node.js", "SQL", "REST APIs", "Git & Version Control", "System Design", "CI/CD Pipelines"],
      experience_level: "Entry to Senior",
    },
    "Backend Developer": {
      required_skills: ["Python/Java/Node.js", "SQL & NoSQL Databases", "REST APIs", "Microservices", "System Design", "Docker", "Git & Version Control", "Debugging & Testing"],
      experience_level: "Entry to Senior",
    },
    "Frontend Developer": {
      required_skills: ["HTML", "CSS", "JavaScript", "React/Vue.js/Angular", "Responsive Design", "Web Accessibility", "Git & Version Control", "Browser DevTools"],
      experience_level: "Entry to Senior",
    },

    // --- Data ---
    "Data Scientist": {
      required_skills: ["Python/R", "Statistics & Probability", "Machine Learning", "SQL", "Data Visualization", "Pandas", "Data Cleaning & Wrangling", "Experiment Design"],
      experience_level: "Mid to Senior",
    },
    "Data Engineer": {
      required_skills: ["Python/Scala", "SQL", "ETL Pipelines", "Apache Spark", "Data Warehousing", "Airflow", "Cloud Platforms (AWS/Azure/GCP)", "Data Modeling"],
      experience_level: "Mid to Senior",
    },
    "Data Analyst": {
      required_skills: ["SQL", "Excel", "Data Visualization", "Statistics & Probability", "Python/R", "Business Intelligence Tools", "Dashboarding", "Data Cleaning & Wrangling"],
      experience_level: "Entry to Mid",
    },

    // --- AI / Machine Learning ---
    "AI Engineer": {
      required_skills: ["Python", "Machine Learning", "Deep Learning", "TensorFlow/PyTorch", "Model Deployment", "MLOps", "Prompt Engineering", "Cloud Platforms (AWS/Azure/GCP)"],
      experience_level: "Mid to Senior",
    },
    "Machine Learning Engineer": {
      required_skills: ["Python", "TensorFlow/PyTorch", "Feature Engineering", "Model Training & Tuning", "MLOps", "Distributed Computing", "SQL", "Statistics & Probability"],
      experience_level: "Mid to Senior",
    },
    "MLOps Engineer": {
      required_skills: ["CI/CD Pipelines", "Docker & Kubernetes", "Model Monitoring", "Cloud Platforms (AWS/Azure/GCP)", "Python", "MLflow/Kubeflow", "Infrastructure as Code (Terraform)", "Version Control for ML (DVC)"],
      experience_level: "Mid to Senior",
    },
    "NLP Engineer": {
      required_skills: ["Python", "Transformers", "Natural Language Processing", "Tokenization & Embeddings", "PyTorch/TensorFlow", "Large Language Models", "Text Preprocessing", "Model Fine-Tuning"],
      experience_level: "Mid to Senior",
    },
    "Computer Vision Engineer": {
      required_skills: ["Python", "OpenCV", "Deep Learning", "Convolutional Neural Networks", "Image Processing", "PyTorch/TensorFlow", "Object Detection", "Model Optimization"],
      experience_level: "Mid to Senior",
    },
    "Robotics Engineer": {
      required_skills: ["C++/Python", "ROS (Robot Operating System)", "Control Systems", "Sensor Fusion", "Kinematics", "Embedded Systems", "Path Planning", "Computer Vision"],
      experience_level: "Mid to Senior",
    },

    // --- Hardware & Systems ---
    "Embedded Systems Engineer": {
      required_skills: ["C/C++", "Microcontrollers (ARM/AVR)", "RTOS", "Sensor Integration", "Circuit Debugging", "UART/SPI/I2C Protocols", "Firmware Development", "Low-Power Design"],
      experience_level: "Mid to Senior",
    },
    "IoT Architect": {
      required_skills: ["MQTT/CoAP Protocols", "Embedded Systems", "Cloud Platforms (AWS/Azure/GCP)", "Edge Computing", "Sensor Networks", "Network Security", "System Design", "Device Provisioning"],
      experience_level: "Mid to Senior",
    },
    "Firmware Engineer": {
      required_skills: ["C/C++", "Microcontrollers (ARM/AVR)", "Bootloader Development", "Debugging Tools (JTAG)", "RTOS", "Hardware Datasheets", "Version Control", "Power Management"],
      experience_level: "Mid to Senior",
    },
    "Hardware Design Engineer": {
      required_skills: ["Circuit Design", "PCB Layout", "VHDL/Verilog", "Signal Integrity", "Schematic Capture Tools", "Embedded Systems", "Testing & Validation", "Datasheet Analysis"],
      experience_level: "Mid to Senior",
    },
    "Systems Optimization Engineer": {
      required_skills: ["C/C++", "Operating Systems Internals", "Performance Profiling", "Memory Management", "Concurrency & Multithreading", "Linux Administration", "Debugging Tools", "Benchmarking"],
      experience_level: "Mid to Senior",
    },

    // --- Mobile ---
    "Android Developer": {
      required_skills: ["Kotlin/Java", "Android SDK", "Jetpack Compose", "REST APIs", "SQLite/Room", "Git & Version Control", "Material Design", "App Performance Optimization"],
      experience_level: "Entry to Senior",
    },
    "iOS Developer": {
      required_skills: ["Swift", "UIKit/SwiftUI", "Xcode", "REST APIs", "Core Data", "Git & Version Control", "App Store Guidelines", "Memory Management"],
      experience_level: "Entry to Senior",
    },

    // --- Game Development ---
    "Game Developer": {
      required_skills: ["C++/C#", "Unity/Unreal Engine", "Game Physics", "3D Math", "Shader Programming", "Version Control (Git/Perforce)", "Performance Optimization", "Multiplayer Networking"],
      experience_level: "Entry to Senior",
    },
    "Game Designer": {
      required_skills: ["Game Design Documentation", "Level Design", "Prototyping Tools", "Player Psychology", "Balancing & Economy Design", "Scripting (C#/Lua)", "Playtesting", "Storytelling"],
      experience_level: "Entry to Mid",
    },

    // --- Cloud & Infrastructure ---
    "Cloud Architect": {
      required_skills: ["AWS/Azure/GCP", "Infrastructure as Code (Terraform)", "Networking Fundamentals", "Cloud Security", "Cost Optimization", "Kubernetes", "Disaster Recovery Planning", "System Design"],
      experience_level: "Mid to Senior",
    },
    "DevOps Engineer": {
      required_skills: ["CI/CD Pipelines", "Docker & Kubernetes", "Cloud Platforms (AWS/Azure/GCP)", "Infrastructure as Code (Terraform)", "Linux Administration", "Monitoring & Logging", "Scripting (Python/Bash)", "Configuration Management (Ansible)"],
      experience_level: "Mid to Senior",
    },
    "Site Reliability Engineer": {
      required_skills: ["Linux Administration", "Monitoring & Alerting (Prometheus/Grafana)", "Incident Response", "CI/CD Pipelines", "Kubernetes", "Scripting (Python/Bash)", "Capacity Planning", "System Design"],
      experience_level: "Mid to Senior",
    },

    // --- Cybersecurity ---
    "Cybersecurity Analyst": {
      required_skills: ["Network Security", "Threat Detection & Response", "Penetration Testing", "SIEM Tools", "Risk Assessment", "Incident Response", "Security Policies & Compliance", "Vulnerability Management"],
      experience_level: "Entry to Senior",
    },
    "Penetration Tester": {
      required_skills: ["Network Security", "Penetration Testing", "Vulnerability Assessment", "Exploit Development", "Scripting (Python/Bash)", "Web Application Security", "Social Engineering Awareness", "Reporting & Documentation"],
      experience_level: "Mid to Senior",
    },
    "Security Engineer": {
      required_skills: ["Network Security", "Cloud Security", "SIEM Tools", "Identity & Access Management", "Threat Modeling", "Incident Response", "Encryption & Cryptography", "Risk Assessment"],
      experience_level: "Mid to Senior",
    },

    // --- Web3 / Blockchain ---
    "Blockchain Developer": {
      required_skills: ["Solidity", "Smart Contract Development", "Ethereum/EVM", "Web3.js/Ethers.js", "Cryptography Fundamentals", "Consensus Mechanisms", "Gas Optimization", "Security Auditing"],
      experience_level: "Mid to Senior",
    },
    "Web3 Engineer": {
      required_skills: ["Solidity", "Smart Contracts", "Decentralized Applications (dApps)", "IPFS", "Wallet Integration (MetaMask)", "Web3.js/Ethers.js", "Layer 2 Solutions", "Tokenomics"],
      experience_level: "Mid to Senior",
    },

    // --- Databases ---
    "Database Administrator": {
      required_skills: ["SQL & NoSQL Databases", "Query Optimization", "Backup & Recovery", "Database Security", "Performance Tuning", "High Availability & Clustering", "Database Monitoring", "Capacity Planning"],
      experience_level: "Mid to Senior",
    },
    "Database Engineer": {
      required_skills: ["SQL & NoSQL Databases", "Database Design & Normalization", "Indexing Strategies", "Replication & Sharding", "Query Optimization", "Backup & Recovery", "Cloud Databases", "Data Migration"],
      experience_level: "Mid to Senior",
    },

    // --- QA ---
    "QA Automation Engineer": {
      required_skills: ["Selenium/Playwright", "Test Case Design", "CI/CD Pipelines", "API Testing", "Scripting (Python/JavaScript)", "Bug Tracking Tools", "Performance Testing", "Test Strategy"],
      experience_level: "Entry to Mid",
    },

    // --- Product & Program Management ---
    "Product Manager": {
      required_skills: ["Roadmap Planning", "Stakeholder Communication", "Market Research", "Agile/Scrum", "Data-Driven Decision Making", "Competitive Analysis", "User Story Writing", "Go-to-Market Strategy"],
      experience_level: "Mid to Senior",
    },
    "Technical Program Manager": {
      required_skills: ["Roadmap Planning", "Cross-Functional Coordination", "Risk Management", "Agile/Scrum", "Stakeholder Communication", "Resource Allocation", "Technical Fluency", "Program Metrics & Reporting"],
      experience_level: "Mid to Senior",
    },

    // --- Design ---
    "UX/UI Designer": {
      required_skills: ["Wireframing & Prototyping", "Figma/Sketch/Adobe XD", "User Research", "Interaction Design", "Visual Design Principles", "Usability Testing", "Design Systems", "Accessibility Standards (WCAG)"],
      experience_level: "Entry to Senior",
    },

    // --- Marketing ---
    "Digital Marketing Specialist": {
      required_skills: ["SEO/SEM", "Content Strategy", "Social Media Marketing", "Google Analytics", "Email Marketing Campaigns", "Paid Advertising (PPC)", "Conversion Rate Optimization", "Marketing Automation Tools"],
      experience_level: "Entry to Mid",
    },
  },
};

const ALL_TECH_SKILLS = [
  "Python", "Java", "C++", "C#", "Go", "Rust", "JavaScript", "TypeScript",
  "HTML", "CSS", "React", "Vue.js", "Angular", "Node.js", "Next.js",
  "Django", "Flask", "FastAPI", "Spring Boot", "Ruby", "Ruby on Rails",
  "PHP", "Swift", "Kotlin", "R",
  "SQL", "MySQL", "PostgreSQL", "MongoDB", "Redis", "SQLite",
  "SQL & NoSQL Databases", "Query Optimization", "Database Security",
  "Backup & Recovery", "Performance Tuning",
  "AWS", "Azure", "Google Cloud Platform", "Cloud Platforms (AWS/Azure/GCP)",
  "Docker", "Kubernetes", "Docker & Kubernetes", "Terraform",
  "Infrastructure as Code (Terraform)", "CI/CD Pipelines", "Jenkins",
  "Linux Administration", "Git & Version Control", "GitHub Actions",
  "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch",
  "Scikit-learn", "Natural Language Processing", "Computer Vision",
  "Data Visualization", "Statistics & Probability", "Pandas", "NumPy",
  "Data Structures & Algorithms", "System Design", "Debugging & Testing",
  "Cybersecurity", "Network Security", "Penetration Testing",
  "Threat Detection & Response", "SIEM Tools", "Risk Assessment",
  "Figma", "Sketch", "Adobe XD", "Wireframing & Prototyping",
  "User Research", "Interaction Design", "Visual Design Principles",
  "Agile", "Scrum", "Roadmap Planning", "Stakeholder Communication",
  "Market Research", "Data-Driven Decision Making",
  "SEO/SEM", "Content Strategy", "Social Media Marketing",
  "Google Analytics", "Email Marketing Campaigns",
  "GraphQL", "REST APIs", "Microservices", "Kafka", "RabbitMQ",
].sort((a, b) => a.localeCompare(b));

const PROFICIENCY_OPTIONS = ["Beginner (0.4)", "Intermediate (0.8)", "Advanced (1.0)"];
const PROFICIENCY_WEIGHTS = {
  "Beginner (0.4)": 0.4,
  "Intermediate (0.8)": 0.8,
  "Advanced (1.0)": 1.0,
};

const FUN_FACTS = [
  "🧠 The term 'bug' in computing traces back to an actual moth found in a Harvard Mark II relay in 1947.",
  "🐍 Python was named after Monty Python's Flying Circus, not the snake.",
  "🖱️ The first computer mouse prototype was carved out of wood.",
  "⌨️ QWERTY was originally designed to slow typists down and stop mechanical typewriters from jamming.",
  "🏦 More than 70% of the world's financial transactions still run on COBOL, a language from 1959.",
  "⚡ JavaScript was originally written in just 10 days by Brendan Eich in 1995.",
  "🚀 The Apollo 11 guidance computer had less RAM than a modern USB-C cable.",
  "🔍 A single Google search reportedly draws more computing power than the entire Apollo 11 mission.",
  "📷 The world's first webcam was built just to monitor a coffee pot at Cambridge University.",
  "💾 The first 1GB hard drive, released in 1980, weighed about 550 pounds and cost $40,000.",
  "🌐 The World Wide Web was originally proposed as a way to help physicists share documents at CERN.",
  "🐛 Grace Hopper coined the term 'debugging' after physically removing that moth from a relay.",
  "📧 The first email was sent in 1971, and its author doesn't remember exactly what it said.",
  "🎮 The 'Konami Code' cheat sequence became so famous it's now used as an easter egg in web browsers.",
  "🧮 The first computer 'programmer' is widely considered to be Ada Lovelace, in the 1840s.",
  "📱 There are more mobile phones on Earth today than there are people.",
  "🔤 The @ symbol was chosen for email addresses in 1971 simply because it was rarely used elsewhere.",
  "🖥️ The original name for the Windows operating system was 'Interface Manager'.",
  "🕹️ 'Space Invaders' was so popular in Japan it reportedly caused a national coin shortage.",
  "🔐 The first computer password was created at MIT in the 1960s — and was reportedly leaked within weeks.",
];

module.exports = {
  JOB_DATA,
  ALL_TECH_SKILLS,
  PROFICIENCY_OPTIONS,
  PROFICIENCY_WEIGHTS,
  FUN_FACTS,
};
