# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

giftolottie is a Python tool that converts GIF animations to Telegram sticker format (TGS/Lottie). The project reads GIF files, processes them pixel-by-pixel to extract colored rectangles, and exports them as compressed Lottie animations.

**Important Note**: The README indicates this tool is largely obsolete since Telegram supports WebM stickers as of 2022.

## Usage

```bash
python3 read.py input.gif output.tgs
```

## Dependencies

Install dependencies with:
```bash
pip3 install -r requirements.txt
```

External dependency: requires `gifsicle` to be installed on the system.

## Architecture

The codebase follows a modular pipeline architecture:

1. **Main Pipeline** (`read.py`): 
   - Uses `gifsicle` to unpack GIF frames
   - Processes frames with `vendor.gif2numpy` to extract pixel data
   - Deduplicates color palette
   - Converts pixels to rectangle shapes using `utils/rect.py`
   - Merges consecutive identical rectangles for compression
   - Scales output to 512px using `utils/scale.py`
   - Exports to TGS format using `export/tgs.py`

2. **Utils Module**:
   - `utils/rect.py`: Converts pixel arrays to rectangle coordinates by color
   - `utils/scale.py`: Scales shape coordinates by a ratio

3. **Export Module**:
   - `export/svg.py`: Exports shapes to SVG format (for debugging)
   - `export/tgs.py`: Core TGS/Lottie export with JSON structure generation and gzip compression

4. **Vendor**: Contains modified `gif2numpy` library for GIF parsing

## Key Technical Details

- Output is always scaled to 512x512px
- TGS format uses 60 FPS with 3-second max duration
- Pink color (254, 0, 254) is treated as transparent
- Rectangle merging optimization combines consecutive identical frames
- Lottie JSON structure is built from scratch without After Effects dependency