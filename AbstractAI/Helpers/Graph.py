from AbstractAI.Helpers.DirtyLazyProp import dirtyable, lazy_property
from dataclasses import dataclass, field
from typing import List, Set

@dataclass
class Node:
	name: str
	edges: List["Edge"] = field(default_factory=list)

@dataclass
class Edge:
	name: str
	in_node: Node
	out_node: Node
	weight: float = 1.0

@dataclass
@dirtyable
class Graph:
	name: str
	nodes: Set[Node] = field(default_factory=set)
	edges: Set[Edge] = field(default_factory=set)
	
	def add_node(self, node:Node):
		if node not in self.nodes:
			self.nodes.append(node)
			for edge in node.edges:
				self.add_edge(edge)
			self._dirty()
	
	def add_edge(self, edge:Edge):
		if edge not in self.edges:
			self.edges.append(edge)
			self.add_node(edge.in_node)
			self.add_node(edge.out_node)
			self._dirty()
	
	@lazy_property
	def input_nodes(self) -> Set[Node]:
		input_nodes = set()
		for node in self.nodes:
			if len(node.edges) == 0:
				input_nodes.add(node)
			else:
				if all(edge.in_node is not node for edge in node.edges):
					input_nodes.add(node)
		return input_nodes
	
	@lazy_property
	def output_nodes(self) -> Set[Node]:
		output_nodes = set()
		for node in self.nodes:
			if len(node.edges) == 0:
				output_nodes.add(node)
			else:
				if all(edge.out_node is not node for edge in node.edges):
					output_nodes.add(node)
		return output_nodes