# 第 154 题 · Q154 · 事件重复订阅后的退订责任

原题号：`Q27`。工程编号与考试显示号一致。

题目项目使用 .NET 11 / C# 14，启用 nullable 与隐式 using；必要的额外 using 和入口在本题源码中提供。编译环境或配置另有指定时，以题干为准。

组件重复初始化两次，关闭时只退订一次；发布者寿命比组件更长。

执行 Q27 中的第一次 -= 和 Raise 后，若要解除该 handler 的全部事件注册，应采取哪项操作？这里是所示的普通字段式事件。

```csharp
private sealed class Publisher
{
    public event Action? Changed;
    public int SubscriptionCount => Changed?.GetInvocationList().Length ?? 0;
    public void Raise() => Changed?.Invoke();
}

private static (int Calls, int Remaining, int Final) Q27()
{
    var publisher = new Publisher();
    int calls = 0;
    Action handler = () => calls++;
    publisher.Changed += handler;
    publisher.Changed += handler;
    publisher.Changed -= handler;
    publisher.Raise();
    int remaining = publisher.SubscriptionCount;
    publisher.Changed -= handler;
    return (calls, remaining, publisher.SubscriptionCount);
}
```

- A. 无需继续退订，一次 -= 已移除该 handler 的全部注册。
- B. 再对保存的 handler 执行一次 -=，移除剩余注册。
- C. 只丢弃局部 handler 引用，发布者随后就不再引用它。
- D. 再调用一次 Raise，剩余注册会在回调执行后自动失效。

## 动手问题

- 在每次订阅、退订和触发事件的位置设断点，记录调用数与订阅数。将同一个委托改为分别创建的两个 lambda 后，退订行为是否相同？
