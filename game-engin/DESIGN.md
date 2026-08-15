# 2D 游戏引擎设计方案

> 目标:**小型游戏创作工具** —— 让开发者/设计师能直接做出可玩的 2D 游戏,并内置可视化场景编辑器。
> 平台:**Windows / Linux / macOS** 桌面;语言 **C++17**;图形 **SDL2 + OpenGL 3.3**。

---

## 1. 技术选型

| 模块 | 选型 | 版本 | 理由 |
|---|---|---|---|
| 语言标准 | C++17 | — | 现代特性 + 广泛编译器支持,无需 C++20 复杂特性 |
| 窗口/事件/上下文 | SDL2 | 2.30.x | 跨平台、成熟稳定、GL 上下文创建简单 |
| 图形 API | OpenGL 3.3 Core | — | 2D 渲染完全够用;比 Vulkan/DX 简单得多 |
| 音频 | SDL_mixer | 2.8.x | 与 SDL2 同生态,支持 WAV/OGG/MP3、流式音乐 |
| 编辑器 UI | Dear ImGui (docking branch) | 1.90+ | 引擎内嵌即时模式 GUI,迭代极快 |
| 数学库 | 自研 `math.h` (header-only) | — | 2D 仅需 Vec2/Mat3/Rect,零依赖 |
| JSON | nlohmann/json (单头文件) | 3.11+ | 场景/配置可读可 diff,调试友好 |
| 构建 | CMake + FetchContent | 3.20+ | 自动拉取依赖,免手工安装 |
| 脚本(可选扩展) | sol2 + Lua | sol2 3.x / Lua 5.4 | 设计师写游戏逻辑,与 C++ 无缝互操作 |

**选型理由摘要**:
- 不选 Web/Unity 等既有引擎,是为了完全掌控渲染与架构,适合学习与深度定制。
- 不选 Vulkan:2D 场景不需要其复杂度,GL3.3 在全部主流平台可用。
- 不选 glm:2D 场景的数学量小,自研可避免模板编译开销并保持 API 贴近游戏语义。

---

## 2. 总体架构

```
┌─────────────────────────────────────────────────────────┐
│  编辑器层 Editor (仅编辑器模式编译)                         │
│  ImGui 视口 / 层级树 / 属性面板 / 资源浏览器 / Gizmo       │
├─────────────────────────────────────────────────────────┤
│  游戏层 Game                                             │
│  Scene  |  GameObject  |  Prefab  |  场景序列化(JSON)    │
├─────────────────────────────────────────────────────────┤
│  系统层 System                                           │
│  Render  |  Physics  |  Audio  |  Input  |  Resource     │
├─────────────────────────────────────────────────────────┤
│  核心层 Core                                             │
│  Math | Time(固定步长) | Logger | EventBus | 内存池       │
├─────────────────────────────────────────────────────────┤
│  平台层 Platform                                         │
│  Window(SDL) | GLContext | 事件轮询 | 计时              │
└─────────────────────────────────────────────────────────┘
```

### 依赖方向(严格单向)
```
Platform ← Core ← System ← Game ← Editor
```
下层不依赖上层;系统之间通过 Core 的 `EventBus` 解耦(如 Physics 发碰撞事件,Audio 系统监听)。

### 两种编译目标
| 目标 | 内容 | 用途 |
|---|---|---|
| `engine_runtime` | Platform+Core+System+Game,不含 ImGui | 发布游戏 |
| `engine_editor` | 全部 + Editor | 开发创作 |

---

## 3. 游戏主循环

```
while (running):
    window.poll_events()                    # 平台层事件 → InputManager
    dt = timer.tick()                       # 实际帧时间,秒
    acc += min(dt, MAX_DT)                  # MAX_DT=0.25 防止螺旋死亡
    while (acc >= FIXED_DT):                # FIXED_DT=1/60,逻辑固定步长
        scene.update(FIXED_DT)              # 所有系统按固定步长更新
        acc -= FIXED_DT
    alpha = acc / FIXED_DT                  # 渲染插值系数 [0,1)
    renderer.begin_frame()
    scene.render(alpha)                     # 渲染,使用前一帧+当前帧插值
    editor.draw()                           # 仅编辑器模式
    renderer.end_frame()
```

