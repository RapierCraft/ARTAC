"""
Ollama Service - Local LLM for agent generation and bulk processing
"""

import json
import httpx
import asyncio
from typing import Dict, List, Any, Optional
from core.logging import get_logger

logger = get_logger(__name__)


class OllamaService:
    """Service for interacting with local Ollama LLM"""
    
    def __init__(self, base_url: str = "http://ollama:11434"):
        self.base_url = base_url
        self.model = "llama3.2:3b"  # Lightweight but capable model
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def initialize(self):
        """Initialize Ollama service and pull model if needed"""
        try:
            # Check if Ollama is available
            response = await self.client.get(f"{self.base_url}/api/version")
            if response.status_code == 200:
                logger.log_system_event("ollama_connected", {"version": response.json()})
                
                # Pull model if not exists
                await self._ensure_model_available()
                
                logger.log_system_event("ollama_initialized", {
                    "model": self.model,
                    "base_url": self.base_url
                })
                return True
            else:
                logger.log_error(Exception("Ollama not available"), {"status_code": response.status_code})
                return False
                
        except Exception as e:
            logger.log_error(e, {"action": "initialize_ollama"})
            return False
    
    async def _ensure_model_available(self):
        """Ensure the model is pulled and available"""
        try:
            # Check if model exists
            models_response = await self.client.get(f"{self.base_url}/api/tags")
            if models_response.status_code == 200:
                models = models_response.json().get("models", [])
                model_names = [model.get("name", "") for model in models]
                
                if self.model not in model_names:
                    logger.log_system_event("pulling_ollama_model", {"model": self.model})
                    
                    # Pull the model
                    pull_data = {"name": self.model}
                    async with self.client.stream("POST", f"{self.base_url}/api/pull", 
                                                json=pull_data) as response:
                        async for line in response.aiter_lines():
                            if line:
                                try:
                                    status = json.loads(line)
                                    if status.get("status") == "success":
                                        logger.log_system_event("model_pulled", {"model": self.model})
                                        break
                                except json.JSONDecodeError:
                                    continue
                else:
                    logger.log_system_event("model_already_available", {"model": self.model})
                    
        except Exception as e:
            logger.log_error(e, {"action": "ensure_model_available"})
    
    async def generate_agent_profile(self, role: str, experience_level: str = "senior") -> Dict[str, Any]:
        """Generate a detailed agent profile using Ollama"""
        
        prompt = f"""Create a detailed profile for a {experience_level} {role} software professional. 
        
        Generate a realistic profile with:
        1. Full name (diverse, international)
        2. 3-5 relevant technical skills with years of experience (3-15 years each)
        3. 3-4 personality traits with scores (1-10)
        4. Professional bio (2-3 sentences)
        5. Success rate (85-98%)
        6. Projects completed (10-60)
        7. Preferred work style
        
        Return ONLY a JSON object with this exact structure:
        {{
            "name": "Full Name",
            "role": "{role}",
            "skills": [
                {{"name": "SkillName", "level": "advanced|expert", "years_experience": 5}}
            ],  
            "personality": [
                {{"trait": "TraitName", "score": 8, "description": "Brief description"}}
            ],
            "bio": "Professional bio here",
            "success_rate": 0.92,
            "projects_completed": 25,
            "preferred_work_style": "Independent|Collaborative|etc"
        }}
        
        Make it realistic and diverse. No explanations, just the JSON."""
        
        try:
            response = await self._generate(prompt)
            
            # Parse the JSON response
            try:
                # Extract JSON from response (in case there's extra text)
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    profile = json.loads(json_str)
                    
                    logger.log_system_event("agent_profile_generated", {
                        "name": profile.get("name"),
                        "role": role,
                        "skills_count": len(profile.get("skills", []))
                    })
                    
                    return profile
                else:
                    raise ValueError("No valid JSON found in response")
                    
            except (json.JSONDecodeError, ValueError) as e:
                logger.log_error(e, {"action": "parse_agent_profile", "response": response[:200]})
                # Return a fallback profile
                return self._create_fallback_profile(role)
                
        except Exception as e:
            logger.log_error(e, {"action": "generate_agent_profile", "role": role})
            return self._create_fallback_profile(role)
    
    async def generate_multiple_agents(self, roles_and_counts: Dict[str, int]) -> List[Dict[str, Any]]:
        """Generate multiple agent profiles efficiently"""
        
        agents = []
        tasks = []
        
        for role, count in roles_and_counts.items():
            for i in range(count):
                experience = ["junior", "mid", "senior", "expert"][min(i, 3)]
                tasks.append(self.generate_agent_profile(role, experience))
        
        # Generate all profiles concurrently
        logger.log_system_event("generating_agent_batch", {
            "total_agents": sum(roles_and_counts.values()),
            "roles": list(roles_and_counts.keys())
        })
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, dict):
                agents.append(result)
            else:
                logger.log_error(result, {"action": "generate_agent_batch"})
        
        logger.log_system_event("agent_batch_completed", {
            "generated": len(agents),
            "requested": sum(roles_and_counts.values())
        })
        
        return agents
    
    async def enhance_interview_prompt(self, agent_profile: Dict[str, Any], task_description: str) -> str:
        """Create a detailed interview prompt for Claude CLI based on agent profile"""
        
        prompt = f"""Create an interview simulation prompt for Claude CLI. 
        
        Agent Profile:
        - Name: {agent_profile.get('name')}
        - Role: {agent_profile.get('role')}
        - Skills: {', '.join([s.get('name', '') for s in agent_profile.get('skills', [])])}
        - Bio: {agent_profile.get('bio')}
        - Personality: {', '.join([f"{t.get('trait')}: {t.get('score')}/10" for t in agent_profile.get('personality', [])])}
        
        Task: {task_description}
        
        Create a Claude CLI prompt that will make Claude roleplay as this agent during an interview.
        The prompt should include:
        1. Agent's background and experience
        2. How they would approach the given task
        3. Their personality traits and communication style
        4. Specific technical knowledge they would demonstrate
        
        Return only the prompt text that will be sent directly to Claude CLI."""
        
        try:
            interview_prompt = await self._generate(prompt)
            
            logger.log_system_event("interview_prompt_generated", {
                "agent_name": agent_profile.get('name'),
                "task_type": task_description[:50]
            })
            
            return interview_prompt.strip()
            
        except Exception as e:
            logger.log_error(e, {"action": "enhance_interview_prompt"})
            return f"You are {agent_profile.get('name')}, a {agent_profile.get('role')} with experience in {', '.join([s.get('name', '') for s in agent_profile.get('skills', [])])}. Answer interview questions from this perspective."
    
    async def _generate(self, prompt: str) -> str:
        """Generate text using Ollama"""
        
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 1000
            }
        }
        
        response = await self.client.post(f"{self.base_url}/api/generate", json=data)
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "")
        else:
            raise Exception(f"Ollama API error: {response.status_code}")
    
    def _create_fallback_profile(self, role: str) -> Dict[str, Any]:
        """Create a basic fallback profile if generation fails"""
        import random
        import uuid
        
        fallback_names = [
            "Alex Johnson", "Sam Wilson", "Jordan Chen", "Taylor Smith", 
            "Morgan Garcia", "Casey Brown", "Riley Jones", "Dakota Kim"
        ]
        
        skill_map = {
            "developer": ["Python", "JavaScript", "React", "Node.js"],
            "devops": ["Docker", "Kubernetes", "AWS", "Terraform"],
            "security": ["Cybersecurity", "Penetration Testing", "OWASP"],
            "designer": ["UI/UX", "Figma", "User Research"],
            "architect": ["System Design", "Microservices", "API Design"],
            "analyst": ["Data Analysis", "SQL", "Business Intelligence"],
            "tester": ["Test Automation", "Selenium", "QA"],
            "project_manager": ["Agile", "Scrum", "Project Planning"],
            "data_scientist": ["Machine Learning", "Python", "Statistics"]
        }
        
        skills = skill_map.get(role, ["Generic Skill", "Problem Solving"])
        
        return {
            "name": random.choice(fallback_names),
            "role": role,
            "skills": [
                {"name": skill, "level": "advanced", "years_experience": random.randint(3, 8)}
                for skill in skills[:3]
            ],
            "personality": [
                {"trait": "Professional", "score": 8, "description": "Highly professional"},
                {"trait": "Reliable", "score": 9, "description": "Very reliable"},
                {"trait": "Team Player", "score": 7, "description": "Works well in teams"}
            ],
            "bio": f"Experienced {role} with strong technical background",
            "success_rate": 0.90,
            "projects_completed": random.randint(15, 35),
            "preferred_work_style": "Collaborative"
        }
    
    async def shutdown(self):
        """Cleanup resources"""
        await self.client.aclose()


# Global Ollama service instance
ollama_service = OllamaService()