# 第 47 题 · Q47 · sealed override 与继续重写

原题号：`Q167`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

Leaf.Name 为什么无法编译？

```csharp
Console.WriteLine(new Base().Name());
class Base { public virtual string Name() => "base"; }
class Middle : Base { public sealed override string Name() => "middle"; }
class Leaf : Middle { public override string Name() => "leaf"; }
```

- A. Middle 类必须也被声明为 sealed。
- B. Middle.Name 是 sealed override，派生类不能继续 override 这个成员。
- C. C# 只允许一层继承。
- D. override 方法不能返回 string。