**设计要点**:
- 逻辑用固定步长:物理与 AI 结果可复现,不受帧率波动影响。
- 渲染用插值:`RigidBody` 保存 `prev_pos/pos`,渲染时按 `alpha` 取插值位置,消除抖动。
- `FixedUpdate` 与 `Update` 分离:物理/AI 走 FixedUpdate,表现层(动画计时、粒子)走 Update。

---

## 4. 模块详细设计

### 4.1 Core 层

#### 4.1.1 数学库 `engine/core/math.h` (header-only)
- `Vec2`(位置/速度/UV)、`Vec4`(颜色,RGBA 归一化)
- `Mat3`(2D 变换:平移/旋转/缩放,支持正交相机 view-proj)
- `Rect`(AABB,`contains / intersects / union`)
- 常量 `PI`、角度↔弧度转换、`lerp / clamp / smoothstep`
- 运算全部 inline,SSE 不做(2D 量小,可读性优先)

#### 4.1.2 时间系统 `time.h`
- `TickTimer`:真实时间、帧时间、帧数统计(FPS)
- 提供全局 `Time::dt / Time::fixed_dt / Time::time`

#### 4.1.3 日志系统 `logger.h`
- 分级:Debug / Info / Warn / Error
- 输出到控制台 + 文件(`logs/engine.log`),轮转 5MB
- 编译期可裁剪 Debug 日志

#### 4.1.4 事件总线 `event.h`
```cpp
struct CollisionEvent { GameObject* a; GameObject* b; };
struct SceneChangedEvent {};
struct KeyEvent { ... };

EventBus::subscribe<CollisionEvent>(handler);   // 注册监听
EventBus::emit(CollisionEvent{...});            // 广播
```
- 类型安全的模板事件,支持任意数量监听者
- 用于:物理→音频(撞击声)、编辑器→场景(保存/重载)

#### 4.1.5 内存池 `pool_allocator.h`
- 组件与粒子使用对象池分配,避免高频创建/销毁的堆碎片
- 接口 `Pool<T>::acquire() / release(T*)`

### 4.2 实体系统(ECS 简化版:组合式)

> 决策:**不采用严格 ECS(Entity/Component/System 全分离),采用 GameObject + Component 组合**。
> 原因:目标实体量 < 1 万,组件模式的心智模型与 Unity/Godot 一致,对"创作工具"更友好;
> 通过对象池 + 批处理渲染弥补其缓存友好性不足。

```cpp
class GameObject {
    std::string  name;              // 唯一名(编辑器标识)
    Transform    transform;         // 位置/旋转/缩放 + 父指针
    std::vector<Component*> components;
    bool         active;            // 激活状态,可整体禁用
    bool         isPrefabInstance;  // Prefab 实例标记(见 4.7.2)
};

class Component {
    GameObject* owner;
    virtual void OnInit()   {}
    virtual void OnUpdate(float dt)      {}   // 每帧(表现)
    virtual void OnFixedUpdate(float dt) {}   // 固定步长(物理)
    virtual void OnRender() {}
    virtual void OnDestroy() {}
    virtual void OnCollision(CollisionEvent&) {}  // 由 Physics 回调
    virtual void Serialize(json&) const {}         // 场景存取
    virtual void Deserialize(const json&) {}
};
```

**内置组件清单**:

| 组件 | 归属系统 | 说明 |
|---|---|---|
| `SpriteRenderer` | Render | 纹理/图集帧/颜色/翻转/层序 |
| `AnimatedSprite` | Render | 帧动画(帧序列、时长、循环) |
| `TilemapRenderer` | Render | 分块瓦片地图渲染 |
| `ParticleSystem` | Render | 粒子发射器(见 4.3.5) |
| `Camera` | Render | 正交相机,视口变换 |
| `RigidBody` | Physics | 速度/重力/质量/弹力/摩擦 |
| `BoxCollider` / `CircleCollider` | Physics | 碰撞形状 |
| `AudioSource` | Audio | 播放音效/音乐,音量衰减 |
| `ScriptComponent` | Game | 承载 Lua 脚本(可选扩展) |

