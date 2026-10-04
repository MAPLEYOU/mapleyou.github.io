---
title: "Linux 内核没有 class，凭什么玩面向对象？"
date: 2026-10-04 13:40:00
tags:
  - Linux
  - C语言
  - 内核
  - 面向对象
categories:
  - 系统底层
cover: /img/linux-c-oo/cover.png
---

C 语言没有 `class`，没有 `extends`，也没有 `virtual`。

但 Linux 内核几千万行 C 代码里，到处都是"对象"：`struct device` 是所有设备的"基类"，`file_operations` 是"虚函数表"，`list_head` 是"泛型容器"。

这套面向对象不是语法糖，是纯手工搭出来的。核心就两样东西：**结构体内嵌 + 一个叫 `container_of` 的宏**。

这篇文章把这两件事讲透。所有结论都在本机实测过（GCC x86-64），完整可运行代码在文末仓库。

# 一、继承：把父类放在子类的第一个位置

先看最朴素的写法——父类结构体作为子类的**第一个成员**：

```c
struct base {                     /* 父类 */
    int type;
    void (*func)(struct base *self);
};

struct derived {                  /* 子类 */
    struct base base;             /* ★ 必须是第一个成员 */
    int         extra;
};
```

C 标准 6.7.2.1p15 有一条刚性规定：**结构体的地址等于其首成员的地址**。

于是下面这个等式恒成立：

```c
struct derived d;
(void *)&d == (void *)&d.base;    /* 永远为真 */
```

也就是说，父类视角和对象真实内存，看的是同一段地址：

![继承内存布局](/img/linux-c-oo/01.png)

子类指针随时可以当父类指针用——**这就是 C 语言继承的全部秘密**。

内核里最经典的是 TCP 栈的四层继承链，`sock → inet_sock → inet_connection_sock → tcp_sock`，每一层把父类放在首位，四个指针的地址完全相同。`struct sock` 里甚至留着一条注释，专门防止有人在这个首成员前面加字段。

**向上转型（子 → 父）因此是零成本的**。偏移恒为 0，转换就是指针原样传递，编译成汇编只剩一条参数搬运：

```asm
upcast_tcp_to_sock:
        mov     rax, rcx      ; 没有哪怕一条算术指令
        ret
```

# 二、反方向的问题：拿着父类指针，怎么找回子类

往上走免费，往下走就麻烦了。

内核里到处是父类指针：总线枚举到设备，把 `struct device *` 一路传进驱动的 probe 函数。可驱动真正要操作的，是自己的子类对象。

更麻烦的是，**父类成员不一定在子类首位**。真实的 `struct i2c_client` 里，`dev` 前面还有 `flags`、`addr`、`name` 等字段：

![为何不能直接强转](/img/linux-c-oo/02.png)

`offsetof(struct i2c_client, dev)` 实测等于 32。这时候直接 `(struct i2c_client *)dev` 会错位 32 字节——**编译器不报错、运行时不崩溃，读到的是垃圾数据**。这种 bug 是 C 语言里最难查的一类。

正确姿势就是 `container_of`：

```c
struct i2c_client *client = container_of(dev, struct i2c_client, dev);
```

一句话定义：**已知「成员地址 + 成员名 + 宿主类型」，反推出「宿主对象地址」**。名字里的 container 就是"容器"——装下这个成员的那个大结构体。

顺带纠正一个流传很广的说法：很多人管 `container_of` 叫"子类推导父类"，反了——它是**父类指针 → 子类指针**（向下转型）。方向只看指针类型从谁变到谁，跟内存地址高低没有关系：

![转型方向辨析](/img/linux-c-oo/03.png)

# 三、container_of 拆解：一个陷阱 + 三步

理解这个宏，只有一道门槛：**指针算术的步进单位**。

指针的「1」不是 1 字节，而是 1 个元素。`struct item *` 类型的 `p - 1`，退的是 `sizeof(struct item)` 字节。如果你需要的是"退 4 字节"，直接减就错了：

![指针步进陷阱](/img/linux-c-oo/04.png)

所以必须先把指针**降级成字节指针**，换一把"数字节"的尺子。想通这一点，`container_of` 剥掉所有包装后其实就三步：

![三步拆解](/img/linux-c-oo/05.png)

① **降级**：`(void *)ptr`，擦掉类型，把步进单位换成字节

② **减偏移**：`- offsetof(type, member)`，按字节后退 N 步

③ **还原**：`(type *)` 转回目标类型

内核原版宏长这样：

