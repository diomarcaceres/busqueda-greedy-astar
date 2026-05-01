import heapq
from PIL import Image, ImageDraw, ImageFont



MAZE_STRING = """\
###########################
#A    #     #             #
# ### # ### # ########### #
# #   #   # #           # #
# # ##### # ########### # #
# #     # #     #       # #
# ##### # ##### # ####### #
#     # #     # #         #
##### # ##### # # #########
#     #       # #         #
# ########### # ######### #
#           # #         # #
########### # ######### # #
#           #       #   # #
# ########### ##### # ### #
#           #     # #     #
########### ##### # ##### #
#         #     # #     # #
# ####### ##### # ##### # #
#       #       #       #B#
###########################"""



class Node():
    def __init__(self, state, parent, action, g=0, h=0):
        self.state  = state   
        self.parent = parent  
        self.action = action  
        self.g = g            
        self.h = h            

    def f(self):
        """f(n) = g(n) + h(n)  — usado por A*"""
        return self.g + self.h

    def __lt__(self, other):
        return self.f() < other.f()



class GreedyFrontier():
    """
    Greedy Best-First Search
    Prioridad = h(n)  →  solo la distancia estimada al objetivo.
    No garantiza el camino más corto, pero suele ser muy rápido.
    """
    def __init__(self):
        self.frontier = []
        self._counter = 0

    def add(self, node):
        heapq.heappush(self.frontier, (node.h, self._counter, node))
        self._counter += 1

    def contains_state(self, state):
        return any(node.state == state for _, _, node in self.frontier)

    def empty(self):
        return len(self.frontier) == 0

    def remove(self):
        if self.empty():
            raise Exception("Frontera vacía")
        _, _, node = heapq.heappop(self.frontier)
        return node


class AStarFrontier():
    """
    A* Search
    Prioridad = f(n) = g(n) + h(n)
    Combina costo real + heurística → garantiza el camino óptimo
    siempre que h(n) sea admisible (nunca sobreestima).
    """
    def __init__(self):
        self.frontier = []
        self._counter = 0

    def add(self, node):
        heapq.heappush(self.frontier, (node.f(), self._counter, node))
        self._counter += 1

    def contains_state(self, state):
        return any(node.state == state for _, _, node in self.frontier)

    def empty(self):
        return len(self.frontier) == 0

    def remove(self):
        if self.empty():
            raise Exception("Frontera vacía")
        _, _, node = heapq.heappop(self.frontier)
        return node



