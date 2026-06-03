# Motion Matching 用户操作指南

这份指南面向想在本工程里亲手复现博客 Motion Matching 画面的学习者。它分成两条路径：

- 手柄实时控制：在 notebook 里按播放按钮，一边推动手柄摇杆，一边观察角色响应。
- 博客确定性重放：粘贴一个临时 scratch cell，用固定输入复现博客里的 `runtime-player` 和 `fast-stop-turn` 画面。

博客资产不是录入手柄操作得到的，而是用固定输入重新渲染出来的稳定结果；学习 notebook 仍然可以接手柄实时控制，只是刷新由 Jupyter 的 timeline 驱动。

## 1. 打开学习 notebook

推荐从仓库根目录启动托管版 JupyterLab：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\start_animationpapers_lab.ps1
```

启动后打开学习副本，而不是直接编辑原始 notebook：

```text
.reports/study/AnimationPapers/Motion Matching.ipynb
```

如果你的本地服务已经在 `8891` 端口运行，也可以直接打开：

```text
http://127.0.0.1:8891/lab/workspaces/animationtech-study/tree/.reports/study/AnimationPapers/Motion%20Matching.ipynb
```

如果这个 URL 打不开，以启动器输出的 URL 为准；当 `8891` 被占用时，启动器可能会使用 `8892` 或后续端口。

打开后确认右上角 kernel 是：

```text
animationtech-motion_matching
```

## 2. 按顺序运行到 Player

从上到下运行 notebook，至少运行到 Cell 26。

关键 cell：

| Cell | 用途 |
| --- | --- |
| Cell 6 | `widgets.Controller(index=0)`，显示浏览器识别到的手柄状态。 |
| Cell 9 | Spring-damper 未来轨迹预测，可先看红/黄调试 marker 是否出现。 |
| Cell 14/18/21 | 数据库动画、滤波 root、33 维特征可视化。 |
| Cell 26 | 最终 Player / Motion Matching 搜索循环，也是实时播放入口。 |

Cell 26 输出里会出现 viewer 和 `frame` timeline。真正让角色更新的是这个 `frame` timeline，不是 Jupyter 顶部的 Run 按钮。

## 3. 手柄实时控制

1. 先连接手柄。
2. 运行 Cell 6，看到 controller widget。
3. 点一下浏览器页面或 notebook 空白处，让页面获得焦点。
4. 按一下手柄任意按钮，或推一下摇杆。
5. 观察 Cell 6 的 axes/buttons 是否变化。
6. 运行到 Cell 26。
7. 点击 Cell 26 输出里 `frame` timeline 左侧的播放按钮。
8. 播放时推动摇杆：
   - 左摇杆：控制移动方向，通常对应 axes `0/1`。
   - 右摇杆：控制朝向/转向，通常对应 axes `2/3`。

重要限制：手柄输入本身不会主动刷新画面。`frame` timeline 必须处于播放状态，或者你手动拖动 timeline，`render(frame)` 才会再次读取当前手柄值。

## 4. 复现博客固定输入画面

如果你想复现博客中的两张 runtime 结果图，不需要手柄。先运行到 Cell 26，然后在 Cell 26 后面新建一个临时 code cell，粘贴下面代码运行。

这段代码会临时提供固定输入，并把相机放到博客采集用的斜俯视角。它不会修改 notebook 文件，只会影响当前 kernel 会话。

```python
import inspect
import numpy as np

_blog_axes = [0.0, 0.0, 0.0, 0.0]

def animationtech_gamepad_axis(gamepad, index, default=0.0):
    try:
        return float(_blog_axes[index])
    except Exception:
        return default

def _blog_reset_player():
    global player
    x[:] = 0.0
    v[:] = 0.0
    a[:] = 0.0
    player = Player(0)
    x_rot[:] = np.array([1, 0, 0, 0], dtype=np.float32)
    v_rot[:] = 0.0
    desired_orientation[:] = np.array([1, 0, 0, 0], dtype=np.float32)

def _blog_set_camera():
    anchor = player.p[0].copy() if "player" in globals() else x.copy()
    viewer.camera_pos = (anchor + np.array([-370, 280, 350], dtype=np.float32)).tolist()
    viewer.camera_pitch = -18
    viewer.camera_yaw = -45

