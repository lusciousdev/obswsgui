import typing


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

def ms_to_hms(ms : float) -> typing.Tuple[int, int, int, float]:
  rem, ms = divmod(ms, 1000)
  rem, s = divmod(rem, 60)
  h, m = divmod(rem, 60)
  
  return int(h), int(m), int(s), ms

def hms_to_ms(h : int, m : int, s : int, ms : float = 0.0) -> float:
  return (60 * 60 * 1000 * h) + (60 * 1000 * m) + (1000 * s) + ms