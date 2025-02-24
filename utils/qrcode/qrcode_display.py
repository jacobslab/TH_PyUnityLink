import tkinter as tk
import qrcode
from PIL import Image, ImageTk
import time

class QRCodeDisplay:
    def __init__(self, root):
        self.root = root
        self.root.title("QR Code Display")
        self.root.state("zoomed")  # Start in maximized mode
        
        self.root.configure(bg="white")  
        
        # Frame to hold QR code and handle resizing
        self.frame = tk.Frame(self.root, bg="white")
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Create label to hold QR code
        self.label = tk.Label(self.frame, bg="white")
        self.label.pack()

        # Bind resizing feature
        self.root.bind("<Configure>", self.update_qr)
        
        # Exit on 'Esc' key
        self.root.bind("<Escape>", lambda e: self.root.destroy())

    def generate_qr(self, size):
        """Generate a QR code with the current time and given size."""
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        qr = qrcode.QRCode(border=1)
        qr.add_data(current_time)
        qr.make(fit=True)

        # Resize QR code
        qr_img = qr.make_image(fill="black", back_color="white").convert("RGB")
        qr_img = qr_img.resize((size, size), Image.Resampling.LANCZOS)

        return ImageTk.PhotoImage(qr_img)

    def update_qr(self, event=None):
        """Update and center the QR code on window resize."""
        screen_width = self.root.winfo_width()
        screen_height = self.root.winfo_height()
        
        # Determine the new QR size (square)
        qr_size = min(screen_width, screen_height) - 100  # Adjust with margin
        
        # Generate new QR image
        qr_image = self.generate_qr(qr_size)
        self.label.config(image=qr_image)
        self.label.image = qr_image
        
        self.label.place(x=(screen_width - qr_size) // 2,
                         y=(screen_height - qr_size) // 2)

# Test
if __name__ == "__main__":
    root = tk.Tk()
    qr_display = QRCodeDisplay(root)
    root.mainloop()
