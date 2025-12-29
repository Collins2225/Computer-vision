import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
from PIL import Image, ImageTk
import os


class HistogramEqualizationApp:
    """
    Building a Histogram + Histogram Equalization

    GUI structure (3 frames):
      1) Control Frame (top): Load, Equalize, Reset, Save, and a button to show histogram
      2) Input Frame (left): original image + its histogram (embedded)
      3) Output Frame (right): equalized image + its histogram (embedded)

    Notes:
      - Histogram is built for grayscale intensity (0..255)
      - Equalization is applied on grayscale for clarity and correctness
        (If you want color equalization, I can add YCrCb/HSV/LAB versions.)
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Histogram Building & Equalization")
        self.root.geometry("1200x700")
        self.root.minsize(1000, 620)

        self.original_image = None   # PIL RGB
        self.output_image = None     # PIL RGB (equalized grayscale converted to RGB)
        self.tk_input = None
        self.tk_output = None

        self._build_ui()

        # redraw previews/hist on resize
        self.input_canvas.bind("<Configure>", lambda e: self._refresh_all())
        self.output_canvas.bind("<Configure>", lambda e: self._refresh_all())

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
        ttk.Button(self.control_frame, text="Equalize Histogram", command=self.equalize_histogram).grid(
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

        ttk.Button(self.control_frame, text="Build/Refresh Histograms", command=self._refresh_all).grid(
            row=0, column=5, padx=8, pady=10, sticky="w"
        )

        self.status_var = tk.StringVar(value="Ready - Load an image to begin.")
        ttk.Label(self.control_frame, textvariable=self.status_var).grid(
            row=0, column=10, padx=8, pady=10, sticky="e"
        )

        # Container for Input/Output
        container = ttk.Frame(self.root)
        container.grid(row=1, column=0, sticky="nsew", padx=10, pady=(6, 10))
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(0, weight=1)

        # 2) INPUT FRAME
        self.input_frame = ttk.LabelFrame(container, text="Input Frame (Original Image + Histogram)")
        self.input_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.input_frame.columnconfigure(0, weight=1)
        self.input_frame.rowconfigure(0, weight=3)
        self.input_frame.rowconfigure(1, weight=2)

        self.input_canvas = tk.Canvas(self.input_frame, bg="white", highlightthickness=1)
        self.input_canvas.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 6))

        self.input_hist_canvas = tk.Canvas(self.input_frame, bg="white", highlightthickness=1, height=200)
        self.input_hist_canvas.grid(row=1, column=0, sticky="nsew", padx=10, pady=(6, 10))

        # 3) OUTPUT FRAME
        self.output_frame = ttk.LabelFrame(container, text="Output Frame (Equalized Image + Histogram)")
        self.output_frame.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        self.output_frame.columnconfigure(0, weight=1)
        self.output_frame.rowconfigure(0, weight=3)
        self.output_frame.rowconfigure(1, weight=2)

        self.output_canvas = tk.Canvas(self.output_frame, bg="white", highlightthickness=1)
        self.output_canvas.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 6))

        self.output_hist_canvas = tk.Canvas(self.output_frame, bg="white", highlightthickness=1, height=200)
        self.output_hist_canvas.grid(row=1, column=0, sticky="nsew", padx=10, pady=(6, 10))

        self._draw_placeholder(self.input_canvas, "No input image loaded")
        self._draw_placeholder(self.output_canvas, "Output will appear here")
        self._draw_placeholder(self.input_hist_canvas, "Input histogram will appear here")
        self._draw_placeholder(self.output_hist_canvas, "Output histogram will appear here")

    def _draw_placeholder(self, canvas, text):
        canvas.delete("all")
        w = canvas.winfo_width() or 400
        h = canvas.winfo_height() or 200
        canvas.create_text(w // 2, h // 2, text=text, fill="gray", font=("Segoe UI", 12))

    # ---------------- File actions ----------------
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

            self.original_image = img
            self.output_image = None
            self.status_var.set(f"Loaded: {os.path.basename(file_path)} | Size: {img.size}")
            self._refresh_all()
        except Exception as e:
            messagebox.showerror("Error", f"Could not open image:\n{e}")

    def save_output(self):
        if self.output_image is None:
            messagebox.showwarning("Warning", "No output image to save! Please equalize first.")
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
        self._refresh_all()

    # ---------------- Histogram + Equalization ----------------
    def equalize_histogram(self):
        if self.original_image is None:
            messagebox.showwarning("Warning", "Please load an image first!")
            return

        try:
            # Convert to grayscale
            gray = np.array(self.original_image.convert("L"), dtype=np.uint8)

            # Build histogram (0..255)
            hist = np.bincount(gray.flatten(), minlength=256).astype(np.float64)

            # CDF
            cdf = hist.cumsum()

            # Avoid division by zero
            cdf_min = cdf[cdf > 0].min() if np.any(cdf > 0) else 0.0
            total = cdf[-1] if cdf.size else 0.0

            if total <= 0:
                messagebox.showerror("Error", "Invalid image data (empty histogram).")
                return

            # Equalization mapping:
            # s = round((cdf(r) - cdf_min) / (N - cdf_min) * 255)
            lut = np.round((cdf - cdf_min) / (total - cdf_min) * 255.0)
            lut = np.clip(lut, 0, 255).astype(np.uint8)

            equalized = lut[gray]

            # Convert back to RGB for display consistency
            self.output_image = Image.fromarray(equalized, mode="L").convert("RGB")

            self.status_var.set("Applied: Histogram Equalization (grayscale).")
            self._refresh_all()

        except Exception as e:
            messagebox.showerror("Error", f"Histogram equalization failed:\n{e}")

    # ---------------- Rendering ----------------
    def _refresh_all(self):
        # images
        if self.original_image is None:
            self._draw_placeholder(self.input_canvas, "No input image loaded")
            self._draw_placeholder(self.input_hist_canvas, "Input histogram will appear here")
        else:
            self.tk_input = self._render_on_canvas(self.input_canvas, self.original_image)
            self._draw_histogram(self.input_hist_canvas, self.original_image)

        if self.output_image is None:
            self._draw_placeholder(self.output_canvas, "Output will appear here")
            self._draw_placeholder(self.output_hist_canvas, "Output histogram will appear here")
        else:
            self.tk_output = self._render_on_canvas(self.output_canvas, self.output_image)
            self._draw_histogram(self.output_hist_canvas, self.output_image)

    def _render_on_canvas(self, canvas, pil_img):
        canvas.delete("all")

        cw = canvas.winfo_width()
        ch = canvas.winfo_height()
        if cw <= 2 or ch <= 2:
            cw, ch = 500, 350

        iw, ih = pil_img.size
        scale = min(cw / iw, ch / ih, 1.0)  # no upscale
        nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))

        resized = pil_img.resize((nw, nh), Image.Resampling.LANCZOS)
        tk_img = ImageTk.PhotoImage(resized)

        x = (cw - nw) // 2
        y = (ch - nh) // 2
        canvas.create_image(x, y, anchor="nw", image=tk_img)

        return tk_img

    def _draw_histogram(self, canvas, pil_img):
        canvas.delete("all")

        cw = canvas.winfo_width()
        ch = canvas.winfo_height()
        if cw <= 2 or ch <= 2:
            cw, ch = 500, 200

        # compute grayscale histogram
        gray = np.array(pil_img.convert("L"), dtype=np.uint8)
        hist = np.bincount(gray.flatten(), minlength=256).astype(np.float64)

        max_h = hist.max() if hist.size else 1.0
        if max_h <= 0:
            max_h = 1.0

        # margins
        pad_l, pad_r, pad_t, pad_b = 35, 10, 10, 25
        w = max(1, cw - pad_l - pad_r)
        h = max(1, ch - pad_t - pad_b)

        # axes
        canvas.create_line(pad_l, pad_t, pad_l, pad_t + h, fill="black")
        canvas.create_line(pad_l, pad_t + h, pad_l + w, pad_t + h, fill="black")

        # label
        canvas.create_text(pad_l + w // 2, ch - 10, text="Intensity (0..255)", fill="black", font=("Segoe UI", 10))
        canvas.create_text(15, pad_t + h // 2, text="Count", angle=90, fill="black", font=("Segoe UI", 10))

        # draw histogram as vertical lines (256 bins)
        x_step = w / 256.0
        for i in range(256):
            x = pad_l + i * x_step
            y = pad_t + h - (hist[i] / max_h) * h
            canvas.create_line(x, pad_t + h, x, y, fill="gray")

        # ticks: 0, 128, 255
        for t in [0, 128, 255]:
            x = pad_l + t * x_step
            canvas.create_line(x, pad_t + h, x, pad_t + h + 5, fill="black")
            canvas.create_text(x, pad_t + h + 12, text=str(t), fill="black", font=("Segoe UI", 9))

        # max label
        canvas.create_text(pad_l + 5, pad_t + 8, text=f"max={int(max_h)}", anchor="w", fill="black", font=("Segoe UI", 9))

        # outline
        canvas.create_rectangle(1, 1, cw - 2, ch - 2, outline="#cfcfcf")


def main():
    root = tk.Tk()
    app = HistogramEqualizationApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
