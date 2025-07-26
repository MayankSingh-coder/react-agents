"""Framework for extending to multiagent systems."""

from typing import Any, Dict, List, Optional, Protocol
from abc import ABC, abstractmethod
from enum import Enum

from agent import ReactAgent


class AgentRole(Enum):
    """Predefined agent roles for multiagent systems."""
    COORDINATOR = "coordinator"
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    EXECUTOR = "executor"
    VALIDATOR = "validator"


class AgentCommunication(Protocol):
    """Protocol for agent communication."""
    
    async def send_message(self, recipient: str, message: Dict[str, Any]) -> bool:
        """Send a message to another agent."""
        ...
    
    async def receive_messages(self) -> List[Dict[str, Any]]:
        """Receive pending messages."""
        ...


class MultiAgent(ABC):
    """Abstract base class for agents in a multiagent system."""
    
    def __init__(self, agent_id: str, role: AgentRole, react_agent: ReactAgent):
        self.agent_id = agent_id
        self.role = role
        self.react_agent = react_agent
        self.communication: Optional[AgentCommunication] = None
    
    @abstractmethod
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task assigned to this agent."""
        pass
    
    @abstractmethod
    async def collaborate(self, other_agents: List['MultiAgent']) -> Dict[str, Any]:
        """Collaborate with other agents on a complex task."""
        pass
    
    def set_communication(self, communication: AgentCommunication):
        """Set the communication interface."""
        self.communication = communication


class CoordinatorAgent(MultiAgent):
    """Coordinator agent that manages task distribution and coordination."""
    
    def __init__(self, agent_id: str, react_agent: ReactAgent):
        super().__init__(agent_id, AgentRole.COORDINATOR, react_agent)
        self.managed_agents: List[MultiAgent] = []
    
    def add_agent(self, agent: MultiAgent):
        """Add an agent to be managed."""
        self.managed_agents.append(agent)
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a coordination task."""
        # Use the React agent to plan the task distribution
        planning_query = f"Plan how to distribute this task among available agents: {task}"
        plan_response = await self.react_agent.run(planning_query)
        
        return {
            "agent_id": self.agent_id,
            "role": self.role.value,
            "task": task,
            "plan": plan_response["output"],
            "success": plan_response["success"]
        }
    
    async def collaborate(self, other_agents: List[MultiAgent]) -> Dict[str, Any]:
        """Coordinate collaboration between agents."""
        # Implementation for coordinating multiple agents
        collaboration_plan = {
            "coordinator": self.agent_id,
            "participating_agents": [agent.agent_id for agent in other_agents],
            "coordination_strategy": "sequential_processing"
        }
        
        return collaboration_plan


class ResearcherAgent(MultiAgent):
    """Researcher agent specialized in information gathering."""
    
    def __init__(self, agent_id: str, react_agent: ReactAgent):
        super().__init__(agent_id, AgentRole.RESEARCHER, react_agent)
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a research task."""
        research_query = f"Research and gather information about: {task.get('query', '')}"
        research_response = await self.react_agent.run(research_query)
        
        return {
            "agent_id": self.agent_id,
            "role": self.role.value,
            "task": task,
            "research_results": research_response["output"],
            "sources_used": [step.get("action") for step in research_response["steps"] if step.get("action")],
            "success": research_response["success"]
        }
    
    async def collaborate(self, other_agents: List[MultiAgent]) -> Dict[str, Any]:
        """Collaborate by sharing research findings."""
        return {
            "collaboration_type": "research_sharing",
            "agent_id": self.agent_id,
            "shared_knowledge": "Research findings and sources"
        }


class AnalystAgent(MultiAgent):
    """Analyst agent specialized in data analysis and interpretation."""
    
    def __init__(self, agent_id: str, react_agent: ReactAgent):
        super().__init__(agent_id, AgentRole.ANALYST, react_agent)
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process an analysis task."""
        analysis_query = f"Analyze the following data and provide insights: {task.get('data', '')}"
        analysis_response = await self.react_agent.run(analysis_query)
        
        return {
            "agent_id": self.agent_id,
            "role": self.role.value,
            "task": task,
            "analysis_results": analysis_response["output"],
            "tools_used": [step.get("action") for step in analysis_response["steps"] if step.get("action")],
            "success": analysis_response["success"]
        }
    
    async def collaborate(self, other_agents: List[MultiAgent]) -> Dict[str, Any]:
        """Collaborate by providing analytical insights."""
        return {
            "collaboration_type": "analysis_sharing",
            "agent_id": self.agent_id,
            "shared_insights": "Analytical findings and interpretations"
        }


