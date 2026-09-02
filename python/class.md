# Python Class（类）知识总结

## 1. 什么是类？

类（Class）是**创建对象的模板/蓝图**，定义了对象拥有的属性（数据）和方法（行为）。

生活类比：
- 类 = 汽车设计图纸
- 对象 = 根据图纸造出来的具体汽车

---

## 2. 基本语法

```python
class Dog:
    def __init__(self, name):  # 构造函数，创建对象时自动执行
        self.name = name       # self = 对象自身，self.name = 属性

    def bark(self):            # 方法（函数绑在类里）
        print(f"{self.name}: 汪汪！")

# 创建对象（实例化）
dog1 = Dog("旺财")
dog2 = Dog("小白")

dog1.bark()  # → "旺财: 汪汪！"
dog2.bark()  # → "小白: 汪汪！"
```

---

## 3. 核心概念

### 3.1 `__init__` 构造函数

对象被创建时自动调用，用于初始化属性：

```python
class Person:
    def __init__(self, name, age):
        self.name = name    # 公有属性
        self.__age = age    # 私有属性（双下划线前缀）

p = Person("张三", 25)
print(p.name)   # "张三"
```

### 3.2 `self` 关键字

- `self` 代表**对象自身**
- 每个实例方法的第一个参数必须是 `self`
- 调用时不需要传 `self`，Python 自动传入

```python
class Counter:
    def __init__(self):
        self.count = 0       # 用 self 绑定到对象上

    def add(self):
        self.count += 1      # 每次调用修改同一个对象的状态

c = Counter()
c.add()
c.add()
print(c.count)  # 2
```

### 3.3 属性 vs 方法

| 类型 | 定义方式 | 示例 |
|------|---------|------|
| 属性 | `self.xxx = value` | `self.name = "张三"` |
| 方法 | `def method(self):` | `def greet(self):` |

---

## 4. 类的三大特性（OOP）

### 4.1 封装

把数据和操作绑在一起，隐藏内部细节：

```python
class BankAccount:
    def __init__(self, balance):
        self.__balance = balance    # 私有，外部不能直接访问

    def deposit(self, amount):      # 通过公开方法操作
        self.__balance += amount

    def get_balance(self):
        return self.__balance

acc = BankAccount(1000)
acc.deposit(500)
print(acc.get_balance())  # 1500
# print(acc.__balance)    # 报错！外部无法直接访问
```

### 4.2 继承

子类继承父类的属性和方法，可以扩展或重写：

```python
class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        print("...")

class Dog(Animal):              # Dog 继承 Animal
    def speak(self):            # 重写父类方法
        print(f"{self.name}: 汪汪！")

class Cat(Animal):
    def speak(self):
        print(f"{self.name}: 喵~")

dog = Dog("旺财")
cat = Cat("小花")
dog.speak()  # "旺财: 汪汪！"
cat.speak()  # "小花: 喵~"
```

### 4.3 多态

同一个方法，不同对象有不同行为：

```python
animals = [Dog("旺财"), Cat("小花")]
for a in animals:
    a.speak()   # 同样调用 speak()，结果不同
```

---

## 5. 常用特殊方法（魔术方法）

| 方法 | 作用 | 何时触发 |
|------|------|---------|
| `__init__(self)` | 初始化属性 | `obj = MyClass()` |
| `__str__(self)` | 定义 `print(obj)` 的输出 | `print(obj)` |
| `__repr__(self)` | 定义调试时的字符串表示 | 在交互式终端显示 |
| `__len__(self)` | 定义 `len(obj)` 的行为 | `len(obj)` |
| `__eq__(self, other)` | 定义 `==` 的行为 | `obj1 == obj2` |

```python
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return f"Point({self.x}, {self.y})"

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

p1 = Point(1, 2)
p2 = Point(1, 2)
print(p1)          # "Point(1, 2)"
print(p1 == p2)    # True
```

---

## 6. 与 C 语言 struct 的对比

| | C struct | Python class |
|---|---------|-------------|
| 数据 | ✅ 有 | ✅ 有（`self.xxx`） |
| 方法/函数 | ❌ 没有，写在外面 | ✅ 绑在一起 |
| 继承 | ❌ 没有 | ✅ 可以继承扩展 |
| 访问控制 | ❌ 无 | ⚠️ 有（公有/私有约定） |
| 本质 | 内存布局的描述 | 数据 + 行为的封装体 |

```c
// C struct：只有数据
struct CTFagent {
    char* api_key;
    int   tool_count;
};

// Python class：数据 + 行为
class CTFagent:
    def __init__(self):
        self.api_key = "sk-xxx"
        self.tool_count = 3

    def solve(self, task):    # 自带行为
        ...
```

---

## 7. 类变量 vs 实例变量

```python
class Dog:
    species = "犬科"          # 类变量：所有对象共享

    def __init__(self, name):
        self.name = name      # 实例变量：每个对象独有

d1 = Dog("旺财")
d2 = Dog("小白")

print(d1.species)  # "犬科"  （访问类变量）
print(d2.species)  # "犬科"  （同一个）
print(d1.name)     # "旺财"  （自己的）
print(d2.name)     # "小白"  （自己的）
```

---

## 8. 实际应用：Agent 中的 class

```python
class CTFagent:
    def __init__(self):              # 初始化：连接 LLM、注册工具
        self.client = OpenAI(...)
        self.tools = []

    def register_tool(self, ...):    # 方法：注册工具
        self.tools.append({...})

    def solve(self, task):           # 方法：核心循环
        ...
```

用 class 把 LLM 客户端、工具列表、提示词**打包成一个整体**，逻辑清晰、方便复用。
