# graph/ — Week 2. You write all of this.

Nothing here is scaffolded on purpose. This directory is the core of the project
and the source of most interview questions.

What lands here in Week 2:

- **Graph construction.** Nodes are buildings plus path intersections; edge
  weights are walking distance computed from coordinates. Decide what an
  intersection node is and why you need them at all — a building-only graph
  gives you straight lines through other buildings.
- **Dijkstra.** Hand-implemented, no library. You will manage the priority queue
  yourself (`heapq`). You built this data structure in CS 225.
- Tests over paths you can verify by hand.

Questions to be able to answer without notes:

- What is a node? What is an edge? How did you choose the weights?
- Why Dijkstra and not A*? What would A* need that you do not have?
- Why not just call the Google Directions API?
- What is the complexity, and what does the priority queue give you?

Cap the graph at 20–30 buildings. Graph size is not a bragging point.
