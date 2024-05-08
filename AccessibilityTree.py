from playwright._impl._cdp_session import CDPSession
import Settings


class AccessibilityTree:
    full_tree = []
    client = None
    chunk_index = 0
    chunk_length = 200

    def __init__(self,c:CDPSession,snapshot):
        self.client = c
        self.load_tree(snapshot)
        self.chunk_index = 0

    #DO NOT USE get_node_children if the node has a children element instead use node["children"]
    def get_node_children(self, node):
        nodeId = node["nodeId"]
        all_children = self.client.send('Accessibility.getChildAXNodes', {
            'id': nodeId,
        })['nodes']

        return [
            child
            for child in all_children
            if "backendDOMNodeId" in child
            and "backendDOMNodeId" in node
            and child["backendDOMNodeId"] != node["backendDOMNodeId"]
        ]

    def getNodeByDomId(self,id,children=None):
        #Set default value to full tree
        if children is None:
            children = self.full_tree
        #recursively iterate through the tree until you find the node by its ID
        for child in children:
            if child["backendDOMNodeId"] in [id, int(id)]:
                return child
            #Search the children if they exist
            if "children" in child:
                output = self.getNodeByDomId(id,child["children"])
                if output is not None:
                    return output
        return None


    #Expand the node and get its children
    def expand_node(self,id):
        node = self.getNodeByDomId(id)
        if node is not None:
            node["expanded"] = True
            node["children"] = self.get_node_children(node)
        return "Expanded Node"

    #Checks if a node is focusable
    def is_focusable(self,node):
        is_focusable = False
        if "properties" in node:
            for prop in node["properties"]:
                if prop["name"] == "focusable":
                    is_focusable = prop["value"]["value"]
                    break
        return is_focusable

    #Outputs the entire tree in a chunk
    def to_string(self,children,inline=0):
        out_string = ""
        for child in children:
            out_string += ("    " * inline)
            is_focusable = self.is_focusable(child)
            if not child["ignored"] and "role" in child and (is_focusable or not Settings.OnlyFocusable):
                node_line = ""
                if "backendDOMNodeId" in child:
                   #out_string += "id: " + str(child["backendDOMNodeId"]) + " "
                    node_line += str(child["backendDOMNodeId"]) + " "
                #out_string += "role: " + child["role"]["value"] + " "
                node_line += child["role"]["value"] + " "
                if "name" in child:
                    #out_string += "name: " + child["name"]["value"] + " "
                    node_line += child["name"]["value"] + " "
            
                #out_string += "focusable: " + str(is_focusable)
                out_string += node_line[:Settings.Max_Node_Size].replace("\n"," ")
                out_string += "\n"
            if "expanded" in child and child["expanded"] and "children" in child:
                out_string += self.to_string(child["children"],inline+1)
        return out_string
    
    #Update the tree based on accessibility snapshot
    def update_tree(self,page):
        snapshot = page.accessibility.snapshot()
        self.load_tree(snapshot)

    #Outputs tree
    def get_output(self):
        full_string = self.to_string(self.full_tree)
        output_string = ""
        output_lines = full_string.split('\n')
        index_start = self.chunk_index*self.chunk_length
        if index_start > len(output_lines):
            index_start = 0
            self.chunk_index = 0
            print("End of page reached")
        lastLine = 0
        for i in range(index_start,min([len(output_lines)-index_start,self.chunk_length+index_start])):
            output_string += output_lines[i] + '\n'
            lastLine = i

        output_string += "\n +" + str(len(output_lines)-lastLine) + " ...Nodes remaining"

        return output_string
    
    #Recursively iterate through the children of a node and its descendents
    def get_all_children(self,node):
        children = self.get_node_children(node)
        if "expanded" not in node:
            node["expanded"] = False
        for child in children:

            childs_children = self.get_all_children(child)
            child["children"] = childs_children

        return children

    #Converts a snapshot into a list of nodes
    def getStartPage(self, accessibility_snapshot):
        start_page = []
        rootAxNode = self.client.send('Accessibility.getRootAXNode')
        all_nodes = self.client.send("Accessibility.getFullAXTree")["nodes"]

        for tree_node in accessibility_snapshot["children"]:
            #  new_node = client.send("Accessibility.queryAXTree",{'nodeId': str(rootNodeID), 'accessibleName': node["name"], 'role': node["role"]})

            # Filter the nodes based on name and role
            '''matching_nodes = [node for node in full_tree.get("nodes", [])
                              if node.get("name", {}).get("value") == tree_node["name"]
                              and node.get("role", {}).get("value") == tree_node["role"]]
            '''
            #matching_nodes = []
            matching_node = None
            for i in range(len(all_nodes)):
                node = all_nodes[i]
                node_role = node["role"]["value"]
                if "name" in node:
                    node_name = node["name"]["value"]
                    #if node_role == tree_node["role"] and node_name == tree_node["name"]:
                    if node_name == tree_node["name"] and "backendDOMNodeId" in node:
                        copy_of_node = node.copy()
                        del all_nodes[i]
                        matching_node = copy_of_node
                        break


            if matching_node is not None:
                new_node = matching_node
                start_page.append(new_node)


        #print(len(all_nodes["nodes"]))

        return start_page

    #Shallow search for all focusable children
    def get_focusable_children(self,node):
        all_children = self.get_node_children(node)
        focusable_children = []
        for child in all_children:
            if is_focusable := self.is_focusable(child):
                focusable_children.append(child)
        return focusable_children

    #Loads the tree based on snapshot
    def load_tree(self,snapshot):
        start_page = []

        if Settings.UseFullTree:
            start_page = self.client.send("Accessibility.getFullAXTree")["nodes"]
        else:
            start_page = self.getStartPage(snapshot)

        if self.full_tree is not None:
            self.full_tree.clear()
        for child in start_page:


            #child["children"] = self.get_all_children(child)
            is_focusable = self.is_focusable(child)
            if not is_focusable and Settings.OnlyFocusable:
                continue
            child["expanded"] = True
            if not is_focusable and "name" in child:
                focusable_children = self.get_focusable_children(child)
                for focus_child in focusable_children:
                    if "name" in focus_child and focus_child["name"]["value"] == child["name"]["value"]:
                        child = focus_child
                        break
            self.full_tree.append(child)
