import os
import sys
import requests
import pygame
import pygame_gui
from pygame.math import Vector2
import webbrowser
    

COLOR_PALETTE = {
    "leaf_tree": (230, 230, 230),
    "leaf_blob": (255, 87, 51),
    "stick": (230, 230, 230),
    "background": (20, 20, 20)
}

screen_width = 1840
screen_height = 920

logo = pygame.Surface((20, 20))
logo.fill((255, 255, 255, 0))
pygame.draw.circle(logo, COLOR_PALETTE["leaf_tree"], (10, 10), 10)
pygame.draw.circle(logo, COLOR_PALETTE["leaf_blob"], (10, 10), 10, 3)

class Menu:
    user = ""
    repo = ""
    branch = "master"
    url = ""
    def __init__(self, manager):
        self.manager = manager
        self.input_line_size = (200, 19)
        self.user_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((0, 0), self.input_line_size), manager=self.manager)

        self.repo_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((0, self.input_line_size[1]), 
            self.input_line_size), manager=self.manager)

        self.branch_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((0, self.input_line_size[1]*2), 
            self.input_line_size), manager=self.manager)

        self.button_size = (100, 20)
        self.generate_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((self.input_line_size[0]/2 - self.button_size[0]/2, 
            self.input_line_size[1] * 3 + self.button_size[1]/2 + 3), 
            self.button_size), text="Generate",
            manager=self.manager)

        self.user_input_label = pygame_gui.elements.UILabel(text="username",
            relative_rect=pygame.Rect((self.input_line_size[0], 2), 
            (self.input_line_size[0]/2, self.input_line_size[1])), manager=self.manager)

        self.repo_input_label = pygame_gui.elements.UILabel(text="repo name",
            relative_rect=pygame.Rect((self.input_line_size[0], self.input_line_size[1] + 4), 
            (self.input_line_size[0]/2, self.input_line_size[1])), manager=self.manager)

        self.branch_input_label = pygame_gui.elements.UILabel(text="branch name",
            relative_rect=pygame.Rect((self.input_line_size[0], self.input_line_size[1] * 2 + 6), 
            (self.input_line_size[0]/2, self.input_line_size[1])), manager=self.manager)

        self.root_json = {"path": "", "type": "tree", "mode": "040000"}

        self.url = ""
        self.json_data = "" 
        self.tree = Tree(Node(self.root_json, Menu.repo))
        self.tree_manager = TreeManager(self.tree)
        self.tree.set_leaves_init_pos(screen_width, screen_height)


    def node_callback(nd):
        webbrowser.open_new("https://github.com/{}/{}/{}/{}/{}"
                    .format(Menu.user, Menu.repo, nd.json["type"], 
                    Menu.branch, nd.json["path"]))
    
    def process_events(self, event):
        if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.generate_button:
                Menu.user = self.user_input.get_text()
                Menu.repo = self.repo_input.get_text()
                Menu.branch = self.branch_input.get_text()
                self.generate_tree()
                

    def generate_tree(self):
        self.url = "https://api.github.com/repos/{}/{}/git/trees/{}?recursive=1".format(
                Menu.user, Menu.repo, Menu.branch)
        self.json_data = requests.get(self.url).json()
        if self.json_data and not ("message" in self.json_data):
            self.tree_manager.kill_buttons()
            self.tree = Tree(Node(self.root_json, Menu.repo))
            for data in self.json_data["tree"]:
                self.tree.paste(Node(data))
            self.tree_manager = TreeManager(self.tree)
            self.tree.set_leaves_init_pos(screen_width, screen_height)
            self.tree_manager.init_buttons(self.manager)

class Node:
    def __init__(self, json, name=None):
        self.json = json
        self.name = json["path"].rpartition("/")[-1] if name is None else name
        self.children = []

        self.pos = Vector2()
        self._level = None

    def add_child(self, node):
        self.children.append(node)

    def get_depth(self):
        if self._level is not None:
            return self._level
        return self.json["path"].count("/") + 1 if self.json["path"] else 0

