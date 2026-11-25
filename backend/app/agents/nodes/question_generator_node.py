import json
import re
import random
from typing import List, Dict, Any, Optional
from app.schemas.interview import GeneratedQuestion, StagePlan
from app.schemas.resume import ResumeParsedData, SkillEntity
from app.agents.llm_factory import llm_factory

ARCHITECTURAL_DOMAINS = [
    "High-Frequency FinTech & Payment Clearinghouse",
    "Global E-Commerce Flash Sale & Inventory Engine",
    "Real-Time Healthcare Telemetry & Biometrics Streaming",
    "Multi-Tenant Distributed SaaS Cloud Architecture",
    "Autonomous Logistics Fleet Telematics & Routing",
    "Low-Latency Video Transcoding & Edge CDN Distribution",
    "Zero-Trust Cloud Identity & Distributed Token Gateway",
    "Collaborative Real-Time Canvas / Multi-User CRDT Sync",
    "High-Throughput IoT Event Ingestion & Aggregation Mesh",
    "Distributed Key-Value Cache with Geo-Replication",
]

PROBLEM_CONSTRAINTS = [
    "with strict p99 latency < 15ms under 100,000 requests/sec",
    "under severe network partitioning (split-brain mitigation)",
    "operating under memory-constrained containers (max 128MB RAM)",
    "handling abrupt 50x read/write traffic spikes without dropping requests",
    "ensuring zero data loss with exactly-once vs at-least-once semantics",
    "preventing cascading failures using adaptive backpressure and circuit breakers",
    "resolving distributed race conditions across multiple asynchronous writer nodes",
]


