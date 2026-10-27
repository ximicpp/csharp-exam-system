// Q219 · 源生成器与分析器的分工（考试第 99 题）

using System.Collections.Immutable;
using System.Text;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;
using Microsoft.CodeAnalysis.Diagnostics;
using Microsoft.CodeAnalysis.Text;

internal static partial class Question
{
    private static async Task<(int Added, bool OriginalPreserved, bool Emitted, int Reported)> Observe()
    {
        const string original = "public partial class lowerCase { }";
        SyntaxTree input = CSharpSyntaxTree.ParseText(original);
        var compilation = CSharpCompilation.Create("GeneratedDemo", [input],
            [MetadataReference.CreateFromFile(typeof(object).Assembly.Location)],
            new CSharpCompilationOptions(OutputKind.DynamicallyLinkedLibrary));

        GeneratorDriver driver = CSharpGeneratorDriver.Create(new DemoGenerator());
        driver = driver.RunGeneratorsAndUpdateCompilation(compilation, out Compilation updated, out _);
        using var output = new MemoryStream();
        bool emitted = updated.Emit(output).Success;
        ImmutableArray<Diagnostic> diagnostics = await updated.WithAnalyzers(
            ImmutableArray.Create<DiagnosticAnalyzer>(new NameAnalyzer())).GetAnalyzerDiagnosticsAsync();
        return (driver.GetRunResult().GeneratedTrees.Length, input.ToString() == original, emitted,
            diagnostics.Count(d => d.Id == "EXAM001"));
    }
}

[Generator]
internal sealed class DemoGenerator : ISourceGenerator
{
    public void Initialize(GeneratorInitializationContext context) { }
    public void Execute(GeneratorExecutionContext context) => context.AddSource("GeneratedValue.g.cs",
        SourceText.From("public partial class lowerCase { public int Value => 42; }", Encoding.UTF8));
}

[DiagnosticAnalyzer(LanguageNames.CSharp)]
internal sealed class NameAnalyzer : DiagnosticAnalyzer
{
    private static readonly DiagnosticDescriptor Rule = new("EXAM001", "Type name", "Type name should start with uppercase",
        "Naming", DiagnosticSeverity.Warning, isEnabledByDefault: true);
    public override ImmutableArray<DiagnosticDescriptor> SupportedDiagnostics => [Rule];
    public override void Initialize(AnalysisContext context)
    {
        context.ConfigureGeneratedCodeAnalysis(GeneratedCodeAnalysisFlags.None);
        context.EnableConcurrentExecution();
        context.RegisterSyntaxNodeAction(node =>
        {
            var declaration = (ClassDeclarationSyntax)node.Node;
            if (char.IsLower(declaration.Identifier.ValueText[0]))
                node.ReportDiagnostic(Diagnostic.Create(Rule, declaration.Identifier.GetLocation()));
        }, SyntaxKind.ClassDeclaration);
    }
}
