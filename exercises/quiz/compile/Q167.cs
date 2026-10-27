#region Q167
Console.WriteLine(new Base().Name());
class Base { public virtual string Name() => "base"; }
class Middle : Base { public sealed override string Name() => "middle"; }
class Leaf : Middle { public override string Name() => "leaf"; }
#endregion
