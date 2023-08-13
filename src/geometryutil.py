import math

class Coords:
  x = 0
  y = 0
  
  def __init__(self, x = 0, y = 0):
    self.x = x
    self.y = y
    
  def __repr__(self):
    return f"({self.x}, {self.y})"
  
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
  
  def set_point(self, index : int, coords : Coords):
    self.__points[index] = coords
    
  def size(self):
    return len(self.__points)

  def to_array(self) -> list:
    arr = []
    for point in self.__points:
      arr.extend([point.x, point.y])
    return arr
  
  def minx(self):
    return min([c.x for c in self.__points])
  
  def maxx(self):
    return max([c.x for c in self.__points])
  
  def miny(self):
    return min([c.y for c in self.__points])
  
  def maxy(self):
    return max([c.y for c in self.__points])
  
def distance_from_line(l1 : Coords, l2 : Coords, p : Coords):
  numerator = abs((l2.x - l1.x) * (l1.y - p.y) - (l1.x - p.x) * (l2.y - l1.y))
  denominator = math.sqrt(math.pow(l2.x - l1.x, 2) + math.pow(l2.y - l1.y, 2))
  dist = numerator / denominator
  print(f"Distance: {dist}")
  return dist