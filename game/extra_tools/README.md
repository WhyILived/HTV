# Sprite Processing Tools

## Collision Process (`collision_process.py`)
Finds the **largest** pink color group and solidifies it.

```bash
python collision_process.py input.png -o output.png -c 234 0 255
```

## Anti-Collision Process (`anti_collision_process.py`)
Finds **all** pink color groups above a minimum pixel threshold and solidifies them.

```bash
python anti_collision_process.py input.png -o output.png -c 234 0 255
python anti_collision_process.py input.png -m 500 -c 234 0 255  # Find smaller groups
```

## GIF Creator (`create_gif.py`)
Creates animated GIFs from multiple images.

```bash
python create_gif.py images/ -o animation.gif -d 500 -l 0
```

## Options
- `-o, --output`: Output file path
- `-c, --color R G B`: Solid color (default: 255 255 255)
- `-t, --tolerance`: Color tolerance (default: 100)
- `-m, --min-pixels`: Minimum pixels for anti-collision (default: 1000)
- `-d, --duration`: Frame duration in ms for GIF (default: 500)
- `-l, --loop`: Loop count for GIF (default: 0 = infinite)
