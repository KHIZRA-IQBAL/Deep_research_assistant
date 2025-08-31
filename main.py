from dotenv import load_dotenv
from agents import Agent, Runner
import rich
import asyncio
from typing import Dict
import json
import re
import chainlit as cl

# -----------------------------------------
load_dotenv()
# -----------------------------------------

class ResearchTeam:
    def __init__(self):
        self.setup_agents()
        
    def setup_agents(self): 
        """Setup research team with specialized agents"""
        self.technical_agent = Agent(
            name="technical_researcher",
            instructions="""
            You are a technical research expert. Focus on technical specifications,
            features, performance metrics, and engineering aspects. Provide detailed technical analysis.
            """,
            model="gpt-4.1-mini"
        )
        
        self.economic_agent = Agent(
            name="economic_researcher",
            instructions="""
            You are an economic research expert. Focus on costs, pricing, market trends,
            economic impact, and financial considerations. Provide economic analysis.
            """,
            model="gpt-4.1-mini"
        )
        
        self.environmental_agent = Agent(
            name="environmental_researcher",
            instructions="""
            You are an environmental research expert. Focus on ecological impact,
            sustainability, carbon footprint, and environmental considerations.
            """,
            model="gpt-4.1-mini"
        )
        
        self.planning_agent = Agent(
            name="research_planner",
            instructions="""
            You are a research planning expert. Break down complex questions into specific research subtopics.
            For each subtopic, specify which specialized agent should research it and what specific aspect to focus on.
            Use ONLY these agent names: technical_agent, economic_agent, environmental_agent.
            Return ONLY valid JSON format with detailed research plan. No other text.
            """,
            model="gpt-4.1-mini"
        )
        
        self.comparative_agent = Agent(
            name="comparative_researcher",
            instructions="""
            You specialize in comparing and contrasting different options, technologies, or approaches.
            Provide balanced comparison with advantages and disadvantages. Analyze trade-offs and recommendations.
            """,
            model="gpt-4.1-mini"
        )
        
        self.verification_agent = Agent(
            name="verification_expert",
            instructions="""
            You are a fact-checking and source verification expert. 
            Verify the credibility of information, check sources, and identify potential biases.
            Return credibility score and verification notes.
            """,
            model="gpt-4.1-mini"
        )
        
        self.quality_agent = Agent(
            name="quality_assurance",
            instructions="""
            You are a quality assurance specialist. Check research quality, 
            identify gaps, ensure completeness, and maintain professional standards.
            Provide quality assessment and improvement suggestions.
            """,
            model="gpt-4.1-mini"
        )
        
        self.coordinator_agent = Agent(
            name="research_coordinator",
            instructions="""You are a research coordinator. Analyze questions and delegate to appropriate 
            specialized researchers. Then synthesize their findings into a comprehensive report.""",
            model="gpt-4.1-mini",
            tools=[
                self.technical_agent.as_tool(
                    tool_name="technical_research",
                    tool_description="Delegate technical aspects research"
                ),
                self.economic_agent.as_tool(
                    tool_name="economic_research",
                    tool_description="Delegate economic aspects research"
                ),
                self.environmental_agent.as_tool(
                    tool_name="environmental_research",
                    tool_description="Delegate environmental aspects research"
                ),
                self.planning_agent.as_tool(
                    tool_name="research_planning",
                    tool_description="Create detailed research plan for complex questions"
                ),
                self.comparative_agent.as_tool(
                    tool_name="comparative_analysis",
                    tool_description="Perform comparative analysis between different options"
                ),
                self.verification_agent.as_tool(
                    tool_name="source_verification",
                    tool_description="Verify sources and check information credibility"
                ),
                self.quality_agent.as_tool(
                    tool_name="quality_assurance", 
                    tool_description="Perform quality check on research findings"
                )
            ]
        )

    def extract_json_from_text(self, text: str) -> Dict:
        """Extract JSON from text if planning agent returns text with JSON"""
        try:
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                plan_data = json.loads(json_str)
                
                valid_agents = ["technical_agent", "economic_agent", "environmental_agent"]
                for subtopic in plan_data.get("subtopics", []):
                    if subtopic.get("assigned_agent") not in valid_agents:
                        focus = subtopic.get("research_focus", "").lower()
                        if any(word in focus for word in ["technical", "performance", "engineer", "spec"]):
                            subtopic["assigned_agent"] = "technical_agent"
                        elif any(word in focus for word in ["economic", "cost", "price", "market", "financial"]):
                            subtopic["assigned_agent"] = "economic_agent"
                        elif any(word in focus for word in ["environment", "ecological", "sustain", "carbon", "pollution"]):
                            subtopic["assigned_agent"] = "environmental_agent"
                        else:
                            subtopic["assigned_agent"] = "technical_agent"
                
                return plan_data
            else:
                return {
                    "overall_approach": "Comprehensive comparison analysis",
                    "subtopics": [
                        {
                            "subtopic": "Technical Performance Comparison",
                            "assigned_agent": "technical_agent",
                            "research_focus": "Compare performance metrics"
                        },
                        {
                            "subtopic": "Cost Analysis",
                            "assigned_agent": "economic_agent", 
                            "research_focus": "Compare costs and economics"
                        },
                        {
                            "subtopic": "Environmental Impact Assessment",
                            "assigned_agent": "environmental_agent",
                            "research_focus": "Compare environmental impact"
                        }
                    ]
                }
        except json.JSONDecodeError:
            return {
                "overall_approach": "Comprehensive comparison analysis",
                "subtopics": [
                    {
                        "subtopic": "Technical Performance Comparison",
                        "assigned_agent": "technical_agent",
                        "research_focus": "Compare performance metrics"
                    },
                    {
                        "subtopic": "Cost Analysis", 
                        "assigned_agent": "economic_agent",
                        "research_focus": "Compare costs and economics"
                    },
                    {
                        "subtopic": "Environmental Impact Assessment",
                        "assigned_agent": "environmental_agent",
                        "research_focus": "Compare environmental impact"
                    }
                ]
            }

    async def create_research_plan(self, question: str) -> Dict:
        """Create detailed research plan for complex questions"""
        result = await Runner.run(
            self.planning_agent,
            input=f"""Break down this complex research question into specific subtopics: {question}
            
            Use ONLY these agent names: technical_agent, economic_agent, environmental_agent.
            
            Return ONLY valid JSON format:
            {{
                "overall_approach": "brief description",
                "subtopics": [
                    {{
                        "subtopic": "specific aspect to research",
                        "assigned_agent": "agent_name",
                        "research_focus": "what specifically to research"
                    }}
                ]
            }}"""
        )
        
        return self.extract_json_from_text(result.final_output)

    async def execute_parallel_research(self, question: str, research_plan: Dict) -> Dict:
        """Execute parallel research using multiple agents simultaneously"""
        results = {}
        
        async def research_subtopic(subtopic: Dict):
            agent_name = subtopic["assigned_agent"]
            research_focus = subtopic["research_focus"]
            
            agent = getattr(self, agent_name)
            result = await Runner.run(
                agent,
                input=f"""Research this specific aspect: {research_focus}
                Context: {question}
                Provide detailed, focused information on this specific topic."""
            )
            return subtopic["subtopic"], result.final_output
        
        tasks = []
        for subtopic in research_plan["subtopics"]:
            tasks.append(research_subtopic(subtopic))
        
        subtopic_results = await asyncio.gather(*tasks)
        
        for subtopic, result in subtopic_results:
            results[subtopic] = result
        
        return results

    async def synthesize_findings(self, question: str, research_results: Dict) -> str:
        """Synthesize all research findings into comprehensive report"""
        research_context = "\n".join([
            f"## {topic}\n{content}\n" for topic, content in research_results.items()
        ])
        
        result = await Runner.run(
            self.coordinator_agent,
            input=f"""Synthesize this research into a comprehensive report:
            
            Original Question: {question}
            
            Research Findings:
            {research_context}
            
            Create a well-structured, comprehensive report that addresses the original question thoroughly.
            Include introduction, main findings, analysis, and conclusion."""
        )
        return result.final_output

    async def professional_research(self, question: str, message: cl.Message = None) -> Dict:
        """Complete professional research process with streaming"""
        if message:
            await message.stream_token(f"🧠 **Researching:** {question}\n\n")
            await message.stream_token("📋 **Creating research plan...**\n")
        
        # 1. Create research plan
        research_plan = await self.create_research_plan(question)
        
        if message:
            await message.stream_token(f"🎯 **Approach:** {research_plan['overall_approach']}\n")
            await message.stream_token("🧩 **Research subtopics:**\n")
            for i, subtopic in enumerate(research_plan["subtopics"], 1):
                await message.stream_token(f"   {i}. {subtopic['subtopic']} → {subtopic['assigned_agent']}\n")
        
        # 2. Execute parallel research
        if message:
            await message.stream_token("\n🔍 **Researching subtopics in parallel...**\n")
        research_results = await self.execute_parallel_research(question, research_plan)
        
        if message:
            await message.stream_token("✅ **All subtopics researched successfully!**\n")
        
        # 3. Synthesize findings
        if message:
            await message.stream_token("\n📊 **Synthesizing findings...**\n")
        synthesis = await self.synthesize_findings(question, research_results)
        
        if message:
            await message.stream_token("🎉 **Final report generated!**\n")
        
        return {
            "research_plan": research_plan,
            "research_results": research_results,
            "synthesis": synthesis
        }