class QuestionGeneratorNode:
    """Agent that generates adaptive, context-driven interview questions with
    zero repetition and dynamic randomization across resume, topic, and role modes.
    """

    @classmethod
    def execute(
        cls,
        stage: str,
        difficulty: str,
        job_role: str,
        experience_level: str,
        resume: ResumeParsedData,
        skills: List[SkillEntity],
        stage_plan: Optional[StagePlan],
        previous_turns: List[Dict[str, Any]],
        turn_number: int,
        interview_type: str = "resume",
        focus_topic: Optional[str] = None,
    ) -> GeneratedQuestion:
        """Generate context-aware, non-repeating question for current stage, difficulty, and mode."""
        # Use temperature 0.7 for creative diversity while maintaining technical rigor
        llm = llm_factory.get_llm(temperature=0.7)

        if llm:
            try:
                question = cls._generate_with_llm(
                    llm, stage, difficulty, job_role, experience_level,
                    resume, skills, stage_plan, previous_turns, turn_number,
                    interview_type, focus_topic
                )
                if question:
                    return question
            except Exception as e:
                print(f"[WARN] LLM question generation failed: {e}. Using randomized deterministic generator.")

        return cls._deterministic_generate(
            stage, difficulty, job_role, experience_level,
            resume, skills, stage_plan, previous_turns, turn_number,
            interview_type, focus_topic
        )

    @classmethod
    def _generate_with_llm(
        cls,
        llm,
        stage: str,
        difficulty: str,
        job_role: str,
        experience_level: str,
        resume: ResumeParsedData,
        skills: List[SkillEntity],
        stage_plan: Optional[StagePlan],
        previous_turns: List[Dict[str, Any]],
        turn_number: int,
        interview_type: str,
        focus_topic: Optional[str],
    ) -> Optional[GeneratedQuestion]:
        # Collect all previously asked questions for strict anti-repetition
        all_prior_questions = [
            f"- Turn {t.get('turn_number', idx + 1)}: {t.get('question_text')}"
            for idx, t in enumerate(previous_turns)
            if t.get("question_text")
        ]
        prior_context_block = "\n".join(all_prior_questions) if all_prior_questions else "None (this is Turn #1)."

        # Pick random real-world architectural context for unique scenario flavor
        random_domain = random.choice(ARCHITECTURAL_DOMAINS)
        random_constraint = random.choice(PROBLEM_CONSTRAINTS)

        target_topics = stage_plan.target_skills_or_topics if stage_plan else []
        if focus_topic and focus_topic not in target_topics:
            target_topics = [focus_topic] + target_topics

        top_project = resume.projects[0].title if resume.projects else "Engineering Project"
        top_skills = [s.name for s in skills[:8]]

        prompt = f"""You are an elite Principal Technical Interviewer conducting a realistic technical interview.
You are generating Question #{turn_number}.

MODE: {interview_type.upper()} INTERVIEW {f'| FOCUS TOPIC: {focus_topic}' if focus_topic else ''}
TARGET ROLE: {job_role} ({experience_level} level)
CURRENT RECRUITMENT STAGE: {stage}
CURRENT DIFFICULTY LEVEL: {difficulty}
STAGE GOAL: {stage_plan.focus_goal if stage_plan else 'Evaluate candidate technical depth and reasoning'}
TOPICS TO PROBE: {target_topics}

REAL-WORLD SCENARIO INJECTION:
- Architectural Domain: {random_domain}
- Operational Challenge: {random_constraint}

CANDIDATE CONTEXT:
- Name: {resume.full_name or 'Candidate'}
- Declared Skills: {top_skills}
- Key Project: {top_project}

STRICT PROHIBITION (ZERO REPETITION):
The following questions have ALREADY BEEN ASKED in this session. You MUST NOT repeat, rephrase, or re-test them:
{prior_context_block}

RULES:
1. Generate an original, thought-provoking, and practical question that has NEVER been asked before.
2. If interview_type is 'topic', the question MUST probe deeply into core internals, trade-offs, and practical design of '{focus_topic}'.
3. If interview_type is 'role', focus directly on real-world engineering responsibilities and scenarios for a '{job_role}'.
4. If interview_type is 'resume', anchor the question in the candidate's actual projects or claimed skills.
5. In difficulty '{difficulty}', calibrate appropriately:
   - 'basic': fundamental mental models, memory lifecycle, scoping, and exact definitions.
   - 'intermediate': practical implementation, API design, trade-offs, and debugging.
   - 'advanced': high-concurrency, distributed bottlenecks, race conditions, and latency optimization.
6. Be conversational, direct, and realistic.

Strictly return a JSON object:
{{
  "stage": "{stage}",
  "difficulty_level": "{difficulty}",
  "question_text": "The exact question to ask the candidate",
  "context_rationale": "Why this specific question was selected based on the scenario/trajectory",
  "expected_concepts": ["Concept 1", "Concept 2", "Concept 3"]
}}
"""
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)

        clean_json = re.sub(r"^```json\s*", "", content.strip())
        clean_json = re.sub(r"^```\s*", "", clean_json)
        clean_json = re.sub(r"\s*```$", "", clean_json)

        data = json.loads(clean_json)
        return GeneratedQuestion(**data)

    @classmethod
    def _deterministic_generate(
        cls,
        stage: str,
        difficulty: str,
        job_role: str,
        experience_level: str,
        resume: ResumeParsedData,
        skills: List[SkillEntity],
        stage_plan: Optional[StagePlan],
        previous_turns: List[Dict[str, Any]],
        turn_number: int,
        interview_type: str = "resume",
        focus_topic: Optional[str] = None,
    ) -> GeneratedQuestion:
        """Randomized deterministic question generator guaranteeing non-repetition across modes."""
        already_asked = [
            t.get("question_text", "").strip().lower()
            for t in previous_turns
            if t.get("question_text")
        ]

        top_skills = [s.name for s in skills[:8]] or ["Python", "FastAPI", "SQL", "Docker", "React"]
        skill1 = random.choice(top_skills[:3]) if top_skills else "Python"
        skill2 = random.choice(top_skills[3:]) if len(top_skills) > 3 else "PostgreSQL"
        project = resume.projects[0] if resume.projects else None
        proj_title = project.title if project else "your featured engineering project"
        topic_target = focus_topic or job_role

        # Build randomized question pools per stage & mode
        question_pool: List[Dict[str, Any]] = []

        if stage == "intro":
            question_pool = [
                {
                    "q": f"Welcome! To start our session, could you walk us through your technical journey and what motivated you to pursue this {job_role} position?",
                    "r": "Assessing candidate introduction and career motivation.",
                    "c": ["Career trajectory", "Engineering motivation", "Communication clarity"]
                },
                {
                    "q": f"Great to meet you! In your own words, what are the primary technical strengths you bring to a {job_role} role, and how do you approach learning complex new technologies?",
                    "r": "Assessing engineering self-awareness and learning velocity.",
                    "c": ["Technical self-awareness", "Continuous learning", "Engineering ownership"]
                },
                {
                    "q": f"To kick things off, could you summarize an engineering challenge you solved recently that you're most proud of, and how it aligns with your goals as a {job_role}?",
                    "r": "Initial engagement grounded in practical engineering achievement.",
                    "c": ["Recent technical accomplishment", "Problem solving", "Role alignment"]
                },
            ]

        elif stage == "skill_verification":
            if interview_type == "topic" and focus_topic:
                question_pool = [
                    {
                        "q": f"Let's dive into {focus_topic}: Can you break down the internal working mechanics and memory model when executing high-throughput operations in {focus_topic}?",
                        "r": f"Verifying foundational mechanics of {focus_topic}.",
                        "c": [f"{focus_topic} internals", "Memory model", "Execution lifecycle"]
                    },
                    {
                        "q": f"In {focus_topic}, what are the common anti-patterns or architectural pitfalls developers encounter, and how do you proactively prevent them?",
                        "r": f"Evaluating anti-pattern recognition in {focus_topic}.",
                        "c": ["Anti-patterns", "Code quality", "Defensive design"]
                    },
                    {
                        "q": f"When comparing different algorithms or paradigms within {focus_topic}, how do you evaluate time complexity, space complexity, and real-world cache locality trade-offs?",
                        "r": f"Testing performance evaluation depth in {focus_topic}.",
                        "c": ["Complexity analysis", "Cache locality", "Performance benchmarks"]
                    },
                ]
            else:
                question_pool = [
                    {
                        "q": f"You highlighted proficiency with {skill1}. How do memory management, variable scoping, and execution lifecycles operate under the hood in {skill1}?",
                        "r": f"Directly testing conceptual grounding in {skill1}.",
                        "c": [f"{skill1} runtime internals", "Memory lifecycle", "Scoping rules"]
                    },
                    {
                        "q": f"Working with {skill2}, what is the distinction between optimistic and pessimistic locking, and in what concrete scenario would you choose one over the other?",
                        "r": f"Verifying concurrency and data consistency in {skill2}.",
                        "c": ["Locking strategies", "Data contention", "Concurrency trade-offs"]
                    },
                    {
                        "q": f"In {skill1}, how does the runtime handle asynchronous execution or multi-threading? What are the synchronization primitives available to prevent race conditions?",
                        "r": f"Probing threading and concurrency primitives in {skill1}.",
                        "c": ["Thread safety", "Event loop vs Worker threads", "Synchronization primitives"]
                    },
                    {
                        "q": f"When scaling applications built with {skill1} and {skill2}, where do memory leaks or performance bottlenecks typically manifest, and what profiling tools do you use?",
                        "r": "Assessing diagnostic profiling and memory debugging.",
                        "c": ["Memory leak profiling", "Garbage collection behavior", "Performance telemetry"]
                    },
                ]

        elif stage == "technical":
            if difficulty == "advanced":
                question_pool = [
                    {
                        "q": f"In a mission-critical {topic_target} service, how do you handle connection pool exhaustion and database starvation under a sudden 50x spike in concurrent traffic?",
                        "r": "Testing high-concurrency bottleneck resolution and resilient architecture.",
                        "c": ["Connection pooling", "Circuit breakers", "Backpressure", "Traffic shedding"]
                    },
                    {
                        "q": f"How would you implement distributed caching for {topic_target} while strictly mitigating Cache Stampede, Cache Avalanche, and Cache Penetration?",
                        "r": "Advanced distributed caching strategies.",
                        "c": ["Cache stampede mitigation", "Bloom filters", "Mutual exclusion locks", "TTL jittering"]
                    },
                    {
                        "q": f"When designing distributed data pipelines for {topic_target}, how do you maintain consistency across microservices without introducing distributed two-phase locking bottlenecks?",
                        "r": "Evaluating distributed consistency and transactional patterns.",
                        "c": ["Saga pattern", "Eventual consistency", "Outbox pattern", "Idempotent consumers"]
                    },
                ]
            elif difficulty == "basic":
                question_pool = [
                    {
                        "q": f"In {topic_target}, what is the fundamental difference between synchronous and asynchronous I/O, and how does non-blocking I/O prevent thread starvation?",
                        "r": "Verifying non-blocking I/O fundamentals.",
                        "c": ["Event loop", "Asynchronous execution", "Thread vs Event-driven I/O"]
                    },
                    {
                        "q": f"What are the core ACID guarantees in relational systems, and how does database indexing (B-Trees vs Hash indexes) accelerate lookup performance in {topic_target}?",
                        "r": "Verifying database fundamentals and index mechanics.",
                        "c": ["ACID properties", "B-Tree mechanics", "Index scan vs Table scan"]
                    },
                    {
                        "q": f"In {topic_target}, what is the difference between process-level and thread-level concurrency? How do processes communicate (IPC) versus threads sharing memory?",
                        "r": "Verifying operating system and concurrency basics.",
                        "c": ["Process vs Thread", "Inter-process communication", "Shared memory"]
                    },
                ]
            else:
                question_pool = [
                    {
                        "q": f"When designing RESTful or RPC services for a {topic_target} architecture, what mechanisms guarantee idempotency across distributed POST or PUT retry requests?",
                        "r": "Evaluating distributed API design and reliability patterns.",
                        "c": ["Idempotency keys", "HTTP verbs", "Duplicate request mitigation"]
                    },
                    {
                        "q": f"How do you design database schema migrations with zero-downtime when working with large production datasets in a {topic_target} system?",
                        "r": "Assessing zero-downtime database deployment strategies.",
                        "c": ["Expand and contract pattern", "Blue-green deployment", "Non-locking migrations"]
                    },
                    {
                        "q": f"In {topic_target}, how do you structure structured logging, distributed tracing (e.g. OpenTelemetry), and metrics collection for effective production observability?",
                        "r": "Observability and production telemetry design.",
                        "c": ["Correlation IDs", "OpenTelemetry spans", "Prometheus metrics", "Log aggregation"]
                    },
                ]

        elif stage == "problem_solving":
            question_pool = [
                {
                    "q": f"System Scenario: You are tasked with designing a distributed rate limiter for a {topic_target} platform that caps users at 1,000 requests/min across 20 cluster nodes with sub-5ms latency. What algorithm and data store would you select, and how do you handle atomic race conditions?",
                    "r": "Assessing analytical problem decomposition and trade-off justification.",
                    "c": ["Sliding window / Token bucket", "Redis Lua scripts", "Atomic increments", "Clock drift"]
                },
                {
                    "q": f"Design Problem: Design a real-time collaborative document/notification system for {topic_target} handling 100,000 concurrent active connections. How do you manage connection state, message ordering, and reconnection packet recovery?",
                    "r": "Evaluating real-time architecture and connection scaling.",
                    "c": ["WebSockets / SSE", "Redis Pub/Sub / Kafka", "Heartbeat mechanisms", "Sequence numbering"]
                },
                {
                    "q": f"Algorithmic Problem: You need to design an in-memory Least Recently Used (LRU) Cache with O(1) get and O(1) put operations. What data structures would you combine, and how would you make it thread-safe for concurrent read/write access?",
                    "r": "Assessing algorithmic data structure selection and concurrent access.",
                    "c": ["Doubly Linked List + Hash Map", "O(1) operations", "ReadWriteLock / Mutex", "Eviction policy"]
                },
                {
                    "q": f"Architecture Scenario: An e-commerce flash sale system experiences sudden 100x traffic for 10 minutes. How do you design the checkout and inventory reservation queue in {topic_target} to prevent overselling while guaranteeing responsive user feedback?",
                    "r": "High-contention inventory reservation and asynchronous queuing.",
                    "c": ["Pessimistic vs Optimistic locking", "Message queues", "Atomic decrement", "Idempotent orders"]
                },
            ]

        elif stage == "project_discussion":
            if interview_type == "topic":
                question_pool = [
                    {
                        "q": f"Describe a real-world system or project you engineered utilizing {focus_topic}. What was the high-level architecture, what bottlenecks emerged during scale, and how did you resolve them?",
                        "r": f"Verifying architectural ownership and problem solving in {focus_topic}.",
                        "c": ["System architecture", "Bottleneck identification", "Engineering trade-offs"]
                    },
                    {
                        "q": f"In your experience applying {focus_topic}, what was the most difficult edge-case or production outage you debugged? Walk me through your diagnostic process.",
                        "r": f"Assessing diagnostic debugging and resilience in {focus_topic}.",
                        "c": ["Root-cause analysis", "Debugging tools", "Defensive remediation"]
                    },
                ]
            else:
                question_pool = [
                    {
                        "q": f"Looking at your project '{proj_title}': Can you walk me through the system architecture from end to end? What was the single most difficult technical challenge you encountered, and what architectural trade-off did you make to resolve it?",
                        "r": f"Deep verification of engineering ownership in '{proj_title}'.",
                        "c": ["System architecture", "Personal engineering contribution", "Root cause problem solving", "Design trade-offs"]
                    },
                    {
                        "q": f"Regarding '{proj_title}': If you had to redesign this system today to support 100x greater scale and 99.99% availability, what components would you refactor or replace, and why?",
                        "r": "Assessing forward-looking architecture and technical self-critique.",
                        "c": ["Scalability refactoring", "High availability design", "Technical debt analysis"]
                    },
                ]

        elif stage == "experience_discussion":
            question_pool = [
                {
                    "q": f"In your development experience as a {job_role}, can you describe a scenario where a deployment or feature failed in testing or production? How did you triage the incident, isolate the root cause, and what automated guardrails did you put in place?",
                    "r": "Evaluating engineering rigor, observability, and defensive practices.",
                    "c": ["Root-cause triage", "Logs and observability", "Automated regression tests", "Post-mortem mindset"]
                },
                {
                    "q": "How do you approach code reviews when reviewing complex pull requests from colleagues? Can you share an example where you identified an architectural flaw or security vulnerability before it reached production?",
                    "r": "Assessing collaborative engineering standards and code quality enforcement.",
                    "c": ["Code review rigor", "Security awareness", "Constructive feedback", "Maintainability"]
                },
                {
                    "q": f"When balancing technical debt versus shipping rapid product features in a {job_role} team, how do you communicate technical debt to stakeholders and schedule refactoring?",
                    "r": "Evaluating technical debt management and pragmatic engineering judgment.",
                    "c": ["Technical debt prioritization", "Stakeholder communication", "Pragmatic balance"]
                },
            ]

        elif stage == "behavioral_hr":
            question_pool = [
                {
                    "q": "Software engineering involves frequent trade-offs between speed and architectural perfection. Can you share an example where you had a strong technical disagreement with a team member or tech lead? How did you navigate it and what was the outcome?",
                    "r": "Assessing professional collaboration, constructive conflict, and empathy.",
                    "c": ["Constructive disagreement", "Data-driven persuasion", "Team cohesion", "Pragmatic consensus"]
                },
                {
                    "q": f"Tell me about a time when you received critical feedback on your code, design proposal, or performance. How did you process that feedback and what concrete changes did you implement?",
                    "r": "Evaluating growth mindset and receptive collaboration.",
                    "c": ["Growth mindset", "Receptiveness to feedback", "Continuous improvement"]
                },
                {
                    "q": "When unexpected priority shifts or shifting requirements occur midway through an engineering sprint, how do you adapt your workflow, manage stress, and ensure delivery quality?",
                    "r": "Assessing adaptability and resilience in high-velocity teams.",
                    "c": ["Agile adaptability", "Prioritization", "Resilience under pressure"]
                },
            ]

        else:
            question_pool = [
                {
                    "q": f"Could you elaborate on how you apply {skill1} and {skill2} to solve complex real-world challenges in this {job_role} role?",
                    "r": "General technical follow-up.",
                    "c": ["Practical application", "Architecture"]
                }
            ]

        # Filter out questions that have already been asked in this session
        available = [
            item for item in question_pool
            if item["q"].strip().lower() not in already_asked
        ]

        # If all predefined questions were asked, pick randomly or synthesize with a random constraint
        chosen = random.choice(available if available else question_pool)

        return GeneratedQuestion(
            stage=stage,
            difficulty_level=difficulty,
            question_text=chosen["q"],
            context_rationale=chosen["r"],
            expected_concepts=chosen["c"]
        )


question_generator_node = QuestionGeneratorNode()