```c
#define container_of(ptr, type, member) ({                              \
        void *__mptr = (void *)(ptr);                                   \
        _Static_assert(__builtin_types_compatible_p(                    \
                __typeof__(*(ptr)), __typeof__(((type *)0)->member)),   \
                "container_of: pointer type mismatch");                 \
        ((type *)(__mptr - offsetof(type, member))); })
```

看起来吓人，拆开就三个零件：

- `({ ... })` 是 **GCC 语句表达式**扩展：允许在表达式位置写语句块，块内最后一条语句的值就是整个表达式的值
- `void *__mptr` 就是上面的"换刻度"
- `_Static_assert` + `__builtin_types_compatible_p` 做**编译期类型防呆**，传错类型直接编译不过

算法只有最后那一行。标准 C 版本一行就够，任何编译器都能用：

```c
#define container_of(ptr, type, member) \
    ((type *)((char *)(ptr) - offsetof(type, member)))
```

**内核原版宏只在 `.c` 文件 + GCC/Clang 下成立**——语句表达式和 `_Static_assert` 在 MSVC、C++ 模式下都不认（C++ 里叫 `static_assert`）。拿去编译会收获一堆语法错误，正确做法是条件编译降级到标准版。这也顺便解释了为什么内核全是 `.c` 文件。

# 四、汇编验证：开销到底多大

![双向转换与汇编证据](/img/linux-c-oo/06.png)

`gcc -O2 -masm=intel -S` 实测：

```asm
upcast_tcp_to_sock:              ; 向上转型
        mov     rax, rcx         ; 零算术
        ret

downcast_dev_to_client:          ; 向下转型 = container_of
        lea     rax, -32[rcx]    ; 全部开销就是这一条减法
        ret
```

`-32` 正是 `offsetof(struct i2c_client, dev)`，编译期就算好了，不产生任何运行时计算。

**成本模型一句话：继承本身完全免费，只有"从父类找回子类"要付一条减法。**

# 五、多态：手写一张虚表

继承解决"是什么"，多态解决"怎么动"。C 的答案是函数指针表：

![虚表多态](/img/linux-c-oo/07.png)

```c
struct animal_ops {                               /* 虚函数表 */
    void (*speak)(struct animal *self);
    void (*move) (struct animal *self, int dx, int dy);
};

struct animal {                                   /* 父类 */
    const struct animal_ops *ops;                 /* vptr */
    char name[16];
};
```

调用方只认父类接口：`a->ops->speak(a)`——手动把 `this` 传进去，查表跳转。实现方在函数内部用 `container_of` 拿回子类视野，否则访问不到子类独有字段。

这套结构跟 C++ `virtual` 编译出来的东西**一模一样**。内核代表是 `file_operations`、`net_device_ops`，VFS 靠它撑起"一切皆文件"。

# 六、list_head：一套链表管住全内核

最后看 `container_of` 最漂亮的用法。内核链表节点里**不含任何数据**，只有两个指针：

```c
struct list_head { struct list_head *next, *prev; };
```

正因为它不带数据，才能挂进任意宿主结构的**任意位置**——首位、中间都行：

![list_head 通用链表](/img/linux-c-oo/08.png)

遍历宏 `list_for_each_entry` 里从头到尾**没有出现过宿主类型**，每走一步都靠 `container_of` 从节点反推宿主指针。所以同一套链表代码，管理着全内核所有不同类型的链表。

# 七、踩坑清单

拿小本本记好这几条：

- **父类不在首位还强转**：静默读错内存，编译器不报错。用 `container_of`，或老实写 `&d->base`
- **忘了先转 `char *` / `void *`**：退错 `sizeof` 倍的距离。记住"换刻度"
- **以为有运行时校验**：C 没有 RTTI，`container_of` 零校验，转错类型不报错
- **拿 MSVC / C++ 编内核原版宏**：语法错误一箩筐，条件编译降级到标准版

# 写在最后

C 的面向对象没有编译器帮忙，每一层都是透明的：继承是内存布局的约定，多态是函数指针的约定，向下转型是一次显式的指针减法。

也正因为透明，你能在汇编里亲眼看到每一次转型的代价——这种确定性，恰恰是 C 语言的浪漫。

完整可运行代码（继承链 / container_of 拆解 / 汇编验证 / 对齐规则，4 个 demo 全部带注释）已开源：

**github.com/MAPLEYOU/linux-c-oo**

如果这篇对你有帮助，也可以在微信搜一搜「码尘飞扬社」找到我——ISP 图像处理、音视频、后台开发的硬核笔记都会同步更新。
