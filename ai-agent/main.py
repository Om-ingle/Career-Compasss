
import os
import json
import httpx
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
from typing import Optional, Dict, Any

# Load environment variables from .env file
load_dotenv()

# Offline mode support
OFFLINE_MODE = os.getenv('OFFLINE_MODE', '').lower() in ('1', 'true', 'yes', 'on')

# Gemini model configuration
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')

# Configure Gemini API (only if available). If not set, fall back to offline mode.
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    OFFLINE_MODE = True

app = FastAPI(title="CareerCompass AI Agent", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalysisRequest(BaseModel):
    userId: str
    mockDataApiUrl: str = "http://mock-data-api:8080"

class CareerRecommendation(BaseModel):
    primaryGoal: str
    recommendedSkills: list
    suggestedCourses: list
    financialAdvice: str
    nextSteps: list

class StudentProfileRequest(BaseModel):
    fullName: str
    interests: str
    skills: list[str]
    education: str

from typing import List

class ProfileBuilderRequest(BaseModel):
    fullName: Optional[str] = ""
    academicBackground: Optional[str] = ""  # e.g., Engineering, Commerce, Arts
    keySubjects: List[str] = []
    technicalSkills: List[str] = []
    softSkills: List[str] = []
    hobbies: List[str] = []
    ambition: Optional[str] = ""  # e.g., large-tech, startup, creative, unsure

class EnrichRequest(BaseModel):
    recommendation: Dict[str, Any]  # expects keys like career_path, match_reason, required_skills, learning_roadmap
    userFinance: Optional[Dict[str, Any]] = None  # optionally include { monthlyIncome, spendingCategories }
    userId: Optional[str] = None
    mockDataApiUrl: Optional[str] = None

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ai-career-agent"}


@app.get("/config")
async def config_info():
    return {
        "service": "ai-career-agent",
        "offlineMode": OFFLINE_MODE,
        "geminiConfigured": bool(GEMINI_API_KEY),
        "model": GEMINI_MODEL,
        "version": "1.0.0"
    }


@app.post("/api/analyze-career", response_model=dict)
async def analyze_career_path(request: AnalysisRequest):
    try:
        # Fetch user data from mock API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{request.mockDataApiUrl}/api/users/{request.userId}/financial-data"
            )

        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="User data not found")

        user_data = response.json()

        # Default fallback recommendation (used for offline mode or parse errors)
        fallback_recommendation = {
            "primaryGoal": "Build technical skills for career advancement",
            "recommendedSkills": ["Data Analysis", "Python Programming", "Communication"],
            "suggestedCourses": [
                {"name": "Python for Data Science", "provider": "Coursera", "estimatedCost": "$49"},
                {"name": "Excel to Python", "provider": "Udemy", "estimatedCost": "$85"}
            ],
            "financialAdvice": "Consider allocating 15% of income to skill development",
            "nextSteps": [
                "Start with one online course this month",
                "Set up a dedicated learning budget",
                "Track progress weekly"
            ]
        }

        recommendation = fallback_recommendation

        if not OFFLINE_MODE and GEMINI_API_KEY:
            # Analyze with Gemini (best-effort; fallback on any error)
            try:
                model = genai.GenerativeModel(GEMINI_MODEL)
                prompt = f"""
                Analyze this financial profile and provide career guidance:

                User Profile: {user_data['name']} - {user_data['profile']}
                Monthly Income: ${user_data['monthlyIncome']}
                Career Stage: {user_data['careerStage']}

                Spending Breakdown:
                {json.dumps(user_data['spendingCategories'], indent=2)}

                Recent Transactions:
                {json.dumps(user_data['recentTransactions'], indent=2)}

                Current Goals: {', '.join(user_data['goals'])}

                Please provide career guidance in this JSON format:
                {{
                    "primaryGoal": "One main career objective based on their profile",
                    "recommendedSkills": ["skill1", "skill2", "skill3"],
                    "suggestedCourses": [
                        {{"name": "Course Name", "provider": "Platform", "estimatedCost": "$XX"}},
                        {{"name": "Course Name 2", "provider": "Platform", "estimatedCost": "$XX"}}
                    ],
                    "financialAdvice": "Specific financial recommendation based on their spending",
                    "nextSteps": ["actionable step 1", "actionable step 2", "actionable step 3"]
                }}

                Focus on practical, actionable advice based on their current financial situation and career stage.
                """

                ai_response = model.generate_content(prompt)
                ai_text = ai_response.text or ""
                # Remove any markdown code block formatting
                if "```json" in ai_text:
                    ai_text = ai_text.split("```json", 1)[1].split("```", 1)[0]
                elif "```" in ai_text:
                    ai_text = ai_text.split("```", 1)[1].split("```", 1)[0]

                recommendation = json.loads(ai_text)
            except Exception:
                recommendation = fallback_recommendation

        return {
            "success": True,
            "userId": request.userId,
            "userProfile": user_data['profile'],
            "analysis": recommendation,
            "confidence": "high"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

def _clean_ai_json_text(text: str) -> str:
    # Remove code block wrappers if present
    if "```json" in text:
        try:
            return text.split("```json", 1)[1].split("```", 1)[0]
        except Exception:
            pass
    if "```" in text:
        try:
            return text.split("```", 1)[1].split("```", 1)[0]
        except Exception:
            pass
    return text


@app.post("/analyze", response_model=dict)
async def analyze_student_profile(request: StudentProfileRequest):
    """Accepts user profile data and returns AI-generated career advice.

    Request payload:
      - fullName: string
      - interests: string
      - skills: list[str]
      - education: string

    Response payload:
      {"recommendations": [{"career_path": str, "match_reason": str,
                             "required_skills": [str, ...], "learning_roadmap": [str, ...]}]}
    """
    try:
        # Fallback deterministic recommendations
        fallback = {
            "recommendations": [
                {
                    "career_path": "Data Analyst",
                    "match_reason": "Combines analytical thinking with demand in the Indian job market; good bridge from general STEM skills.",
                    "required_skills": ["Excel/Spreadsheets", "SQL", "Python", "Data Visualization", "Statistics"],
                    "learning_roadmap": [
                        "Complete a beginner SQL course",
                        "Learn Python for data analysis (pandas, matplotlib)",
                        "Build a portfolio project analyzing a public dataset"
                    ]
                },
                {
                    "career_path": "Software Engineer",
                    "match_reason": "Strong demand across product and services companies; suits logical problem-solving and coding skills.",
                    "required_skills": ["Data Structures", "Algorithms", "Git", "Backend or Frontend Framework", "Testing"],
                    "learning_roadmap": [
                        "Practice DSA 30–45 mins daily",
                        "Build a small web app (frontend+backend)",
                        "Contribute to an open-source issue"
                    ]
                },
                {
                    "career_path": "UX Designer",
                    "match_reason": "For creative interests blended with user empathy; growing product ecosystem in India values strong UX.",
                    "required_skills": ["User Research", "Wireframing", "Figma", "Prototyping", "Usability Testing"],
                    "learning_roadmap": [
                        "Study UX fundamentals and heuristics",
                        "Redesign a familiar app and document process",
                        "Share case study on portfolio site"
                    ]
                }
            ]
        }

        if OFFLINE_MODE or not GEMINI_API_KEY:
            return fallback

        try:
            model = genai.GenerativeModel(GEMINI_MODEL)
            prompt = (
                "Act as an expert career counselor for students in India. Given the user's profile, "
                "analyze their strengths and the current Indian job market to provide actionable advice. "
                f"The user's profile is: Interests: {request.interests}, "
                f"Skills: {', '.join(request.skills)}, Education: {request.education}. "
                "Your task is to: 1. Recommend the top 3 most suitable career paths. "
                "2. For each path, briefly explain why it's a good fit. "
                "3. List the 4-5 most critical skills required for that path. "
                "4. Provide a simple 3-step learning roadmap for a beginner. "
                "Respond ONLY with a valid JSON object in the following structure: "
                '{"recommendations": [{"career_path": "...", "match_reason": "...", '
                '"required_skills": ["...", "..."], "learning_roadmap": ["...", "..."]}]}'
            )

            ai_response = model.generate_content(prompt)
            ai_text = ai_response.text or ""
            ai_text = _clean_ai_json_text(ai_text)

            parsed = json.loads(ai_text)
            recs = parsed.get("recommendations")
            if not isinstance(recs, list) or len(recs) == 0:
                raise ValueError("Invalid recommendations format")
            return parsed
        except Exception:
            return fallback

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Student analysis failed: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Student analysis failed: {str(e)}")


@app.post("/enrich-recommendation", response_model=dict)
async def enrich_recommendation(payload: EnrichRequest):
    """Enrich a selected recommendation with salary insights, role progression, market outlook, suggested courses,
    a brief financial advice section tailored to the goal, and a budget plan.
    Accepts either userFinance directly or userId+mockDataApiUrl to fetch it.
    """
    try:
        def _build_spending_plan(finance: Dict[str, Any]) -> Dict[str, Any]:
            monthly = float(finance.get("monthlyIncome") or 30000)
            cats = finance.get("spendingCategories") or {}
            # Baselines
            base_savings = 0.20
            base_education = 0.12
            # Remaining share to split across rent/food/other based on current distribution
            rem = max(0.0, 1.0 - (base_savings + base_education))
            rent = float(cats.get("rent") or 0)
            food = float(cats.get("food") or 0)
            other_known = float(cats.get("other") or 0) + float(cats.get("entertainment") or 0) + float(cats.get("transportation") or 0)
            denom = rent + food + other_known
            if denom <= 0:
                # Even split if no data
                rent_share = food_share = other_share = rem / 3.0
            else:
                rent_share = rem * (rent / denom)
                food_share = rem * (food / denom)
                other_share = rem * (other_known / denom)
            # Normalize to ensure sum=1.0
            alloc = {
                "education": round(base_education, 4),
                "savings": round(base_savings, 4),
                "rent": round(rent_share, 4),
                "food": round(food_share, 4),
                "other": round(other_share, 4)
            }
            # Final tiny adjust for rounding
            total_share = sum(alloc.values())
            if abs(total_share - 1.0) > 1e-6:
                # Adjust 'other'
                alloc["other"] = round(alloc["other"] + (1.0 - total_share), 4)
            notes = (
                f"Suggested monthly allocations computed from your current spending and income of ₹{int(monthly):,}. "
                "Aim for ~20% savings and ~12% education while distributing the rest in line with your existing expenses."
            )
            return {"suggestedAllocation": alloc, "notes": notes}

        def _ensure_defaults(enriched: Dict[str, Any], finance: Dict[str, Any]) -> Dict[str, Any]:
            if not isinstance(enriched, dict):
                enriched = {}
            # Ensure courses
            if not enriched.get("courses"):
                enriched["courses"] = [
                    {"name": "SQL for Data Analysis", "provider": "Coursera", "estimatedCost": "₹3,999"},
                    {"name": "Python with Pandas", "provider": "Udemy", "estimatedCost": "₹2,499"}
                ]
            # Ensure financial advice
            if not enriched.get("financialAdvice"):
                mi = finance.get("monthlyIncome") or 30000
                enriched["financialAdvice"] = (
                    f"With a monthly income around ₹{int(mi):,}, dedicate ~10–15% to learning while maintaining ≥20% savings. "
                    "Scale rent/food/other according to your current pattern and re-evaluate quarterly."
                )
            # Ensure spending plan
            if not enriched.get("spendingPlan") or not enriched["spendingPlan"].get("suggestedAllocation"):
                enriched["spendingPlan"] = _build_spending_plan(finance)
            return enriched

        finance = payload.userFinance
        # Optionally fetch finance data if not provided
        if finance is None and payload.userId and payload.mockDataApiUrl:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{payload.mockDataApiUrl}/api/users/{payload.userId}/financial-data")
                if resp.status_code == 200:
                    user_data = resp.json()
                    finance = {
                        "monthlyIncome": user_data.get("monthlyIncome"),
                        "spendingCategories": user_data.get("spendingCategories", {})
                    }
        # Fallback finance if still missing
        if finance is None:
            finance = {"monthlyIncome": 30000, "spendingCategories": {}}

        fallback = {
            "salaryInsights": {
                "entry": "₹4–6 LPA",
                "median": "₹8–12 LPA",
                "senior": "₹18–25 LPA",
            },
            "roleProgression": [
                "Junior Analyst", "Analyst", "Senior Analyst", "Analytics Lead"
            ],
            "marketOutlook": {
                "demandLevel": "high",
                "trend": "growing",
                "geographies": ["Bengaluru", "Hyderabad", "Gurugram"]
            },
            "courses": [
                {"name": "SQL for Data Analysis", "provider": "Coursera", "estimatedCost": "₹3,999"},
                {"name": "Python with Pandas", "provider": "Udemy", "estimatedCost": "₹2,499"}
            ],
            "financialAdvice": "Allocate a modest monthly budget towards skill development (10–15%) while maintaining at least 20% savings.",
            "spendingPlan": _build_spending_plan(finance)
        }

        if OFFLINE_MODE or not GEMINI_API_KEY:
            return fallback

        try:
            model = genai.GenerativeModel(GEMINI_MODEL)
            monthly_income = finance.get("monthlyIncome")
            prompt = (
                "Given the selected career recommendation, enrich it with realistic insights for the Indian market.\n"
                f"Recommendation: {json.dumps(payload.recommendation)}\n"
                f"Monthly Income (user): {monthly_income}\n"
                "Respond ONLY with valid JSON in this structure: {\n"
                "  \"salaryInsights\": {\"entry\": \"₹x–y LPA\", \"median\": \"₹x–y LPA\", \"senior\": \"₹x–y LPA\"},\n"
                "  \"roleProgression\": [\"Role 1\", \"Role 2\", \"Role 3\"],\n"
                "  \"marketOutlook\": {\"demandLevel\": \"low|medium|high\", \"trend\": \"growing|stable|declining\", \"geographies\": [\"city\", ...]},\n"
                "  \"courses\": [{\"name\": \"Course Name\", \"provider\": \"Platform\", \"estimatedCost\": \"₹x\"}],\n"
                "  \"financialAdvice\": \"One paragraph of practical budget guidance aligned to the selected goal and income.\",\n"
                "  \"spendingPlan\": {\"suggestedAllocation\": {\"education\": 0.1, \"savings\": 0.2, \"rent\": 0.3, \"food\": 0.2, \"other\": 0.2}, \"notes\": \"...\"}\n"
                "}\n"
            )
            ai_resp = model.generate_content(prompt)
            ai_text = ai_resp.text or ""
            ai_text = _clean_ai_json_text(ai_text)
            enriched = json.loads(ai_text)
            enriched = _ensure_defaults(enriched, finance)
            return enriched
        except Exception:
            return fallback
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enrichment failed: {str(e)}")


@app.post("/analyze-profile-advanced", response_model=dict)
async def analyze_profile_advanced(request: ProfileBuilderRequest):
    """Advanced AI analysis: career paths, skill gap mapping, and actionable plan in a strict JSON schema.
    Returns deterministic fallback in offline mode.
    """
    try:
        # Deterministic fallback
        name_str = (request.fullName or "Student").strip() or "Student"
        first_name = name_str.split(' ')[0]
        fallback = {
            "user": {"name": name_str},
            "headline": f"Hi {first_name}, based on your interests and skills, here are tailored career paths.",
            "recommendations": [
                {
                    "jobTitle": "Data Analyst",
                    "whyMatch": "Combines your analytical mindset with your interest in data-driven problem solving.",
                    "skillsHave": [s for s in request.technicalSkills[:2]] + [ss for ss in request.softSkills[:1]],
                    "skillsToDevelop": ["SQL", "Tableau", "Data Visualization"],
                    "actionPlan": [
                        {"type": "course", "title": "Google Data Analytics Professional Certificate", "provider": "Coursera", "link": "https://www.coursera.org/professional-certificates/google-data-analytics"},
                        {"type": "project", "title": "Analyze a Kaggle dataset and publish insights"},
                        {"type": "cert", "title": "Tableau Desktop Specialist"}
                    ]
                },
                {
                    "jobTitle": "Software Engineer",
                    "whyMatch": "Leverages your technical foundation and problem-solving aptitude.",
                    "skillsHave": [s for s in request.technicalSkills[:2]] + [ss for ss in request.softSkills[:1]],
                    "skillsToDevelop": ["Data Structures & Algorithms", "Git", "Testing"],
                    "actionPlan": [
                        {"type": "course", "title": "CS50x: Introduction to Computer Science", "provider": "edX", "link": "https://www.edx.org/course/cs50s-introduction-to-computer-science"},
                        {"type": "project", "title": "Build a full-stack CRUD app (frontend + backend)"},
                        {"type": "cert", "title": "AWS Cloud Practitioner (optional)"}
                    ]
                }
            ]
        }

        if OFFLINE_MODE or not GEMINI_API_KEY:
            return fallback

        try:
            model = genai.GenerativeModel(GEMINI_MODEL)
            prompt = (
                "You are an expert career counselor for students in India, with up-to-date knowledge of the 2025 job market.\n"
                "Given this student profile (as JSON), perform three tasks: 1) recommend 2-3 specific career paths, 2) map skill gaps (skillsHave vs skillsToDevelop), 3) provide an actionable plan per path with 2-3 steps (courses with provider+link, project idea, certification).\n"
                "Respond ONLY with valid JSON in this exact structure: {\n"
                "  \"user\": {\"name\": \"...\"},\n"
                "  \"headline\": \"...\",\n"
                "  \"recommendations\": [\n"
                "    {\n"
                "      \"jobTitle\": \"...\",\n"
                "      \"whyMatch\": \"...\",\n"
                "      \"skillsHave\": [\"...\"],\n"
                "      \"skillsToDevelop\": [\"...\"],\n"
                "      \"actionPlan\": [\n"
                "        {\"type\": \"course\", \"title\": \"...\", \"provider\": \"...\", \"link\": \"https://...\"},\n"
                "        {\"type\": \"project\", \"title\": \"...\"},\n"
                "        {\"type\": \"cert\", \"title\": \"...\"}\n"
                "      ]\n"
                "    }\n"
                "  ]\n"
                "}\n"
                f"Student Profile JSON: {request.model_dump()}\n"
            )
            ai_resp = model.generate_content(prompt)
            ai_text = ai_resp.text or ""
            ai_text = _clean_ai_json_text(ai_text)
            parsed = json.loads(ai_text)
            # Minimal validation
            if not parsed.get("recommendations"):
                return fallback
            return parsed
        except Exception:
            return fallback
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Advanced analysis failed: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