@cl.on_chat_start
async def start_chat():
    """Initialize when chat starts"""
    research_team = ResearchTeam()
    cl.user_session.set("research_team", research_team)
    await cl.Message(content="""
    🔬 **Welcome to AI Research Assistant!**
    
    I'm your specialized research assistant with multiple expert agents:
    - 🤖 Technical Researcher
    - 💰 Economic Analyst  
    - 🌍 Environmental Expert
    - 📊 Comparative Analyst
    - ✅ Quality Assurance
    
    **Please enter your research question below and I'll provide a comprehensive analysis!**
    """).send()

@cl.on_message
async def main(message: cl.Message):
    """Handle user messages with streaming"""
    research_team = cl.user_session.get("research_team")
    
    if not message.content.strip():
        await cl.Message(content="❌ Please enter a valid question!").send()
        return
    
    # Create streaming message
    msg = cl.Message(content="")
    await msg.send()
    
    try:
        # Conduct research with streaming
        result = await research_team.professional_research(message.content, msg)
        
        # Final report with streaming
        await msg.stream_token("\n" + "="*50 + "\n")
        await msg.stream_token("# 📊 **FINAL RESEARCH REPORT**\n\n")
        await msg.stream_token(f"## ❓ Original Question:\n{message.content}\n\n")
        await msg.stream_token(f"## 🎯 Research Approach:\n{result['research_plan']['overall_approach']}\n\n")
        await msg.stream_token(f"## 📋 Topics Researched:\n{len(result['research_results'])} specialized topics\n\n")
        await msg.stream_token("## 📄 Detailed Report:\n")
        
        await msg.stream_token(result['synthesis'])
        
        await msg.stream_token("\n\n## ✅ **Research Completed Successfully!**")
        
    except Exception as e:
        await msg.stream_token(f"❌ **Error:** {str(e)}")

if __name__ == "__main__":
    pass