`Transform` 为值语义(struct),渲染/物理直接读写,不设组件访问开销。

### 4.3 渲染系统 Render

#### 4.3.1 渲染器 `Renderer2D`
- **单批次批量渲染**:所有精灵合并为 1 次 draw call
  - 输入:位置/旋转/缩放 + UV + 颜色
  - 按纹理 ID 排序,切换纹理时 flush;每帧 1~N 次 draw call
- 顶点格式:`[pos(2), uv(2), color(4)]` × 4 顶点/quad,16 字节对齐,GL_DYNAMIC_DRAW 环形缓冲
- 渲染状态严格管理:`begin_frame / flush / end_frame` 封装,避免状态泄漏

#### 4.3.2 纹理图集 `TextureAtlas`
- 精灵图集打包(运行时加载 `assets/atlas.json` + png)
- UV 预计算,`SpriteRenderer` 只需 `atlas_id + frame_index`
- 提供打包工具 `tools/atlas_packer`(命令行,纹理排布算法:简单贪心 + shelf 算法)

#### 4.3.3 相机 `Camera`
- 正交投影,`zoom` 支持
- `SetFollow(target, lerp_speed)` 平滑跟随
- `AddShake(intensity, duration)` 屏幕抖动
- 坐标约定:世界 Y 轴向上,屏幕 Y 向下,由矩阵转换

#### 4.3.4 渲染顺序与分层
- 层序(Layer):`Background(-100) < Tilemap(0) < World(100) < UI(1000)`
- 同层内按 `sortOrder`(int) 排序,再按纹理 ID 合并批次
- 渲染管线:场景视口(Game 相机)→ 粒子 → 编辑器叠加层(ImGui)

#### 4.3.5 粒子系统 `ParticleSystem`
- 发射器参数:发射速率、初始速度范围、重力、颜色渐变、尺寸曲线、寿命
- 粒子存储在池中(4.1.5),按尺寸/颜色分段 batch 渲染(点精灵或四边形)
- 全部 GPU 无关,CPU 模拟,目标并发 5000 粒子 @60fps

#### 4.3.6 Shader 管理
- 内置着色器:默认精灵(shader)、网格线(编辑器)、粒子
- `ShaderProgram` 封装 compile/link/uniform 设置,文本缓存避免重复编译

### 4.4 物理系统 Physics

#### 4.4.1 形状与组件
- `BoxCollider`(AABB,带 offset)/ `CircleCollider`(半径 + offset)
- `RigidBody`:`velocity、mass、gravity_scale、restitution(弹力)、friction、is_static`
- 静态碰撞体(地面/墙体):无 RigidBody 或 `is_static=true`

#### 4.4.2 碰撞流程(每固定步长)
```
1. 积分:更新刚体位置(速度 × dt + 重力)
2. 宽相位:空间哈希网格(AABB 粗检测)
   - 网格单元 64px,动态物体只与邻近单元检测,复杂度 O(n+k)
3. 窄相位:AABB-AABB / AABB-Circle / Circle-Circle 精确检测
4. 求解:最小平移向量(MTV)位置修正 + 速度反弹(弹性系数)
5. 事件:OnCollisionEnter/Stay/Exit 经 EventBus 广播
```

#### 4.4.3 限制与约定
- 仅支持矩形/圆形,不支持多边形、关节、旋转碰撞
- 每步最多 2 次位置迭代,防止隧道效应;高速物体(> 2×网格单元/步)做扫掠检测(swept)
- 物理在固定步长中运行,与渲染插值配合(见 3)

### 4.5 音频系统 Audio

