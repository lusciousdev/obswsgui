
def obs_to_color(color : int) -> str:
  chex = hex(color).lstrip("0x").rstrip("L")
  if len(chex) <= 6:
    chex = chex.rjust(6, "0")
  else:
    chex = chex[-6:]
    
  r = chex[4:]
  g = chex[2:4]
  b = chex[:2]
  colorstr = f"#{r}{g}{b}"
  return colorstr

def color_to_obs(color : str) -> int:
  digits = color.lstrip("#")
  r = digits[:2]
  g = digits[2:4]
  b = digits[4:]
  
  colorhex = f"0x{b}{g}{r}"
  colordec = int(colorhex, 16)
  return colordec