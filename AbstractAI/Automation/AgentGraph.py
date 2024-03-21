from AbstractAI.Helpers.Graph import Graph, Node, Edge
from .Conditions import Condition
from .Agents import Agent

from dataclasses import dataclass, field

@dataclass
def AgentNode(Node):
	agent: Agent

@dataclass
def ConditionEdge(Edge):
	condition: Condition

@dataclass
def AgentGraph(Graph):
	def add_agent(self, agent:Agent):
		agent_node = AgentNode(agent=agent)
		self.add_node(agent_node)
		return agent_node
	
	def add_node(self, node:AgentNode):
		super().add_node(node)
	
	def add_edge(self, edge:ConditionEdge):
		super().add_edge(edge)