| 类 | 职责 |
|---|---|
| `AudioManager` | 初始化 SDL_mixer(48kHz/32ch)、加载解码、全局音量/静音、**音乐流切换**(淡入淡出) |
| `AudioSource` | 组件,播放/暂停/停止、循环、音量、3D 衰减(按与 Camera 距离,线性衰减到 0) |
| `SoundAsset` | 短音效,WAV/OGG,预解码常驻内存 |

- 音效上限 32 并发通道,超出按优先级丢弃新音
- 资源由 ResourceManager 统一管理(见 4.6)

### 4.6 资源系统 Resource

#### 4.6.1 资源类型
| 类型 | 扩展 | 加载器 |
|---|---|---|
| Texture | png/jpg | stb_image 解码 → GL 纹理 |
| Sound | wav/ogg | SDL_mixer |
| Font | ttf | stb_truetype(位图化) |
| Tilemap | json + atlas | 自研解析 |
| Scene | json | 自研序列化 |

#### 4.6.2 `ResourceManager` 设计
```cpp
template<typename T> T* Load(const std::string& path);   // 带缓存 + 引用计数
template<typename T> void Unload(const std::string& path);
void LoadAsync(paths, callback);   // 后台线程加载,主线程完成注册
std::vector<AssetMeta> ListAssets(dir);  // 资源浏览器用
```
- 全局单例,`assets/` 目录为根,路径统一相对
- 异步加载:加载任务线程池(2 线程),完成回调投递到主线程队列,下一帧执行
- **Hot reload**(编辑器模式):文件 mtime 监控,纹理/场景修改后自动重载,编辑器实时刷新

### 4.7 场景系统 Scene

#### 4.7.1 场景结构
- `Scene`:实体根列表、背景色、启用系统开关、物理/渲染参数
- 实体父子层级:子实体继承父变换(transform 级联)
- API:`CreateEntity(name) / DestroyEntity(obj) / FindByName(name)`

#### 4.7.2 Prefab(预制体)
- 场景 JSON 中可引用 `prefabs/xxx.json` 作为实体模板
- 实例化:模板深拷贝 + 实例字段覆盖表(按组件路径)
- 修改 Prefab → 所有实例同步(未覆盖字段)

#### 4.7.3 场景序列化格式(JSON)
```json
{
  "version": 1,
  "name": "Level1",
  "background": [0.1, 0.1, 0.15],
  "entities": [
    {
      "id": "player",
      "name": "Player",
      "parent": null,
      "transform": { "pos": [0, 0], "rot": 0, "scale": [1, 1] },
      "components": [
        { "type": "SpriteRenderer",
          "atlas": "hero", "frame": 0, "layer": 100, "sortOrder": 0 },
        { "type": "RigidBody", "velocity": [0,0], "gravityScale": 1.0 },
        { "type": "BoxCollider", "size": [32, 48], "offset": [0, 0] }
      ]
    },
    { "id": "enemy_1", "name": "Enemy", "parent": "player",
      "prefab": "prefabs/enemy.json", "overrides": { "transform.pos": [10, 0] } }
  ]
}
```

#### 4.7.4 保存/加载
- 编辑器 Ctrl+S → 全量序列化(保持当前字段值)
- 加载失败:报错列出路径 + 行号,场景不崩溃回退到空场景

### 4.8 编辑器 Editor(ImGui)

| 面板 | 功能 |
|---|---|
| **Viewport 视口** | 游戏画面渲染到 ImGui 纹理;平移(中键)/缩放(滚轮);Gizmo 拖拽(移动/旋转/缩放) |
| **Hierarchy 层级** | 实体树,拖拽调整父子;右键菜单(新建/复制/删除/添加组件) |
| **Inspector 属性** | 选中实体的 Transform + 组件字段编辑(数值/纹理选择/布尔),即时生效 |
| **Assets 资源浏览器** | 目录树 + 预览缩略图;拖拽资源到视口创建实体 |
| **Toolbar 工具栏** | 播放/暂停/单帧、保存/加载场景、开关系统(物理/粒子/音频) |
| **Console 控制台** | 引擎日志(4.1.3)实时显示,点击跳转到来源 |