class MultiAgentSystem:
    """System for managing multiple React agents."""
    
    def __init__(self):
        self.agents: Dict[str, MultiAgent] = {}
        self.task_queue: List[Dict[str, Any]] = []
        self.results: List[Dict[str, Any]] = []
    
    def add_agent(self, agent: MultiAgent):
        """Add an agent to the system."""
        self.agents[agent.agent_id] = agent
    
    def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent from the system."""
        if agent_id in self.agents:
            del self.agents[agent_id]
            return True
        return False
    
    def get_agents_by_role(self, role: AgentRole) -> List[MultiAgent]:
        """Get all agents with a specific role."""
        return [agent for agent in self.agents.values() if agent.role == role]
    
    async def distribute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Distribute a task to appropriate agents."""
        # Simple task distribution logic
        task_type = task.get("type", "general")
        
        if task_type == "research":
            researchers = self.get_agents_by_role(AgentRole.RESEARCHER)
            if researchers:
                result = await researchers[0].process_task(task)
                self.results.append(result)
                return result
        
        elif task_type == "analysis":
            analysts = self.get_agents_by_role(AgentRole.ANALYST)
            if analysts:
                result = await analysts[0].process_task(task)
                self.results.append(result)
                return result
        
        # Default: use coordinator if available
        coordinators = self.get_agents_by_role(AgentRole.COORDINATOR)
        if coordinators:
            result = await coordinators[0].process_task(task)
            self.results.append(result)
            return result
        
        # Fallback: use any available agent
        if self.agents:
            agent = list(self.agents.values())[0]
            result = await agent.process_task(task)
            self.results.append(result)
            return result
        
        return {"error": "No agents available to process the task"}
    
    async def collaborative_task(self, task: Dict[str, Any], agent_ids: List[str]) -> Dict[str, Any]:
        """Execute a task that requires collaboration between multiple agents."""
        participating_agents = [self.agents[agent_id] for agent_id in agent_ids if agent_id in self.agents]
        
        if not participating_agents:
            return {"error": "No valid agents found for collaboration"}
        
        # Execute collaboration
        collaboration_results = []
        for agent in participating_agents:
            result = await agent.collaborate(participating_agents)
            collaboration_results.append(result)
        
        # Combine results
        combined_result = {
            "task": task,
            "collaboration_results": collaboration_results,
            "participating_agents": agent_ids,
            "success": True
        }
        
        self.results.append(combined_result)
        return combined_result
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get statistics about the multiagent system."""
        return {
            "total_agents": len(self.agents),
            "agents_by_role": {
                role.value: len(self.get_agents_by_role(role)) 
                for role in AgentRole
            },
            "completed_tasks": len(self.results),
            "agent_ids": list(self.agents.keys())
        }


# Factory functions for creating specialized agents
def create_coordinator_agent(agent_id: str = "coordinator_1") -> CoordinatorAgent:
    """Create a coordinator agent."""
    react_agent = ReactAgent(verbose=False)
    return CoordinatorAgent(agent_id, react_agent)


def create_researcher_agent(agent_id: str = "researcher_1") -> ResearcherAgent:
    """Create a researcher agent."""
    react_agent = ReactAgent(verbose=False)
    return ResearcherAgent(agent_id, react_agent)


def create_analyst_agent(agent_id: str = "analyst_1") -> AnalystAgent:
    """Create an analyst agent."""
    react_agent = ReactAgent(verbose=False)
    return AnalystAgent(agent_id, react_agent)