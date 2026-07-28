import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import numpy as np
import cv2
from PIL import Image, ImageTk

class GrainSizeTool:
    def __init__(self, root):
        self.root = root
        self.root.title("ASTM E112 Grain Size Estimator (Intercept Method)")

        self.img = None
        self.display_img = None
        self.gray = None
        self.edges = None

        self.scale_points = []
        self.line_points = []
        self.lines = []  # list of ((x1,y1),(x2,y2))
        self.px_per_um = None

        self.canvas = tk.Canvas(root, width=1200, height=800, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        toolbar = tk.Frame(root)
        toolbar.pack(fill=tk.X)

        tk.Button(toolbar, text="Open Image", command=self.open_image).pack(side=tk.LEFT, padx=4, pady=4)
        tk.Button(toolbar, text="Set Scale (2 clicks)", command=self.set_scale_mode).pack(side=tk.LEFT, padx=4)
        tk.Button(toolbar, text="Add Intercept Line (2 clicks)", command=self.set_line_mode).pack(side=tk.LEFT, padx=4)
        tk.Button(toolbar, text="Auto 10 Random Lines", command=self.auto_lines).pack(side=tk.LEFT, padx=4)
        tk.Button(toolbar, text="Detect Boundaries", command=self.detect_boundaries).pack(side=tk.LEFT, padx=4)
        tk.Button(toolbar, text="Calculate Grain Size", command=self.calculate).pack(side=tk.LEFT, padx=4)
        tk.Button(toolbar, text="Clear Lines", command=self.clear_lines).pack(side=tk.LEFT, padx=4)

        self.status = tk.Label(root, text="Load an image to begin.", anchor="w")
        self.status.pack(fill=tk.X)

        self.mode = None
        self.canvas.bind("<Button-1>", self.on_click)

    def open_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.tif *.tiff *.bmp")])
        if not path:
            return
        self.img = cv2.imread(path)
        if self.img is None:
            messagebox.showerror("Error", "Could not open image.")
            return
        self.img = cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB)
        self.gray = cv2.cvtColor(self.img, cv2.COLOR_RGB2GRAY)
        self.edges = None
        self.scale_points = []
        self.line_points = []
        self.lines = []
        self.px_per_um = None
        self.render()
        self.status.config(text=f"Loaded: {path}")

    def render(self):
        if self.img is None:
            return
        vis = self.img.copy()

        # overlay edges if exists
        if self.edges is not None:
            edge_rgb = np.zeros_like(vis)
            edge_rgb[:, :, 1] = self.edges  # green edges
            vis = cv2.addWeighted(vis, 0.85, edge_rgb, 0.6, 0)

        # draw scale points
        for p in self.scale_points:
            cv2.circle(vis, p, 5, (255, 0, 0), -1)
        if len(self.scale_points) == 2:
            cv2.line(vis, self.scale_points[0], self.scale_points[1], (255, 0, 0), 2)

        # draw intercept lines
        for (p1, p2) in self.lines:
            cv2.line(vis, p1, p2, (0, 255, 255), 2)

        # fit to canvas
        h, w = vis.shape[:2]
        c_w = max(100, self.canvas.winfo_width())
        c_h = max(100, self.canvas.winfo_height())
        scale = min(c_w / w, c_h / h)
        self.disp_scale = scale
        new_w, new_h = int(w * scale), int(h * scale)
        disp = cv2.resize(vis, (new_w, new_h), interpolation=cv2.INTER_AREA)

        self.display_img = disp
        im_pil = Image.fromarray(disp)
        self.tk_img = ImageTk.PhotoImage(image=im_pil)
        self.canvas.delete("all")
        self.canvas.create_image((c_w - new_w)//2, (c_h - new_h)//2, anchor=tk.NW, image=self.tk_img)

        self.offset_x = (c_w - new_w)//2
        self.offset_y = (c_h - new_h)//2

    def canvas_to_image(self, x, y):
        if self.img is None:
            return None
        ix = int((x - self.offset_x) / self.disp_scale)
        iy = int((y - self.offset_y) / self.disp_scale)
        h, w = self.img.shape[:2]
        if ix < 0 or iy < 0 or ix >= w or iy >= h:
            return None
        return (ix, iy)

    def on_click(self, event):
        p = self.canvas_to_image(event.x, event.y)
        if p is None:
            return

        if self.mode == "scale":
            self.scale_points.append(p)
            if len(self.scale_points) > 2:
                self.scale_points = self.scale_points[-2:]
            if len(self.scale_points) == 2:
                px_len = np.linalg.norm(np.array(self.scale_points[0]) - np.array(self.scale_points[1]))
                real_um = simpledialog.askfloat("Scale", "Enter scale bar length in µm (e.g., 100):", minvalue=0.001)
                if real_um:
                    self.px_per_um = px_len / real_um
                    self.status.config(text=f"Scale set: {self.px_per_um:.4f} px/µm")
            self.render()

        elif self.mode == "line":
            self.line_points.append(p)
            if len(self.line_points) == 2:
                self.lines.append((self.line_points[0], self.line_points[1]))
                self.line_points = []
                self.status.config(text=f"Added line #{len(self.lines)}")
                self.render()

    def set_scale_mode(self):
        self.mode = "scale"
        self.status.config(text="Scale mode: click two ends of scale bar.")

    def set_line_mode(self):
        if self.img is None:
            return
        self.mode = "line"
        self.status.config(text="Line mode: click two points to define an intercept line.")

    def clear_lines(self):
        self.lines = []
        self.line_points = []
        self.render()
        self.status.config(text="Intercept lines cleared.")

    def auto_lines(self):
        if self.img is None:
            return
        h, w = self.img.shape[:2]
        rng = np.random.default_rng(0)
        self.lines = []
        for _ in range(10):
            x1, y1 = int(rng.integers(0, w)), int(rng.integers(0, h))
            angle = rng.uniform(0, np.pi)
            L = int(min(w, h) * 0.6)
            x2 = int(np.clip(x1 + L * np.cos(angle), 0, w - 1))
            y2 = int(np.clip(y1 + L * np.sin(angle), 0, h - 1))
            self.lines.append(((x1, y1), (x2, y2)))
        self.render()
        self.status.config(text="Added 10 random intercept lines.")

    def detect_boundaries(self):
        if self.gray is None:
            return
        # Basic enhancement + edge detect (tuneable)
        blur = cv2.GaussianBlur(self.gray, (3, 3), 0)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8)).apply(blur)
        edges = cv2.Canny(clahe, threshold1=40, threshold2=120)
        kernel = np.ones((2,2), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)
        self.edges = edges
        self.render()
        self.status.config(text="Boundaries detected (preview in green).")

    @staticmethod
    def sample_line_points(p1, p2, n=2000):
        x = np.linspace(p1[0], p2[0], n)
        y = np.linspace(p1[1], p2[1], n)
        return np.vstack([x, y]).T.astype(int)

    def count_intersections(self, p1, p2):
        pts = self.sample_line_points(p1, p2)
        h, w = self.edges.shape[:2]
        vals = []
        for x, y in pts:
            if 0 <= x < w and 0 <= y < h:
                vals.append(1 if self.edges[y, x] > 0 else 0)
            else:
                vals.append(0)
        vals = np.array(vals, dtype=np.uint8)
        # Count 0->1 transitions as intersections
        transitions = np.sum((vals[1:] == 1) & (vals[:-1] == 0))
        return int(transitions)

    def calculate(self):
        if self.img is None:
            messagebox.showwarning("Missing", "Load image first.")
            return
        if self.px_per_um is None:
            messagebox.showwarning("Missing", "Set scale first.")
            return
        if self.edges is None:
            messagebox.showwarning("Missing", "Run boundary detection first.")
            return
        if len(self.lines) == 0:
            messagebox.showwarning("Missing", "Add intercept lines first.")
            return

        total_length_px = 0.0
        total_intercepts = 0
        line_stats = []

        for (p1, p2) in self.lines:
            Lpx = np.linalg.norm(np.array(p1) - np.array(p2))
            P = self.count_intersections(p1, p2)
            total_length_px += Lpx
            total_intercepts += P
            line_stats.append((Lpx, P))

        if total_intercepts == 0:
            messagebox.showerror("Error", "No intercepts found. Adjust edge detection or lines.")
            return

        # Mean lineal intercept (um): lbar = total_test_line_length / number_of_intercepts
        total_length_um = total_length_px / self.px_per_um
        lbar_um = total_length_um / total_intercepts

        # Approx ASTM G estimate from intercept length using common log-linear approximation.
        # (Practical approximation for quick estimate, not certified report.)
        # G ≈ -6.643856 * log10(lbar_mm) - 3.288
        lbar_mm = lbar_um / 1000.0
        G_est = -6.643856 * np.log10(max(lbar_mm, 1e-9)) - 3.288

        report = (
            f"Lines: {len(self.lines)}\n"
            f"Total test length: {total_length_um:.2f} µm\n"
            f"Total intercepts (P): {total_intercepts}\n"
            f"Mean lineal intercept (l̄): {lbar_um:.2f} µm\n"
            f"Estimated ASTM grain size number (G): {G_est:.2f}\n\n"
            f"Note: This is an automated estimate; verify manually for strict ASTM E112 compliance."
        )

        self.status.config(text=f"Done. l̄={lbar_um:.2f} µm, G≈{G_est:.2f}")
        messagebox.showinfo("Grain Size Result", report)

def main():
    root = tk.Tk()
    app = GrainSizeTool(root)
    root.geometry("1280x900")
    root.bind("<Configure>", lambda e: app.render() if app.img is not None else None)
    root.mainloop()

if __name__ == "__main__":
    main()