**编辑器与运行时关系**:
- 编辑器模式 = 引擎完整运行 + 覆盖层 GUI,无代码生成,场景即数据
- 播放时实体变更同步回编辑器(两态同步,标记 dirty 后合并)

### 4.9 脚本系统(可选扩展,Phase 3)
- sol2 绑定:暴露 `Vec2 / GameObject / Component 通用访问 / Input / Scene API`
- 组件 `ScriptComponent`:绑定 Lua 文件,回调 `update/draw/collide`
- 编辑器内嵌 Lua 控制台(可执行任意引擎命令)

---

## 5. 目录结构

```
game-engine/
├── CMakeLists.txt                  # 顶层:runtime / editor / tools 目标
├── DESIGN.md
├── engine/
│   ├── core/
│   │   ├── math.h                  # Vec2/Mat3/Rect/插值
│   │   ├── time.h                  # TickTimer, Time 全局
│   │   ├── logger.h                # 分级日志
│   │   ├── event.h                 # EventBus
│   │   ├── pool_allocator.h        # 对象池
│   │   └── platform.h              # 平台宏(win/linux/mac)
│   ├── platform/
│   │   ├── window.h                # SDL 窗口 + GL context
│   │   └── window_sdl.cpp
│   ├── ecs/
│   │   ├── gameobject.h            # GameObject / Transform
│   │   ├── component.h             # Component 基类
│   │   ├── scene.h                 # Scene:实体管理
│   │   └── scene.cpp
│   ├── render/
│   │   ├── renderer2d.h/.cpp       # 批处理渲染器
│   │   ├── shader.h/.cpp           # GLSL 程序封装
│   │   ├── texture.h/.cpp          # stb_image 加载 + GL 纹理
│   │   ├── texture_atlas.h/.cpp    # 图集管理
│   │   ├── camera.h/.cpp
│   │   ├── tilemap.h/.cpp
│   │   └── particle_system.h/.cpp
│   ├── physics/
│   │   ├── collider.h/.cpp         # Box/Circle 碰撞体
│   │   ├── rigidbody.h/.cpp
│   │   ├── spatial_hash.h/.cpp     # 宽相位
│   │   └── physics_world.h/.cpp    # 求解 + 事件广播
│   ├── audio/
│   │   ├── audio_manager.h/.cpp    # SDL_mixer 封装
│   │   └── audio_source.h/.cpp     # 组件
│   ├── input/
│   │   ├── input_manager.h/.cpp    # 三态按键/鼠标
│   │   └── input_map.h/.cpp        # 动作映射
│   ├── resource/
│   │   ├── resource_manager.h/.cpp # 缓存 + 引用计数 + 异步
│   │   ├── asset_types.h           # Texture/Sound/Font 元数据
│   │   └── hot_reload.h/.cpp       # mtime 监控(编辑器)
│   ├── scene/
│   │   ├── prefab.h/.cpp
│   │   └── serializer.h/.cpp       # Scene ↔ JSON
│   └── editor/
│       ├── editor_app.h/.cpp       # ImGui 初始化 + 面板布局
│       ├── viewport_panel.h/.cpp
│       ├── hierarchy_panel.h/.cpp
│       ├── inspector_panel.h/.cpp
│       ├── assets_panel.h/.cpp
│       └── gizmo.h/.cpp            # ImGuizmo 集成
├── sandbox/
│   ├── main.cpp                    # 示例游戏入口(可切换 runtime/editor)
│   └── game_scene.json
├── tools/
│   └── atlas_packer/               # 图集打包命令行工具
├── assets/
│   ├── textures/   # png
│   ├── audio/      # wav/ogg
│   ├── fonts/      # ttf
│   ├── scenes/     # json
│   ├── prefabs/    # json
│   └── atlas.json
└── third_party/                    # FetchContent 管理
    ├── SDL2 / SDL_mixer / imgui / nlohmann_json / stb / sol2
```

