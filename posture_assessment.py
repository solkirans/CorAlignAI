import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import tkinter as tk
from tkinter import ttk

class PostureAssessment:
    def __init__(self):
        self.questions = {
            'neck': [
                ('neck_forward', 'Is your neck positioned forward? (0-10, 0=normal, 10=severe)'),
                ('neck_tilt', 'Does your neck tilt to one side? (-10=left, 0=center, 10=right)'),
                ('neck_rotation', 'Is your neck rotated? (-10=left, 0=center, 10=right)')
            ],
            'shoulders': [
                ('l_shoulder_height', 'Left shoulder: Is it elevated? (0=normal, 10=highly elevated)'),
                ('r_shoulder_height', 'Right shoulder: Is it elevated? (0=normal, 10=highly elevated)'),
                ('l_shoulder_forward', 'Left shoulder: How rounded forward? (0=normal, 10=severe)'),
                ('r_shoulder_forward', 'Right shoulder: How rounded forward? (0=normal, 10=severe)'),
                ('l_shoulder_blade', 'Left shoulder blade: (-10=wings out, 0=normal, 10=tucked in)'),
                ('r_shoulder_blade', 'Right shoulder blade: (-10=wings out, 0=normal, 10=tucked in)')
            ],
            'thoracic_spine': [
                ('upper_thoracic_rotation', 'Upper back rotation? (-10=left, 0=center, 10=right)'),
                ('l_thoracic_tension', 'Left upper back tension? (0=none, 10=severe)'),
                ('r_thoracic_tension', 'Right upper back tension? (0=none, 10=severe)'),
                ('thoracic_kyphosis', 'Upper back rounding? (0=normal, 10=severe)')
            ],
            'lumbar_spine': [
                ('lumbar_rotation', 'Lower back rotation? (-10=left, 0=center, 10=right)'),
                ('l_lumbar_tension', 'Left lower back tension? (0=none, 10=severe)'),
                ('r_lumbar_tension', 'Right lower back tension? (0=none, 10=severe)'),
                ('lumbar_lordosis', 'Lower back curve? (-10=flat, 0=normal, 10=excessive)')
            ],
            'hips': [
                ('l_hip_rotation', 'Left hip rotation? (-10=internal, 0=neutral, 10=external)'),
                ('r_hip_rotation', 'Right hip rotation? (-10=internal, 0=neutral, 10=external)'),
                ('l_hip_height', 'Left hip height? (-10=low, 0=level, 10=high)'),
                ('r_hip_height', 'Right hip height? (-10=low, 0=level, 10=high)'),
                ('l_hip_shift', 'Left hip shift? (-10=back, 0=centered, 10=forward)'),
                ('r_hip_shift', 'Right hip shift? (-10=back, 0=centered, 10=forward)')
            ],
            'knees': [
                ('l_knee_alignment', 'Left knee alignment? (-10=knock knee, 0=straight, 10=bow legged)'),
                ('r_knee_alignment', 'Right knee alignment? (-10=knock knee, 0=straight, 10=bow legged)'),
                ('l_knee_rotation', 'Left knee rotation? (-10=internal, 0=straight, 10=external)'),
                ('r_knee_rotation', 'Right knee rotation? (-10=internal, 0=straight, 10=external)')
            ],
            'feet': [
                ('l_foot_arch', 'Left foot arch? (-10=flat, 0=normal, 10=high)'),
                ('r_foot_arch', 'Right foot arch? (-10=flat, 0=normal, 10=high)'),
                ('l_foot_rotation', 'Left foot rotation? (-10=in, 0=straight, 10=out)'),
                ('r_foot_rotation', 'Right foot rotation? (-10=in, 0=straight, 10=out)')
            ]
        }
        
        self.muscles = {
            'neck': ['Upper Trapezius', 'Levator Scapulae', 'Sternocleidomastoid'],
            'shoulders': ['Middle Trapezius', 'Lower Trapezius', 'Rhomboids', 'Pectoralis Minor', 'Serratus Anterior'],
            'thoracic_spine': ['Thoracic Erector Spinae', 'Rhomboids', 'Serratus Anterior', 'Intercostals'],
            'lumbar_spine': ['Lumbar Erector Spinae', 'Multifidus', 'Quadratus Lumborum', 'Psoas'],
            'hips': ['Gluteus Maximus', 'Gluteus Medius', 'Piriformis', 'TFL', 'Hip Flexors'],
            'knees': ['Vastus Medialis', 'Vastus Lateralis', 'Hamstrings', 'Gastrocnemius'],
            'feet': ['Tibialis Anterior', 'Peroneals', 'Posterior Tibialis', 'Plantar Fascia']
        }
        
        self.responses = {}
        self.muscle_status = {}

    def ask_questions(self):
        root = tk.Tk()
        root.title("Bilateral Posture Assessment")
        
        # Create scrollable frame
        main_frame = ttk.Frame(root)
        main_frame.pack(fill="both", expand=True)
        
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        for region, questions in self.questions.items():
            frame = ttk.LabelFrame(scrollable_frame, text=region.title(), padding="10")
            frame.pack(fill="x", padx=10, pady=5)
            
            for key, question in questions:
                ttk.Label(frame, text=question).pack()
                scale = ttk.Scale(frame, from_=-10, to=10, orient="horizontal")
                scale.pack()
                self.responses[key] = scale
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        ttk.Button(root, text="Submit", command=root.quit).pack(pady=20)
        root.mainloop()
        
        # Get final values
        for key in self.responses:
            self.responses[key] = self.responses[key].get()
        
        root.destroy()

    def analyze_muscles(self):
        # Initialize muscle status dictionary with bilateral values
        self.muscle_status = {muscle: {'left': 0, 'right': 0} 
                            for group in self.muscles.values() 
                            for muscle in group}
        
        # Analyze shoulder complex
        self._analyze_shoulder_complex()
        # Analyze spinal regions
        self._analyze_spine()
        # Analyze lower extremity
        self._analyze_lower_extremity()

    def _analyze_shoulder_complex(self):
        # Left shoulder analysis
        if self.responses['l_shoulder_forward'] > 5:
            self.muscle_status['Pectoralis Minor']['left'] = -1  # tight
            self.muscle_status['Middle Trapezius']['left'] = 1   # stretched
            self.muscle_status['Rhomboids']['left'] = 1         # stretched
            
        # Right shoulder analysis
        if self.responses['r_shoulder_forward'] > 5:
            self.muscle_status['Pectoralis Minor']['right'] = -1
            self.muscle_status['Middle Trapezius']['right'] = 1
            self.muscle_status['Rhomboids']['right'] = 1

    def _analyze_spine(self):
        # Thoracic analysis
        if self.responses['l_thoracic_tension'] > 5:
            self.muscle_status['Thoracic Erector Spinae']['left'] = -1
        if self.responses['r_thoracic_tension'] > 5:
            self.muscle_status['Thoracic Erector Spinae']['right'] = -1
            
        # Lumbar analysis
        if self.responses['l_lumbar_tension'] > 5:
            self.muscle_status['Lumbar Erector Spinae']['left'] = -1
            self.muscle_status['Quadratus Lumborum']['left'] = -1
        if self.responses['r_lumbar_tension'] > 5:
            self.muscle_status['Lumbar Erector Spinae']['right'] = -1
            self.muscle_status['Quadratus Lumborum']['right'] = -1

    def _analyze_lower_extremity(self):
        # Knee analysis
        if self.responses['l_knee_alignment'] < -5:  # knock knee
            self.muscle_status['Vastus Lateralis']['left'] = -1
            self.muscle_status['Vastus Medialis']['left'] = 1
        if self.responses['r_knee_alignment'] < -5:
            self.muscle_status['Vastus Lateralis']['right'] = -1
            self.muscle_status['Vastus Medialis']['right'] = 1
            
        # Foot analysis
        if self.responses['l_foot_arch'] < -5:  # flat foot
            self.muscle_status['Posterior Tibialis']['left'] = 1
            self.muscle_status['Peroneals']['left'] = -1
        if self.responses['r_foot_arch'] < -5:
            self.muscle_status['Posterior Tibialis']['right'] = 1
            self.muscle_status['Peroneals']['right'] = -1

    def visualize_results(self):
        views = ['front', 'back', 'left', 'right']
        fig, axes = plt.subplots(2, 2, figsize=(15, 15))
        
        for idx, view in enumerate(views):
            ax = axes[idx//2, idx%2]
            ax.set_title(f'{view.title()} View')
            
            # Create separate heatmaps for left and right sides
            heatmap_data = np.zeros((20, 10))
            
            # Fill heatmap data based on muscle status
            for muscle, status in self.muscle_status.items():
                # Map muscle locations to heatmap coordinates
                # This would need to be customized for each view
                if view in ['front', 'back']:
                    # Split visualization for left and right
                    left_coords = self._get_muscle_coordinates(muscle, 'left', view)
                    right_coords = self._get_muscle_coordinates(muscle, 'right', view)
                    
                    if left_coords:
                        heatmap_data[left_coords] = status['left']
                    if right_coords:
                        heatmap_data[right_coords] = status['right']
                else:
                    # Single side view
                    side = 'left' if view == 'left' else 'right'
                    coords = self._get_muscle_coordinates(muscle, side, view)
                    if coords:
                        heatmap_data[coords] = status[side]
            
            # Create custom colormap: blue (stretched) to white (normal) to red (tight)
            colors = ['blue', 'white', 'red']
            cmap = LinearSegmentedColormap.from_list("custom", colors, N=100)
            
            im = ax.imshow(heatmap_data, cmap=cmap, vmin=-1, vmax=1)
            ax.axis('off')
        
        plt.colorbar(im, ax=axes.ravel().tolist())
        plt.tight_layout()
        plt.show()

    def _get_muscle_coordinates(self, muscle, side, view):
        # This would need to be implemented with specific coordinates for each muscle
        # Returns tuple of (row_idx, col_idx) for the muscle location in the heatmap
        # This is a placeholder - you would need to define actual coordinates
        return (0, 0)

    def run_assessment(self):
        self.ask_questions()
        self.analyze_muscles()
        self.visualize_results()

if __name__ == "__main__":
    assessment = PostureAssessment()
    assessment.run_assessment()