class Maze():

    def __init__(self):
        contents = MAZE_STRING

        contents = contents.splitlines()
        self.height = len(contents)
        self.width  = max(len(line) for line in contents)

        self.walls = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                try:
                    if contents[i][j] == "A":
                        self.start = (i, j)
                        row.append(False)
                    elif contents[i][j] == "B":
                        self.goal = (i, j)
                        row.append(False)
                    elif contents[i][j] == " ":
                        row.append(False)
                    else:
                        row.append(True)
                except IndexError:
                    row.append(False)
            self.walls.append(row)

        self.solution = None

    # ── Heurística: Distancia Manhattan ───────────────────────
    def heuristic(self, state):
        """
        Distancia Manhattan entre 'state' y el objetivo.
        h(n) = |fila_n - fila_meta| + |col_n - col_meta|
        Es admisible porque nunca sobreestima el costo real.
        """
        (r1, c1) = state
        (r2, c2) = self.goal
        return abs(r1 - r2) + abs(c1 - c2)

    def print(self):
        solution = self.solution[1] if self.solution is not None else None
        print()
        for i, row in enumerate(self.walls):
            for j, col in enumerate(row):
                if col:
                    print("█", end="")
                elif (i, j) == self.start:
                    print("A", end="")
                elif (i, j) == self.goal:
                    print("B", end="")
                elif solution is not None and (i, j) in solution:
                    print("*", end="")
                else:
                    print(" ", end="")
            print()
        print()

    def neighbors(self, state):
        row, col = state
        candidates = [
            ("up",    (row - 1, col)),
            ("down",  (row + 1, col)),
            ("left",  (row, col - 1)),
            ("right", (row, col + 1)),
        ]
        return [
            (action, (r, c))
            for action, (r, c) in candidates
            if 0 <= r < self.height and 0 <= c < self.width and not self.walls[r][c]
        ]

    def solve(self, method):
        """
        Resuelve con 'greedy' o 'astar'.
        Registra la distancia Manhattan inicial para mostrarla.
        """
        self.num_explored = 0
        h_start = self.heuristic(self.start)
        self.distancia_inicial = h_start   # ← distancia Manhattan desde A hasta B

        start = Node(state=self.start, parent=None, action=None, g=0, h=h_start)

        if method == "greedy":
            frontier = GreedyFrontier()
        elif method == "astar":
            frontier = AStarFrontier()
        else:
            raise Exception(f"Método no reconocido: {method}")

        frontier.add(start)
        self.explored = set()

        while True:
            if frontier.empty():
                raise Exception("Sin solución")

            node = frontier.remove()
            self.num_explored += 1

            if node.state == self.goal:
                actions, cells = [], []
                while node.parent is not None:
                    actions.append(node.action)
                    cells.append(node.state)
                    node = node.parent
                actions.reverse()
                cells.reverse()
                self.solution = (actions, cells)
                return

            self.explored.add(node.state)

            for action, state in self.neighbors(node.state):
                if not frontier.contains_state(state) and state not in self.explored:
                    g_new = node.g + 1
                    h_new = self.heuristic(state)
                    child = Node(state=state, parent=node, action=action,
                                 g=g_new, h=h_new)
                    frontier.add(child)

    def output_image(self, filename, label="", stats=""):
        """Genera imagen PNG con colores por rol y encabezado informativo."""
        cell_size   = 36
        cell_border = 2
        header_h    = 72

        img_w = self.width  * cell_size
        img_h = self.height * cell_size + header_h

        img  = Image.new("RGBA", (img_w, img_h), (20, 20, 30))
        draw = ImageDraw.Draw(img)

        draw.rectangle([(0, 0), (img_w, header_h - 4)], fill=(30, 30, 45))
        try:
            f_title = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 17)
            f_stats = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except Exception:
            f_title = ImageFont.load_default()
            f_stats = f_title

        draw.text((10, 6),  label, fill=(255, 220, 80),  font=f_title)
        draw.text((10, 34), stats, fill=(180, 200, 255), font=f_stats)

        solution = self.solution[1] if self.solution is not None else None

        for i, row in enumerate(self.walls):
            for j, col in enumerate(row):
                x0 = j * cell_size + cell_border
                y0 = i * cell_size + cell_border + header_h
                x1 = (j + 1) * cell_size - cell_border
                y1 = (i + 1) * cell_size - cell_border + header_h

                if col:
                    fill = (35, 35, 50)
                elif (i, j) == self.start:
                    fill = (50, 180, 255)
                elif (i, j) == self.goal:
                    fill = (50, 230, 80)
                elif solution is not None and (i, j) in solution:
                    fill = (255, 220, 40)
                elif (i, j) in self.explored:
                    fill = (180, 80, 80)
                else:
                    fill = (220, 225, 240)

                draw.rectangle([(x0, y0), (x1, y1)], fill=fill)

        # Leyenda
        legend_y = img_h - cell_size - 4
        items = [
            ((50, 180, 255), "Inicio (A)"),
            ((50, 230, 80),  "Meta (B)"),
            ((255, 220, 40), "Solución"),
            ((180, 80, 80),  "Explorado"),
        ]
        x_cur = 10
        try:
            f_leg = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
        except Exception:
            f_leg = ImageFont.load_default()

        for color, text in items:
            draw.rectangle([(x_cur, legend_y + 8), (x_cur + 14, legend_y + 22)],
                           fill=color)
            draw.text((x_cur + 18, legend_y + 7), text,
                      fill=(220, 220, 220), font=f_leg)
            x_cur += 110

        img.save(filename)



methods = {
    "greedy": "Greedy Best-First Search",
    "astar":  "A* Search",
}

print("\n" + "═" * 58)
print("   BÚSQUEDAS INFORMADAS: GREEDY  y  A*")
print("   Heurística: Distancia Manhattan  h(n) = |Δfila| + |Δcol|")
print("═" * 58)

for key, label in methods.items():
    print(f"\n{'─'*58}")
    print(f"  {label}")
    print(f"{'─'*58}")

    m = Maze()
    m.solve(method=key)

    steps    = len(m.solution[0])
    explored = m.num_explored
    dist_ini = m.distancia_inicial

    print(f"  Distancia Manhattan inicial (h inicio→meta) : {dist_ini}")
    print(f"  Estados explorados                          : {explored}")
    print(f"  Pasos en la solución encontrada             : {steps}")
    print(f"  Costo real del camino (g)                   : {steps}")

    if key == "astar":
        print(f"  f(inicio) = g(0) + h({dist_ini})                    = {dist_ini}")

    print("\n  Solución en el mapa ('*' = camino):")
    m.print()

    stats_str = (
        f"Distancia Manhattan inicial: {dist_ini}  |  "
        f"Explorados: {explored}  |  Pasos: {steps}"
    )
    fname = f"maze_{key}.png"
    m.output_image(fname, label=label, stats=stats_str)
    print(f"  Imagen guardada: {fname}")

print("\n" + "═" * 58)
print("  COMPARATIVA FINAL")
print("═" * 58)
print(f"  {'Algoritmo':<30} {'Dist.Manhattan':>14} {'Explorados':>11} {'Pasos':>7}")
print(f"  {'─'*30} {'─'*14} {'─'*11} {'─'*7}")

for key, label in methods.items():
    m2 = Maze()
    m2.solve(method=key)
    print(f"  {label:<30} {m2.distancia_inicial:>14} "
          f"{m2.num_explored:>11} {len(m2.solution[0]):>7}")

print()