---

## 6. 关键接口示例

### 6.1 Renderer2D 核心 API
```cpp
class Renderer2D {
public:
    void begin_frame(Mat3 view_proj);
    void draw_sprite(Texture* tex, Vec2 pos, float rot, Vec2 scale,
                     const Rect& uv, Vec4 color, int layer, int sort_order);
    void draw_circle(Vec2 center, float radius, Vec4 color, int segments = 32);
    void draw_text(Font* font, const char* text, Vec2 pos, float size, Vec4 color);
    void flush();
    void end_frame();
};
```

### 6.2 示例:玩家创建(沙盒)
```cpp
GameObject* player = scene.CreateEntity("player");
player->transform.pos = { 0, 0 };

auto* spr = player->AddComponent<SpriteRenderer>();
spr->atlas = res.Load<TextureAtlas>("atlas.json");
spr->frame = 0;

auto* rb = player->AddComponent<RigidBody>();
rb->gravity_scale = 1.0f;

auto* col = player->AddComponent<BoxCollider>();
col->size = { 32, 48 };
```

---

## 7. 开发里程碑(9 阶段,每阶段可运行验证)

| 阶段 | 目标 | 验收标准 | 预计规模 |
|---|---|---|---|
| **M1** | 工程骨架 | CMake 构建成功;窗口 + GL 上下文;清屏 + 三角形;日志/FPS 显示 | ~500 行 |
| **M2** | 核心循环 + 实体 | 固定步长循环;Scene/GameObject/Component;旋转方块动画 | ~1200 行 |
| **M3** | 渲染批处理 | 纹理加载 + 图集 + Renderer2D;相机平移缩放;**1 万精灵 @60fps**(单批 <10 draw call) | ~2000 行 |
| **M4** | 输入 + 资源管理 | 键盘/鼠标三态;InputMap 动作绑定;异步加载 + 缓存;Hot reload | ~1500 行 |
| **M5** | 物理 | 空间哈希宽相位 + 窄相位;刚体积分;**1000 圆球堆积稳定不抖**;碰撞事件 | ~2500 行 |
| **M6** | 音频 | SFX 播放/循环/3D 衰减;BGM 淡入淡出;撞击触发音效 | ~800 行 |
| **M7** | 场景序列化 | JSON 保存/加载往返一致;Prefab 实例化 + 覆盖 | ~1500 行 |
| **M8** | 编辑器 | 视口/层级/属性面板/Gizmo;播放暂停;拖拽资源创建实体;场景保存 | ~3000 行 |
| **M9** | 示例游戏 | **平台跳跃小游戏**(移动/跳跃/砖块/敌人/音效/关卡场景),编辑器内完整制作 | ~1500 行 |

**总规模预估**:~1.4 万行引擎 + ~1500 行示例,单人 2~3 个月可完成。

### 风险与对策
| 风险 | 对策 |
|---|---|
| 批处理渲染性能不达标 | M3 单独验收(1 万精灵 @60fps);必要时引入纹理图集自动合并 + 缓存排序 |
| 碰撞隧道/抖动 | 固定步长 + 扫掠检测 + 位置迭代上限;M5 用 1000 球堆积压力测试 |
| 编辑器与运行状态同步复杂 | 编辑器即运行时,无两套状态;用 dirty 标记 + 统一序列化通道 |
| 跨平台(尤其 macOS GL) | 统一 GL3.3 Core + 不使用已废弃 API;CI 三平台构建 |

---

## 8. 后续扩展方向(本方案范围外)
- 粒子 GPU 化 / 自定义 Shader 支持(材质系统)
- 动画状态机(Animator,AnimationClip 资产)
- Lua 脚本生态完善 + 热重载脚本
- 物理升级:多边形碰撞、关节、CCD
- 打包发布:资源加密、平台导出(Windows 安装包等)
- 图元绘制:线段/贝塞尔曲线、复杂 UI 系统