def _blog_render_with_input(
    frame,
    move_x,
    move_z,
    turn_x,
    turn_z,
    max_speed,
    halflife,
    halflife_rot,
    code_vs_anim=0.0,
    fast_stop=False,
    inertialize=True,
    substeps=4,
):
    signature = inspect.signature(render)
    for substep in range(substeps):
        _blog_set_camera()
        kwargs = dict(
            max_speed=max_speed,
            halflife=halflife,
            halflife_rot=halflife_rot,
            code_vs_anim=code_vs_anim,
            fast_stop=fast_stop,
            inertialize=inertialize,
        )
        if "use_gamepad" in signature.parameters:
            kwargs.update(
                use_gamepad=False,
                move_x=move_x,
                move_z=move_z,
                turn_x=turn_x,
                turn_z=turn_z,
            )
        else:
            _blog_axes[:] = [move_x, -move_z, turn_x, -turn_z]
        render(frame + substep, **kwargs)
```

### 4.1 Runtime Player 搜索循环

继续新建一个 code cell，运行：

```python
_blog_reset_player()
_blog_render_with_input(
    frame=50,
    move_x=0.75,
    move_z=1.0,
    turn_x=0.35,
    turn_z=0.65,
    max_speed=5.5,
    halflife=0.30,
    halflife_rot=0.22,
    fast_stop=False,
    inertialize=True,
)
viewer
```

你应该看到角色在棋盘地面上运动，脚边有红色当前 marker，前方有黄色未来轨迹 marker。这对应博客里的 `inertialization_transition_result.png`。

### 4.2 Stop / Turn 压力测试

继续新建一个 code cell，运行：

```python
_blog_reset_player()
_blog_render_with_input(
    frame=65,
    move_x=1.0,
    move_z=0.15,
    turn_x=1.0,
    turn_z=0.15,
    max_speed=5.8,
    halflife=0.18,
    halflife_rot=0.15,
    fast_stop=False,
    inertialize=True,
)
viewer
```

你应该看到角色处在急转/变向的中段，红色当前 marker 和黄色未来轨迹 marker 都在画面内。这对应博客里的 `fast_stop_turn_cases_result.png`。

如果想观察更接近“停下”的末段，可以把 `frame=80`，并把 `move_x/move_z` 改为 `0.0`、`turn_x=1.0`、`turn_z=0.0`、`fast_stop=True`。这一帧黄色轨迹可能更短，所以博客静态截图使用中段帧来保留调试信息。

## 5. 恢复手柄控制

上面的 scratch cell 会临时覆盖 `animationtech_gamepad_axis()`，用于稳定复现博客画面。要恢复真实手柄读取：

1. 重新运行 Cell 1，恢复默认 helper。
2. 重新运行 Cell 6，重新显示 controller widget。
3. 重新运行 Cell 26。
4. 点击 `frame` timeline 播放按钮，再推动手柄。

如果状态已经乱了，最干净的方式是 Kernel -> Restart Kernel and Run All Cells，然后重新按顺序运行到 Cell 26。

## 6. 常见问题

| 现象 | 处理 |
| --- | --- |
| 手柄 widget 没反应 | 点一下浏览器页面，按一次手柄按钮，再重新运行 Cell 6。浏览器通常需要页面焦点和一次按钮输入后才暴露 Gamepad API。 |
| 多个手柄时读错设备 | 把 Cell 6 改成 `widgets.Controller(index=1)` 再试。 |
| timeline 播放了但角色不动 | 确认手柄 axes 在 Cell 6 中变化；若使用 scratch cell，确认已经运行 `_blog_render_with_input(...)`。 |
| 只看到棋盘地面 | 先重新运行 Cell 26 重置 `player`，再运行博客复现代码；也可以用鼠标拖 viewer 或滚轮调整相机。 |
| 画面延迟明显 | 这是 Jupyter widget + browser viewer 的限制，适合学习算法，不等同于低延迟游戏窗口。 |
| Cell 26 未来出现 `use_gamepad` 控件 | 勾选 `use_gamepad` 可读真实手柄；不勾选时可直接用 `move_x/move_z/turn_x/turn_z` 滑块模拟输入。 |
| kernel 不对或导入失败 | 确认 kernel 是 `animationtech-motion_matching`，并优先通过 `tools/start_animationpapers_lab.ps1` 打开学习副本。 |
