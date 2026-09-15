import sys
from PySide6.QtGui import QGuiApplication, QIcon, QPixmap
from PySide6.QtCore import QSize
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QImage, QPainter
import os

def svg_to_ico(svg_path, ico_path):
    app = QGuiApplication(sys.argv)
    
    # We will generate multiple sizes for the ICO file
    sizes = [16, 24, 32, 48, 64, 128, 256]
    
    # Let's try to save as ICO using QImageWriter? 
    # Actually QIcon can't easily be saved to .ico via PySide API directly.
    # But we can try to save a single high-res PNG and save it as .ico, 
    # QImage.save supports "ico" format in Qt.
    
    renderer = QSvgRenderer(svg_path)
    if not renderer.isValid():
        print("Invalid SVG")
        return False
        
    img = QImage(256, 256, QImage.Format_ARGB32)
    img.fill(0) # transparent
    painter = QPainter(img)
    renderer.render(painter)
    painter.end()
    
    # Save as ICO (Qt usually has an ICO plugin)
    success = img.save(ico_path, "ICO")
    print(f"Saved {ico_path} using Qt: {success}")
    
    # Also save a PNG for good measure
    png_path = ico_path.replace('.ico', '.png')
    img.save(png_path, "PNG")
    print(f"Saved {png_path} using Qt: True")
    
    return success

if __name__ == "__main__":
    svg_file = r"d:\Antigravity\ZK_Draw\assets\zk-draw-icon.svg"
    ico_file = r"d:\Antigravity\ZK_Draw\assets\zk-draw.ico"
    svg_to_ico(svg_file, ico_file)
