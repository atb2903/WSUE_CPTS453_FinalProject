# WSU-GPS

Interactive campus map for WSU Pullman that overlays a user-modifiable graph of campus locations and walking routes. A graph traversal algorithm suggests an optimal route between locations. Built with Streamlit + Folium for CPTS 453 (Graph Theory) Spring 2026.

## Requirements

### Python Version

Python version 3.11 or newer is required. Python version 3.12.3 is recommended for strongest guarantee of stability, as development and testing was performed on this version.

### Packages

The following Python packages are required for this program:

- streamlit
- streamlit-folium
- folium
- Pillow

## Running the Program

From the project root, use the terminal and enter `streamlit run src/app.py`

## Using the Program

The program is self-documenting, meaning the features are explained as you use them, but are defined with additional detail below.

### Using the GUI elements

The map may be navigated by zooming and panning. You may zoom the map by scrolling, or by using the +/- buttons in the top left. You may pan the map by holding left-click and dragging the map in your desired direction. 

The buttons and mode switcher are activated by clicking on them when they are active. 

### Current Mode

The modes supported by this program are navigation and editing mode, visible in the mode switcher. The active mode is highlighted in red. The mode may be freely switched at any time.

### Navigation Mode

The program launches in navigation mode with nothing selected. This mode lets you obtain the shortest path between two nodes.

To obtain a shortest path between two nodes, first select them one at a time by clicking on them. Make sure that the tooltip indicating the node's ID number is displayed before clicking, as the program identifies the node in the underlying data structure by extracting the ID from the tooltip. Selected nodes are displayed in WSU Crimson, and unselected nodes are displayed in WSU Gray. If you mistakenly select an incorrect node, you may click the "Deselect" button to clear your selection. Upon selecting 2 nodes, you may then click the "Find Shortest Path" button to find the shortest path between the two nodes, as determined by Dijkstra's shortest path algorithm. The program will then highlight all the nodes and edges along this path in WSU Crimson, leaving all other nodes and edges in WSU Gray. After this, if you wish to find another shortest path, you may click "Deselect" to stop displaying this path and return navigation mode to its starting state.

### Editing Mode

This mode allows you to modify the graph using the same toolset which was used to build it. The features of editing mode are as follows:

#### Saving the Graph

The graph is loaded on program startup from a JSON file. If you wish your changes to be persistent and not disappear upon closing the program, click "Save Graph" to update this JSON to reflect the current state of the graph. 

#### Selecting & Deselecting Nodes & Edges

Ensuring that the tooltip displaying the Node/Edge ID is displayed, as the program identifies it in the underlying data structure by extracting the ID from the tooltip, you may click on a node or edge to select it. Unlike navigation mode, you may only select one node or edge at a time. You may then deselect it by clicking "Deselect". As in navigation mode, selected nodes/edges are displayed in WSU Crimson, and unselected nodes/edges are displayed in WSU Gray

#### Deleting Nodes & Edges

With a node or edge selected, you may click "Delete Selected" to remove it from the graph. Performing this operation on an edge only removes the edge. Performing this operation on a node deletes all edges incident to the node. 

##### Known Bug

Deleting a node with edges attached to it first requires deleting the edges incident to it to avoid leaving orphaned edges in the underlying data structure. However sometimes, with a sufficiently high degree node, this process takes more time than the streamlit library allots to a single update. Streamlit will aggressively rerun, terminating algorithms which take too long to proceed. As such, a sigle delete operation on a sufficiently high degree node will only delete some (or all) of its edges and fail to finish the task. This can be worked around as a user by simply selecting the node and performing a deleting operation multiple times. Fixing this in the code would require significant time optimizing the edge & node lookup algorithms to attempt to get this to run within streamlit's limited execution threshhold, and is not strictly necessary to successfully delete any impacted nodes. 

#### Moving Nodes & Edges

To move a node, first select it. Then click somewhere unoccupied (where there is no tooltip when you hover). The node will be moved to this new location, with all of its edges still attached to it. 

#### Adding Nodes & Edges

To add a new node, click somewhere unoccupied (where there is no tooltip when you hover). A new node will be added to the graph and automatically selected. You may then click "Deselect" to leave it as an isolated node, "Delete Selected" to remove it, click another unoccupied space to add another new node and connect the two new nodes with a new edge, or click an existing node to add an edge between the new node and the existing one. 

To add an edge between two existing nodes, first click one to select it. Then click on the node you would like to add an edge to. A new edge will be added between these two nodes.

Note that duplicate nodes sharing the same space are disallowed, as are self-loops and duplicate edges between two given nodes. These would, at best, increase the computational cost of performing a shortest path computation while providing no benefit or, at worst, make a visually connected portion of a graph be actually disconnected in the underlying data-structure. Attempting to perform an operation that creates any of these conditions will fail to create any changes in the graph.

##### Known Bug

The tech stack used (I suspect the integration between streamlit and folium) created a problem of "ghost clicks", where the program would register repeated input from the user that the user never actually provided. This created destructive, unpredictable behavior in the edit mode. To protect against this, I added a safety system that would detect these "ghost clicks" and reject their input. However, for some reason I wasn't able to figure out, this will occasionally produce a false positive. As best as I can identify, the trigger of this false positive is when trying to create an edge between a node (newly created or existing) on a node which had recently had another edge attached to it such that it would reject the click on the destination node. Although, there must be more to the problem as you can "chain" nodes (create a line of new nodes, each one linking the previously created one) with no issue. 

This is a difficult bug to identify the precise source of, and has 2 functioning workarounds so it was left in place. If I had more time for development (and no additional projects to concern myself with), this would be the first thing I would tackle. The first workaround is to simply connect to a different destination node (or create a new one, if placing a new node), do one more operation elsewhere on the graph, then return to the edge you were trying to create. The second workaround is to deselect the node, select a different node, deselect it, then return to the edge you were trying to create. 