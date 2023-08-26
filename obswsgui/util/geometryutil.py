import math

class Coords:
  x : float = 0.0
  y : float = 0.0
  
  def __init__(self, x : float = 0, y : float = 0):
    self.x = x
    self.y = y
    
  def add(self, other : 'Coords') -> None:
    self.x += other.x
    self.y += other.y
    
  def div(self, divisor : float) -> None:
    self.x /= divisor
    self.y /= divisor
    
  def mult(self, multiplier : float) -> None:
    self.x *= multiplier
    self.y *= multiplier
    
  def angle(self) -> float:
    if self.x == 0:
      angle = (math.pi / 2.0) if self.y >= 0 else (3.0 * math.pi / 2.0)
    else:
      angle = math.atan(self.y / self.x)
    
    if self.x < 0:
      angle += math.pi
      
    return angle
    
  def rotate(self, a : float) -> None:
    r = math.sqrt(math.pow(self.x, 2) + math.pow(self.y, 2))
    currangle = self.angle()
    
    newangle = currangle + a
    
    self.x = r * math.cos(newangle)
    self.y = r * math.sin(newangle)
    
  def magnitude(self) -> float:
    return math.sqrt(math.pow(self.x, 2) + math.pow(self.y, 2))
    
  def __repr__(self) -> str:
    return f"({self.x:.2f}, {self.y:.2f})"
  
  def __add__(self, other : 'Coords') -> 'Coords':
    return Coords(self.x + other.x, self.y + other.y)
  
  def __sub__(self, other : 'Coords') -> 'Coords':
    return Coords(self.x - other.x, self.y - other.y)
  
  def __floordiv__(self, divisor : int) -> 'Coords':
    return Coords(self.x // divisor, self.y // divisor)
  
  def __truediv__(self, divisor : float) -> 'Coords':
    return Coords(self.x / divisor, self.y / divisor)
  
  def __mult__(self, multiplier : float) -> 'Coords':
    return Coords(self.x * multiplier, self.y * multiplier)
  
  def __copy__(self) -> 'Coords':
    return Coords(self.x, self.y)
  
class Polygon:
  __points = []
  
  def __init__(self, *points : Coords):
    self.__points = []
    for point in points:
      self.__points.append(Coords(point[0], point[1]))
      
  def point(self, index : int) -> Coords:
    return self.__points[index]
  
  def points(self) -> list:
    return self.__points
  
  def set_point(self, index : int, coords : Coords) -> None:
    self.__points[index] = coords
    
  def size(self) -> int:
    return len(self.__points)

  def to_array(self) -> list:
    arr = []
    for point in self.__points:
      arr.extend([point.x, point.y])
    return arr
  
  def minx(self) -> float:
    return min([c.x for c in self.__points])
  
  def maxx(self) -> float:
    return max([c.x for c in self.__points])
  
  def miny(self) -> float:
    return min([c.y for c in self.__points])
  
  def maxy(self) -> float:
    return max([c.y for c in self.__points])

  def centroid(self) -> Coords:
    c = Coords(0, 0)
    n = len(self.__points)
    
    area = 0
    for i in range(n):
      v0 = self.point(i)
      v1 = self.point((i + 1) % n)
      
      a = v0.x * v1.y - v0.y * v1.x
      area += (a / 2.0)
      
      c.x += (v0.x + v1.x) * a
      c.y += (v0.y + v1.y) * a
      
    c.x /= (6.0 * area)
    c.y /= (6.0 * area)
    
    return c
    
  def __repr__(self):
    return ", ".join([str(p) for p in self.__points])
  
def distance_from_line(l0 : Coords, l1 : Coords, p : Coords) -> float:
  numerator = abs((l1.x - l0.x) * (l0.y - p.y) - (l0.x - p.x) * (l1.y - l0.y))
  denominator = math.sqrt(math.pow(l1.x - l0.x, 2) + math.pow(l1.y - l0.y, 2))
  dist = numerator / denominator
  return dist

def distance_from_segment(l0 : Coords, l1 : Coords, p : Coords) -> float:
  seglen = distance(l0, l1)
  if seglen == 0:
    return distance(l0, p)
  
  t = ((p.x - l0.x) * (l1.x - l0.x) + (p.y - l0.y) * (l1.y - l0.y)) / math.pow(seglen, 2)
  t = max(0, min(1, t))
  return distance(p, Coords(l0.x + t * (l1.x - l0.x), l0.y + t * (l1.y - l0.y)))

def distance(a : Coords, b : Coords) -> float:
  return math.sqrt(math.pow(a.x - b.x, 2) + math.pow(a.y - b.y, 2))

def on_segment(l0 : Coords, l1 : Coords, p : Coords, epsilon : float = 0.01) -> bool:
  return abs(distance(l0, p) + distance(p, l1) - distance(l0, l1)) < epsilon

def quadrant(p : Coords) -> int:
  if p.x >= 0 and p.y >= 0:
    return 1
  elif p.x < 0 and p.y >= 0:
    return 2
  elif p.x < 0 and p.y < 0:
    return 3
  else:
    return 4

def edge_contribution(v0 : Coords, v1 : Coords, p : Coords) -> int:  
  this = Coords(v0.x - p.x, v0.y - p.y)
  next = Coords(v1.x - p.x, v1.y - p.y)
  
  dist = Coords(next.x - this.x, next.y - this.y)
  det = dist.x * this.y - dist.y * this.x
  
  qthis = quadrant(this)
  qnext = quadrant(next)
  
  if qthis == qnext:
    return 0
  elif qnext - 1 == (qthis % 4):
    return 1
  elif qthis - 1 == (qnext % 4):
    return -1
  elif det <= 0:
    return 2
  else:
    return -2

def point_in_polygon(polygon : Polygon, p : Coords) -> bool:
  w = 0.0
  n = len(polygon.points())
  
  if n < 3:
    return False
  
  for i in range(n):
    v0 = polygon.point(i)
    v1 = polygon.point((i + 1) % n)
    
    if on_segment(v0, v1, p):
      return True
    
    w += edge_contribution(v0, v1, p)
        
  return w != 0