class Tree:
    def __init__(self, root: Node):
        self.root = root

        self._leaves_with_depth = None
    
    def paste(self, node: Node):
        def inner_iter(relative_root: Node):
            if not relative_root.children:
                relative_root.add_child(node)
                return

            for nd in relative_root.children:
                if (node.json["path"] + "/").startswith(nd.json["path"] + "/"):
                    inner_iter(nd)
                    return

            relative_root.add_child(node)            
        inner_iter(self.root)

    def get_leaves_list(self):
        leaves = []

        def inner_iter(node):
            leaves.append(node)
            for nd in node.children:
                inner_iter(nd)

        inner_iter(self.root)
        return leaves

    def get_leaves_with_depth_list(self):
        if self._leaves_with_depth is not None:
            return self._leaves_with_depth

        leaves = []
        def inner_iter(node, depth):
            leaves.append((node, depth))
            for nd in node.children:
                inner_iter(nd, depth + 1)
                
        inner_iter(self.root, 0)
        return leaves

    def get_max_depth(self):
        return max(self.get_leaves_with_depth_list(), key=lambda item:item[1])[1]

    def get_leaves_on_level(self, level):
        return [nd[0] for nd in list(filter(lambda l: l[1] == level, 
                self.get_leaves_with_depth_list()))]

    def set_leaves_init_pos(self, screen_width, screen_height):
        height_spacing = screen_height / (self.get_max_depth() + 1)
        
        def inner_iter(depth):
            level_nodes = self.get_leaves_on_level(depth)
            level_nodes_amount = len(level_nodes)

            if level_nodes_amount == 0: return

            x_offset = screen_width / (level_nodes_amount + 1)
            y_offset = height_spacing * depth

            for i, nd, in enumerate(level_nodes, start=1):
                nd.pos.xy = x_offset * i, y_offset
            inner_iter(depth + 1)
        
        inner_iter(0)

    def apply(self, f):
        def inner_iter(node):
            f(node)
            for nd in node.children:
                inner_iter(nd)

        inner_iter(self.root)


class TreeManager:
    def __init__(self, tree: Tree):
        self.tree = tree
        self.leaf_buttons = []

    def init_buttons(self, manager):
        default_font = pygame.font.Font(pygame.font.get_default_font(), 20)
        buttons_periodic_offset_dict = {i : True for i in range(self.tree.get_max_depth() + 1)}
        def create_button(node):
            button_size = default_font.size(node.name)
            node_depth = node.get_depth()
            buttons_periodic_offset_dict[node_depth] = not buttons_periodic_offset_dict[node_depth]
            button_pos_shift = Vector2(-button_size[0]/2, -button_size[1] 
                                       * bool(buttons_periodic_offset_dict[node_depth]))

            self.leaf_buttons.append((pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(node.pos + button_pos_shift, button_size), 
                text=node.name,
                manager=manager), node))

        self.tree.apply(create_button)

    def kill_buttons(self):
        for btn in self.leaf_buttons:
            btn[0].kill()

    def process_events(self, event):
        if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
            for btn, nd in self.leaf_buttons:
                if event.ui_element == btn:
                    Menu.node_callback(nd)
                    return

    def draw_leaves(self, surface):
        def draw_leaf(node):
            pygame.draw.circle(surface, COLOR_PALETTE["leaf_tree"], node.pos, 15)
            if node.json["type"] == "tree":
                pygame.draw.circle(surface, COLOR_PALETTE["background"], node.pos, 6)
            else:
                pygame.draw.circle(surface, COLOR_PALETTE["leaf_blob"], node.pos, 15, 5)

        self.tree.apply(draw_leaf)

    def draw_sticks(self, surface):
        def draw_stick(node):
            for nd in node.children:
                pygame.draw.line(surface, COLOR_PALETTE["stick"], node.pos, nd.pos, 2)
                draw_stick(nd)

        self.tree.apply(draw_stick)
    

def main():
     
    pygame.init()
    pygame.font.init()
    pygame.display.set_caption("RepoTree")
    pygame.display.set_icon(logo)
    screen = pygame.display.set_mode((screen_width, screen_height))

    gui_manager = pygame_gui.UIManager((screen_width, screen_height), "default_theme.json")

    screen.fill(COLOR_PALETTE["background"])

    menu = Menu(gui_manager)

    FPS = 60
    clock = pygame.time.Clock()

    running = True
     
    while running:
        time_delta = clock.tick(FPS)/1000.0
        screen.fill(COLOR_PALETTE["background"])
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    menu.tree_manager.process_events(event)

                menu.process_events(event)

            gui_manager.process_events(event)
            
            menu.tree_manager.draw_sticks(screen)
            menu.tree_manager.draw_leaves(screen)

            gui_manager.update(time_delta)

            screen.blit(screen, (0, 0))
            gui_manager.draw_ui(screen)

            pygame.display.flip()
    
    
if __name__=="__main__":
    main()