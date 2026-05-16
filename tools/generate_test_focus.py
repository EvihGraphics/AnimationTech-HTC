import nbformat as nbf

nb = nbf.v4.new_notebook()

# 1. CSS Injection
css_code = """
from IPython.display import display, HTML
display(HTML('''
<style>
/* Hide JupyterLab Top/Left Panels */
#jp-top-panel, #jp-left-stack, #jp-bottom-panel, .jp-Activity { display: none !important; }
.jp-Toolbar { display: none !important; }

/* Hide all cell inputs */
.jp-Cell-inputWrapper { display: none !important; }
.jp-OutputArea-prompt { display: none !important; }

/* Make the specific output area full screen */
.jp-Notebook { padding: 0 !important; }
.jp-Cell { padding: 0 !important; margin: 0 !important; border: none !important; }
.jp-OutputArea-output { margin: 0 !important; padding: 0 !important; }

/* Make canvas larger */
canvas {
    width: 800px !important;
    height: 800px !important;
    margin: 0 auto !important;
    display: block !important;
}
</style>
'''))
"""

# 2. Render code
render_code = r"""
import pickle
import numpy as np
from ipywebgl import Viewer

with open(r'd:\Users\hi\Documents\SCU\WorldModel\AnimationTech-HTC\labs\AnimationPapers\animated_face.dat', 'rb') as f:
    indices, normals, frames = pickle.load(f)

v = np.array(frames[0], dtype=np.float32)
n = np.array(normals, dtype=np.float32)
ind = np.array(indices, dtype=np.uint16)

viewer = Viewer(camera_pos=[-370, 280, 350], camera_yaw=-45, camera_pitch=-18)
vbo = viewer.create_buffer(v)
vbo_n = viewer.create_buffer(n)
ibo = viewer.create_buffer(ind)
vao = viewer.create_vertex_array()
viewer.bind_vertex_array(vao)
viewer.vertex_attrib_pointer(0, 3, 'FLOAT', False, 0, 0, vbo)
viewer.vertex_attrib_pointer(1, 3, 'FLOAT', False, 0, 0, vbo_n)

shader = viewer.create_program(
    '''#version 300 es
    layout(location=0) in vec3 in_vert;
    layout(location=1) in vec3 in_normal;
    uniform mat4 u_view_matrix;
    uniform mat4 u_proj_matrix;
    out vec3 v_normal;
    void main() {
        gl_Position = u_proj_matrix * u_view_matrix * vec4(in_vert, 1.0);
        v_normal = in_normal;
    }''',
    '''#version 300 es
    precision highp float;
    in vec3 v_normal;
    out vec4 fragColor;
    void main() {
        vec3 normal = normalize(v_normal);
        float light = dot(normal, vec3(0.0, 1.0, 1.0)) * 0.5 + 0.5;
        fragColor = vec4(vec3(0.8, 0.7, 0.6) * light, 1.0);
    }'''
)

viewer.clear()
viewer.use_program(shader)
viewer.bind_vertex_array(vao)
viewer.draw_elements('TRIANGLES', ind.size, 'UNSIGNED_SHORT', 0)
viewer.execute_commands()

viewer
"""

nb.cells = [
    nbf.v4.new_code_cell(css_code),
    nbf.v4.new_code_cell(render_code)
]

with open('.reports/study/AnimationPapers/test_focus.ipynb', 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

print('Created test_focus.ipynb')
