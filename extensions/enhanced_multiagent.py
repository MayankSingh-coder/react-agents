"""Enhanced Multi-Agent Framework - Practical Implementation"""

import asyncio
import uuid
import json
from typing import Any, Dict, List, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import time
import logging

# Import your existing components
from agent.react_agent import ReactAgent
from tools.base_tool import BaseTool, ToolResult
from memory.episodic_memory import Episode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentCapability(Enum):
    """Enhanced agent capabilities for specialization"""
    RESEARCH = "research"
    ANALYSIS = "analysis"
    CODING = "coding"
    PLANNING = "planning"
    COORDINATION = "coordination"
    MEMORY = "memory"
    VALIDATION = "validation"
    EXECUTION = "execution"
    LEARNING = "learning"
    COMMUNICATION = "communication"


class MessageType(Enum):
    """Types of inter-agent messages"""
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    INFORMATION_SHARE = "info_share"
    COORDINATION = "coordination"
    STATUS_UPDATE = "status_update"
    ERROR_REPORT = "error_report"
    CAPABILITY_QUERY = "capability_query"
    KNOWLEDGE_SHARE = "knowledge_share"


@dataclass
class AgentMessage:
    """Message structure for inter-agent communication"""
    sender_id: str
    recipient_id: str
    message_type: MessageType
    content: Dict[str, Any]
    priority: int = 1
    requires_response: bool = False
    correlation_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "message_type": self.message_type.value,
            "content": self.content,
            "priority": self.priority,
            "requires_response": self.requires_response,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        return cls(
            sender_id=data["sender_id"],
            recipient_id=data["recipient_id"],
            message_type=MessageType(data["message_type"]),
            content=data["content"],
            priority=data.get("priority", 1),
            requires_response=data.get("requires_response", False),
            correlation_id=data.get("correlation_id"),
            timestamp=data.get("timestamp", time.time())
        )


@dataclass
class Task:
    """Task representation for multi-agent processing"""
    id: str
    description: str
    required_capabilities: List[AgentCapability]
    priority: int = 1
    deadline: Optional[float] = None
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CollaborationResult:
    """Result of multi-agent collaboration"""
    task_id: str
    success: bool
    result: Any
    participating_agents: List[str]
    execution_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentTool(BaseTool):
    """Wrapper that makes any agent appear as a tool to other agents"""
    
    def __init__(self, agent: 'EnhancedMultiAgent', agent_role: str):
        super().__init__(
            name=f"{agent_role}_agent",
            description=f"Specialized {agent_role} agent with capabilities: {', '.join([cap.value for cap in agent.capabilities])}"
        )
        self.agent = agent
        self.agent_role = agent_role
    
    async def execute(self, query: str, **kwargs) -> ToolResult:
        """Execute the wrapped agent"""
        try:
            result = await self.agent.process_request(query, **kwargs)
            
            return ToolResult(
                success=result.get("success", True),
                output=result.get("output", ""),
                metadata={
                    "agent_role": self.agent_role,
                    "agent_id": self.agent.agent_id,
                    "execution_time": result.get("execution_time", 0)
                }
            )
        except Exception as e:
            logger.error(f"Error executing agent tool {self.agent_role}: {e}")
            return ToolResult(
                success=False,
                output=f"Error in {self.agent_role} agent: {str(e)}",
                metadata={"error": str(e)}
            )
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's input schema"""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": f"Query to process with {self.agent_role} agent"
                },
                "context": {
                    "type": "object",
                    "description": "Additional context for the agent"
                }
            },
            "required": ["query"]
        }


