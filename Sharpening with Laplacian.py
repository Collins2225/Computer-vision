import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
from PIL import Image, ImageTk
import os


class LaplacianSharpenApp:
    """
    Sharpening using the Laplacian

    Common sharpening model:
        S = I - k * Laplacian(I)
    where k controls strength.

    GUI structure (3 frames):
      1) Control Frame (top): Load, Apply, Reset, Save, Strength slider
      2) Input Frame (left): original image
      3) Output Frame (right): sharpened result
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Sharpening using the Laplacian - Image Processing")
        self.root.geometry("1200x650")
        self.root.minsize(1000, 600)

        # Images
        self.original_image = None   # PIL (RGB)
        self.output_image = None     # PIL (RGB)
        self.tk_input = None         # keep references
        self.tk_output = None
        self.loaded_path = None

        # Strength (k)
        self.strength_var = tk.DoubleVar(value=1.0)

        self._build_ui()

        # Redraw previews on resize
        self.input_canvas.bind("<Configure>", lambda e: self._refresh_previews())
        self.output_canvas.bind("<Configure>", lambda e: self._refresh_previews())

    # ---------------- UI ----------------
    def _build_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        # 1) CONTROL FRAME
        self.control_frame = ttk.LabelFrame(self.root, text="Control Frame")
        self.control_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))
        self.control_frame.columnconfigure(10, weight=1)

        ttk.Button(self.control_frame, text="Load Image", command=self.load_image).grid(
            row=0, column=0, padx=8, pady=10, sticky="w"
        )
        ttk.Button(self.control_frame, text="Apply Laplacian Sharpen", command=self.apply_laplacian_sharpen).grid(
            row=0, column=1, padx=8, pady=10, sticky="w"
        )
        ttk.Button(self.control_frame, text="Reset", command=self.reset).grid(
            row=0, column=2, padx=8, pady=10, sticky="w"
        )
        ttk.Button(self.control_frame, text="Save Output", command=self.save_output).grid(
            row=0, column=3, padx=8, pady=10, sticky="w"
        )

        ttk.Separator(self.control_frame, orient="vertical").grid(
            row=0, column=4, sticky="ns", padx=10, pady=6
        )

        ttk.Label(self.control_frame, text="Strength (k):").grid(
            row=0, column=5, padx=(0, 6), pady=10, sticky="w"
        )
        self.strength_scale = ttk.Scale(
            self.control_frame, from_=0.0, to=5.0, variable=self.strength_var, orient=tk.HORIZONTAL, length=220
        )
        self.strength_scale.grid(row=0, column=6, padx=6, pady=10, sticky="w")
        ttk.Label(self.control_frame, text="(0 = no sharpen)").grid(
            row=0, column=7, padx=6, pady=10, sticky="w"
        )

        self.status_var = tk.StringVar(value="Ready - Load an image to begin.")
        ttk.Label(self.control_frame, textvariable=self.status_var).grid(
            row=0, column=10, padx=8, pady=10, sticky="e"
        )

        # Container for input/output
        container = ttk.Frame(self.root)
        container.grid(row=1, column=0, sticky="nsew", padx=10, pady=(6, 10))
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(0, weight=1)

        # 2) INPUT FRAME
        self.input_frame = ttk.LabelFrame(container, text="Input Frame (Original Image)")
        self.input_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.input_frame.rowconfigure(0, weight=1)
        self.input_frame.columnconfigure(0, weight=1)

        self.input_canvas = tk.Canvas(self.input_frame, bg="white", highlightthickness=1)
        self.input_canvas.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # 3) OUTPUT FRAME
        self.output_frame = ttk.LabelFrame(container, text="Output Frame (Laplacian Sharpen Result)")
        self.output_frame.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        self.output_frame.rowconfigure(0, weight=1)
        self.output_frame.columnconfigure(0, weight=1)

        self.output_canvas = tk.Canvas(self.output_frame, bg="white", highlightthickness=1)
        self.output_canvas.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self._draw_placeholder(self.input_canvas, "No input image loaded")
        self._draw_placeholder(self.output_canvas, "Output will appear here")

    def _draw_placeholder(self, canvas, text):
        canvas.delete("all")
        w = canvas.winfo_width() or 400
        h = canvas.winfo_height() or 300
        canvas.create_text(w // 2, h // 2, text=text, fill="gray", font=("Segoe UI", 14))

    # ---------------- I/O ----------------
    def load_image(self):
        file_path = filedialog.askopenfilename(
            title="Open Image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.gif"),
                ("All files", "*.*"),
            ],
        )
        if not file_path:
            return

        try:
            img = Image.open(file_path)
            if img.mode != "RGB":
                img = img.convert("RGB")

            self.loaded_path = file_path
            self.original_image = img
            self.output_image = None

            self.status_var.set(f"Loaded: {os.path.basename(file_path)}  |  Size: {img.size}")
            self._refresh_previews()
        except Exception as e:
            messagebox.showerror("Error", f"Could not open image:\n{e}")

    def save_output(self):
        if self.output_image is None:
            messagebox.showwarning("Warning", "No output image to save! Apply the filter first.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Save Output Image",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")],
        )
        if not file_path:
            return

        try:
            self.output_image.save(file_path)
            self.status_var.set(f"Saved output: {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save image:\n{e}")

    def reset(self):
        if self.original_image is None and self.output_image is None:
            self.status_var.set("Nothing to reset.")
            return
        self.output_image = None
        self.status_var.set("Reset done. Output cleared.")
        self._refresh_previews()

    # ---------------- Laplacian Sharpen ----------------
    def apply_laplacian_sharpen(self):
        if self.original_image is None:
            messagebox.showwarning("Warning", "Please load an image first!")
            return

        k = float(self.strength_var.get())

        try:
            # Convert to float RGB array
            rgb = np.array(self.original_image, dtype=np.float32)

            # Grayscale for Laplacian
            gray = (0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2])

            # 4-neighbor Laplacian kernel:
            # [ 0  1  0
            #   1 -4  1
            #   0  1  0 ]
            kernel = np.array([[0, 1, 0],
                               [1, -4, 1],
                               [0, 1, 0]], dtype=np.float32)

            # Convolution (no SciPy needed): pad + slice
            p = np.pad(gray, ((1, 1), (1, 1)), mode="edge")

            lap = (
                kernel[0, 0] * p[0:-2, 0:-2] + kernel[0, 1] * p[0:-2, 1:-1] + kernel[0, 2] * p[0:-2, 2:] +
                kernel[1, 0] * p[1:-1, 0:-2] + kernel[1, 1] * p[1:-1, 1:-1] + kernel[1, 2] * p[1:-1, 2:] +
                kernel[2, 0] * p[2:,   0:-2] + kernel[2, 1] * p[2:,   1:-1] + kernel[2, 2] * p[2:,   2:]
            )

            # Sharpen (classic): S = I - k * Laplacian(I)
            # Add/subtract to RGB channels
            sharpened = rgb - (k * lap[:, :, None])

            # Clip and convert back
            sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)
            self.output_image = Image.fromarray(sharpened, mode="RGB")

            self.status_var.set(f"Applied Laplacian sharpening (k={k:.2f}).")
            self._refresh_previews()

        except Exception as e:
            messagebox.showerror("Error", f"Laplacian sharpening failed:\n{e}")

    # ---------------- Preview ----------------
    def _refresh_previews(self):
        if self.original_image is None:
            self._draw_placeholder(self.input_canvas, "No input image loaded")
        else:
            self.tk_input = self._render_on_canvas(self.input_canvas, self.original_image)

        if self.output_image is None:
            self._draw_placeholder(self.output_canvas, "Output will appear here")
        else:
            self.tk_output = self._render_on_canvas(self.output_canvas, self.output_image)

    def _render_on_canvas(self, canvas, pil_img):
        canvas.delete("all")

        cw = canvas.winfo_width()
        ch = canvas.winfo_height()
        if cw <= 2 or ch <= 2:
            cw, ch = 500, 400

        iw, ih = pil_img.size
        scale = min(cw / iw, ch / ih, 1.0)  # no upscale
        nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))

        resized = pil_img.resize((nw, nh), Image.Resampling.LANCZOS)
        tk_img = ImageTk.PhotoImage(resized)

        x = (cw - nw) // 2
        y = (ch - nh) // 2
        canvas.create_image(x, y, anchor="nw", image=tk_img)

        return tk_img


def main():
    root = tk.Tk()
    app = LaplacianSharpenApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