class EnhancedMultiAgent:
    """Enhanced agent that can work independently or as part of multi-agent system"""
    
    def __init__(self, 
                 agent_id: str,
                 capabilities: List[AgentCapability],
                 react_agent: Optional[ReactAgent] = None):
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.react_agent = react_agent or ReactAgent(verbose=False)
        
        # Multi-agent specific components
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.peer_agents: Dict[str, 'EnhancedMultiAgent'] = {}
        self.collaboration_sessions: Dict[str, Dict] = {}
        self.knowledge_shared: Dict[str, Any] = {}
        
        # Performance tracking
        self.task_count = 0
        self.success_count = 0
        self.total_execution_time = 0.0
        
        logger.info(f"Created enhanced multi-agent {agent_id} with capabilities: {[cap.value for cap in capabilities]}")
    
    async def process_request(self, query: str, **kwargs) -> Dict[str, Any]:
        """Process a request using the agent's React core"""
        start_time = time.time()
        
        try:
            # Check if this request should be handled collaboratively
            if await self._should_collaborate(query):
                result = await self._collaborative_process(query, **kwargs)
            else:
                # Use the existing ReactAgent logic
                result = await self.react_agent.run(query, **kwargs)
            
            execution_time = time.time() - start_time
            
            # Update performance metrics
            self.task_count += 1
            if result.get("success", True):
                self.success_count += 1
            self.total_execution_time += execution_time
            
            # Add agent metadata
            result.update({
                "agent_id": self.agent_id,
                "capabilities": [cap.value for cap in self.capabilities],
                "execution_time": execution_time
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error in agent {self.agent_id}: {e}")
            return {
                "success": False,
                "output": f"Error: {str(e)}",
                "agent_id": self.agent_id,
                "error": str(e)
            }
    
    async def _should_collaborate(self, query: str) -> bool:
        """Determine if query requires collaboration with other agents"""
        # Simple heuristics - you can make this more sophisticated
        collaboration_keywords = [
            "analyze and research", "research and then", "first search then",
            "multiple steps", "complex analysis", "comprehensive report"
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in collaboration_keywords)
    
    async def _collaborative_process(self, query: str, **kwargs) -> Dict[str, Any]:
        """Process query through collaboration with peer agents"""
        collaboration_id = str(uuid.uuid4())
        
        try:
            # Identify required capabilities
            required_capabilities = await self._identify_required_capabilities(query)
            
            # Find capable peer agents
            capable_agents = self._find_capable_peers(required_capabilities)
            
            if not capable_agents:
                # Fallback to single agent processing
                return await self.react_agent.run(query, **kwargs)
            
            # Create collaboration session
            collaboration = {
                "id": collaboration_id,
                "query": query,
                "participants": [self.agent_id] + list(capable_agents.keys()),
                "start_time": time.time(),
                "status": "active"
            }
            self.collaboration_sessions[collaboration_id] = collaboration
            
            # Delegate parts of the query to capable agents
            results = await self._coordinate_collaboration(query, capable_agents, **kwargs)
            
            # Synthesize results
            final_result = await self._synthesize_results(results)
            
            collaboration["status"] = "completed"
            collaboration["end_time"] = time.time()
            
            return final_result
            
        except Exception as e:
            logger.error(f"Collaboration error: {e}")
            if collaboration_id in self.collaboration_sessions:
                self.collaboration_sessions[collaboration_id]["status"] = "failed"
            
            # Fallback to single agent processing
            return await self.react_agent.run(query, **kwargs)
    
    async def _identify_required_capabilities(self, query: str) -> List[AgentCapability]:
        """Identify capabilities required for the query"""
        capabilities = []
        query_lower = query.lower()
        
        # Simple keyword-based capability detection
        capability_keywords = {
            AgentCapability.RESEARCH: ["search", "research", "find information", "lookup"],
            AgentCapability.ANALYSIS: ["analyze", "analysis", "examine", "evaluate"],
            AgentCapability.CODING: ["code", "program", "implement", "debug"],
            AgentCapability.PLANNING: ["plan", "organize", "structure", "breakdown"]
        }
        
        for capability, keywords in capability_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                capabilities.append(capability)
        
        return capabilities
    
    def _find_capable_peers(self, required_capabilities: List[AgentCapability]) -> Dict[str, 'EnhancedMultiAgent']:
        """Find peer agents with required capabilities"""
        capable_peers = {}
        
        for agent_id, agent in self.peer_agents.items():
            if any(cap in agent.capabilities for cap in required_capabilities):
                capable_peers[agent_id] = agent
        
        return capable_peers
    
    async def _coordinate_collaboration(self, 
                                      query: str, 
                                      capable_agents: Dict[str, 'EnhancedMultiAgent'],
                                      **kwargs) -> Dict[str, Any]:
        """Coordinate collaboration between agents"""
        results = {}
        
        # Simple sequential processing - can be enhanced to parallel
        for agent_id, agent in capable_agents.items():
            try:
                # Delegate appropriate part of query to agent
                delegated_query = await self._create_delegated_query(query, agent.capabilities)
                result = await agent.process_request(delegated_query, **kwargs)
                results[agent_id] = result
                
                # Share knowledge with other agents
                await self._share_knowledge(agent_id, result)
                
            except Exception as e:
                logger.error(f"Error in collaboration with agent {agent_id}: {e}")
                results[agent_id] = {"success": False, "error": str(e)}
        
        return results
    
    async def _create_delegated_query(self, original_query: str, agent_capabilities: List[AgentCapability]) -> str:
        """Create a delegated query appropriate for agent's capabilities"""
        # Simple delegation logic - can be enhanced
        if AgentCapability.RESEARCH in agent_capabilities:
            return f"Research information about: {original_query}"
        elif AgentCapability.ANALYSIS in agent_capabilities:
            return f"Analyze the following: {original_query}"
        elif AgentCapability.CODING in agent_capabilities:
            return f"Help with coding aspects of: {original_query}"
        else:
            return original_query
    
    async def _synthesize_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize results from multiple agents"""
        all_outputs = []
        all_successful = True
        
        for agent_id, result in results.items():
            if result.get("success", True):
                all_outputs.append(f"From {agent_id}: {result.get('output', '')}")
            else:
                all_successful = False
                all_outputs.append(f"Error from {agent_id}: {result.get('error', 'Unknown error')}")
        
        synthesized_output = "\n\n".join(all_outputs)
        
        return {
            "success": all_successful,
            "output": synthesized_output,
            "collaboration_results": results,
            "participating_agents": list(results.keys())
        }
    
    async def _share_knowledge(self, source_agent_id: str, knowledge: Dict[str, Any]):
        """Share knowledge learned from collaboration"""
        self.knowledge_shared[source_agent_id] = {
            "timestamp": time.time(),
            "knowledge": knowledge,
            "relevance_score": 1.0  # Can be enhanced with actual scoring
        }
    
    def add_peer(self, agent: 'EnhancedMultiAgent'):
        """Add a peer agent for collaboration"""
        self.peer_agents[agent.agent_id] = agent
        logger.info(f"Added peer agent {agent.agent_id} to {self.agent_id}")
    
    def remove_peer(self, agent_id: str):
        """Remove a peer agent"""
        if agent_id in self.peer_agents:
            del self.peer_agents[agent_id]
            logger.info(f"Removed peer agent {agent_id} from {self.agent_id}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        success_rate = (self.success_count / self.task_count) if self.task_count > 0 else 0
        avg_execution_time = (self.total_execution_time / self.task_count) if self.task_count > 0 else 0
        
        return {
            "agent_id": self.agent_id,
            "capabilities": [cap.value for cap in self.capabilities],
            "task_count": self.task_count,
            "success_count": self.success_count,
            "success_rate": success_rate,
            "average_execution_time": avg_execution_time,
            "peer_count": len(self.peer_agents),
            "active_collaborations": len([c for c in self.collaboration_sessions.values() if c["status"] == "active"])
        }


class MultiAgentOrchestrator:
    """Orchestrator for managing multiple enhanced agents"""
    
    def __init__(self):
        self.agents: Dict[str, EnhancedMultiAgent] = {}
        self.capability_index: Dict[AgentCapability, List[str]] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.active_tasks: Dict[str, Task] = {}
        
        logger.info("Multi-agent orchestrator initialized")
    
    def register_agent(self, agent: EnhancedMultiAgent):
        """Register an agent with the orchestrator"""
        self.agents[agent.agent_id] = agent
        
        # Update capability index
        for capability in agent.capabilities:
            if capability not in self.capability_index:
                self.capability_index[capability] = []
            self.capability_index[capability].append(agent.agent_id)
        
        # Connect agent to other relevant agents as peers
        self._connect_peers(agent)
        
        logger.info(f"Registered agent {agent.agent_id} with orchestrator")
    
    def _connect_peers(self, new_agent: EnhancedMultiAgent):
        """Connect new agent to relevant existing agents"""
        for agent_id, existing_agent in self.agents.items():
            if agent_id != new_agent.agent_id:
                # Connect if they have complementary capabilities
                if self._have_complementary_capabilities(new_agent, existing_agent):
                    new_agent.add_peer(existing_agent)
                    existing_agent.add_peer(new_agent)
    
    def _have_complementary_capabilities(self, agent1: EnhancedMultiAgent, agent2: EnhancedMultiAgent) -> bool:
        """Check if two agents have complementary capabilities"""
        # Simple heuristic: different capabilities that can work together
        complementary_pairs = [
            (AgentCapability.RESEARCH, AgentCapability.ANALYSIS),
            (AgentCapability.PLANNING, AgentCapability.EXECUTION),
            (AgentCapability.CODING, AgentCapability.VALIDATION)
        ]
        
        for cap1, cap2 in complementary_pairs:
            if ((cap1 in agent1.capabilities and cap2 in agent2.capabilities) or
                (cap2 in agent1.capabilities and cap1 in agent2.capabilities)):
                return True
        
        return False
    
    async def process_query(self, query: str, preferred_agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Process a query using the best available agent"""
        
        if preferred_agent_id and preferred_agent_id in self.agents:
            # Use preferred agent
            agent = self.agents[preferred_agent_id]
            return await agent.process_request(query)
        
        # Find best agent for the query
        required_capabilities = await self._analyze_query_requirements(query)
        best_agent = self._find_best_agent(required_capabilities)
        
        if best_agent:
            return await best_agent.process_request(query)
        else:
            return {
                "success": False,
                "output": "No capable agent available for this query",
                "error": "No agent found"
            }
    
    async def _analyze_query_requirements(self, query: str) -> List[AgentCapability]:
        """Analyze query to determine required capabilities"""
        # This is a simplified version - can be enhanced with ML
        query_lower = query.lower()
        
        capabilities = []
        
        # Keyword-based analysis
        if any(word in query_lower for word in ["search", "research", "find", "lookup"]):
            capabilities.append(AgentCapability.RESEARCH)
        
        if any(word in query_lower for word in ["analyze", "analysis", "examine", "evaluate"]):
            capabilities.append(AgentCapability.ANALYSIS)
        
        if any(word in query_lower for word in ["code", "program", "implement", "debug"]):
            capabilities.append(AgentCapability.CODING)
        
        if any(word in query_lower for word in ["plan", "organize", "structure", "breakdown"]):
            capabilities.append(AgentCapability.PLANNING)
        
        return capabilities
    
    def _find_best_agent(self, required_capabilities: List[AgentCapability]) -> Optional[EnhancedMultiAgent]:
        """Find the best agent for given capabilities"""
        candidate_agents = []
        
        # Find agents with required capabilities
        for capability in required_capabilities:
            if capability in self.capability_index:
                candidate_agents.extend(self.capability_index[capability])
        
        if not candidate_agents:
            # Return any available agent as fallback
            return list(self.agents.values())[0] if self.agents else None
        
        # Score agents by capability match and performance
        best_agent = None
        best_score = -1
        
        for agent_id in set(candidate_agents):  # Remove duplicates
            agent = self.agents[agent_id]
            
            # Calculate score based on capability match and performance
            capability_score = len(set(required_capabilities) & set(agent.capabilities))
            performance_score = agent.success_count / max(agent.task_count, 1)
            
            total_score = capability_score + performance_score
            
            if total_score > best_score:
                best_score = total_score
                best_agent = agent
        
        return best_agent
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get overall system statistics"""
        total_tasks = sum(agent.task_count for agent in self.agents.values())
        total_successes = sum(agent.success_count for agent in self.agents.values())
        
        agent_stats = {agent_id: agent.get_performance_stats() 
                      for agent_id, agent in self.agents.items()}
        
        return {
            "total_agents": len(self.agents),
            "total_tasks_processed": total_tasks,
            "total_successful_tasks": total_successes,
            "overall_success_rate": total_successes / max(total_tasks, 1),
            "capability_coverage": {cap.value: len(agents) for cap, agents in self.capability_index.items()},
            "agent_stats": agent_stats
        }


# Factory functions for creating specialized agents
def create_researcher_agent(agent_id: str = None) -> EnhancedMultiAgent:
    """Create a specialized research agent"""
    agent_id = agent_id or f"researcher_{uuid.uuid4().hex[:8]}"
    react_agent = ReactAgent(verbose=False)
    
    return EnhancedMultiAgent(
        agent_id=agent_id,
        capabilities=[AgentCapability.RESEARCH, AgentCapability.COMMUNICATION],
        react_agent=react_agent
    )


def create_analyst_agent(agent_id: str = None) -> EnhancedMultiAgent:
    """Create a specialized analysis agent"""
    agent_id = agent_id or f"analyst_{uuid.uuid4().hex[:8]}"
    react_agent = ReactAgent(verbose=False)
    
    return EnhancedMultiAgent(
        agent_id=agent_id,
        capabilities=[AgentCapability.ANALYSIS, AgentCapability.VALIDATION],
        react_agent=react_agent
    )


def create_coder_agent(agent_id: str = None) -> EnhancedMultiAgent:
    """Create a specialized coding agent"""
    agent_id = agent_id or f"coder_{uuid.uuid4().hex[:8]}"
    react_agent = ReactAgent(verbose=False)
    
    return EnhancedMultiAgent(
        agent_id=agent_id,
        capabilities=[AgentCapability.CODING, AgentCapability.EXECUTION],
        react_agent=react_agent
    )


def create_coordinator_agent(agent_id: str = None) -> EnhancedMultiAgent:
    """Create a coordinator agent"""
    agent_id = agent_id or f"coordinator_{uuid.uuid4().hex[:8]}"
    react_agent = ReactAgent(verbose=False)
    
    return EnhancedMultiAgent(
        agent_id=agent_id,
        capabilities=[AgentCapability.COORDINATION, AgentCapability.PLANNING, AgentCapability.COMMUNICATION],
        react_agent=react_agent
    )


# Enhanced integration with existing ReactAgent
class MultiAgentReactAgent(ReactAgent):
    """Enhanced ReactAgent that can leverage multiple specialized agents as tools"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orchestrator = MultiAgentOrchestrator()
        self.multi_agent_tools_enabled = False
    
    def enable_multi_agent_tools(self):
        """Enable multi-agent tools integration"""
        if not self.multi_agent_tools_enabled:
            # Create specialized agents
            researcher = create_researcher_agent()
            analyst = create_analyst_agent()
            coder = create_coder_agent()
            
            # Register with orchestrator
            self.orchestrator.register_agent(researcher)
            self.orchestrator.register_agent(analyst)
            self.orchestrator.register_agent(coder)
            
            # Convert agents to tools
            researcher_tool = AgentTool(researcher, "researcher")
            analyst_tool = AgentTool(analyst, "analyst")
            coder_tool = AgentTool(coder, "coder")
            
            # Register tools
            self.tool_manager.register_tool(researcher_tool)
            self.tool_manager.register_tool(analyst_tool)
            self.tool_manager.register_tool(coder_tool)
            
            self.multi_agent_tools_enabled = True
            logger.info("Multi-agent tools enabled for ReactAgent")
    
    async def run(self, query: str, session_id: str = None, **kwargs) -> Dict[str, Any]:
        """Enhanced run method with multi-agent capability"""
        
        # Enable multi-agent tools if not already enabled
        if not self.multi_agent_tools_enabled:
            self.enable_multi_agent_tools()
        
        # Check if we should use multi-agent orchestration directly
        if await self._should_use_orchestrator(query):
            return await self.orchestrator.process_query(query)
        else:
            # Use normal ReactAgent flow (which now has agent tools available)
            return await super().run(query, session_id, **kwargs)
    
    async def _should_use_orchestrator(self, query: str) -> bool:
        """Determine if query should use direct orchestrator"""
        # Use orchestrator for complex multi-step queries
        orchestrator_keywords = [
            "complex analysis", "comprehensive research", "multi-step process",
            "research and analyze", "coordinate multiple", "collaborative task"
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in orchestrator_keywords)
    
    def get_multi_agent_stats(self) -> Dict[str, Any]:
        """Get multi-agent system statistics"""
        return self.orchestrator.get_system_stats()


# Example usage and testing
async def demo_multi_agent_system():
    """Demonstrate the multi-agent system"""
    
    print("🚀 Initializing Multi-Agent System Demo")
    
    # Create orchestrator
    orchestrator = MultiAgentOrchestrator()
    
    # Create specialized agents
    researcher = create_researcher_agent("researcher_001")
    analyst = create_analyst_agent("analyst_001")
    coder = create_coder_agent("coder_001")
    coordinator = create_coordinator_agent("coordinator_001")
    
    # Register agents
    orchestrator.register_agent(researcher)
    orchestrator.register_agent(analyst)
    orchestrator.register_agent(coder)
    orchestrator.register_agent(coordinator)
    
    print(f"✅ Registered {len(orchestrator.agents)} agents")
    
    # Test queries
    test_queries = [
        "Research information about Python async programming",
        "Analyze the performance of different sorting algorithms",
        "Write a Python function to calculate fibonacci numbers",
        "Research machine learning trends and then analyze the findings"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test Query {i}: {query}")
        
        result = await orchestrator.process_query(query)
        
        print(f"✅ Success: {result.get('success', False)}")
        print(f"🤖 Agent: {result.get('agent_id', 'Unknown')}")
        print(f"⏱️ Time: {result.get('execution_time', 0):.2f}s")
        
        if result.get('participating_agents'):
            print(f"🤝 Collaborated with: {result['participating_agents']}")
    
    # Show system statistics
    print("\n📊 System Statistics:")
    stats = orchestrator.get_system_stats()
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    # Run the demonstration
    asyncio.run(demo_multi_agent_system())