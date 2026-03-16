---
name: julia-dev
description: General Julia development practices — Pkg.jl package management, testing with Test.jl, code formatting (BlueStyle), static analysis (JET.jl, Aqua.jl), package creation, documentation, and C/Fortran/Python interop. Use whenever setting up a Julia project, writing tests, creating packages, managing dependencies, or asking about Julia tooling and development workflows.
---

## Package Management

Manage dependencies exclusively through Pkg.jl — never edit Project.toml by hand, because Pkg maintains internal consistency between Project.toml and Manifest.toml that manual edits can break.

```julia
# In Pkg REPL (press ] in REPL)
add DifferentialEquations
rm UnusedPackage

# Or programmatically
import Pkg
Pkg.add("DifferentialEquations")
```

- Use project-local environments (`Project.toml` + `Manifest.toml`) for reproducibility
- Use `Pkg.instantiate()` to reproduce an environment from a Manifest
- Package extensions (Julia 1.9+) for optional dependencies — avoids bloating load time
- Commit both `Project.toml` and `Manifest.toml` for applications; only `Project.toml` for libraries

## Development Workflow

- **Revise.jl**: Load with `using Revise` before your package for automatic code reloading — avoids restarting Julia after every edit
- **REPL-driven development**: Test ideas interactively, then move working code into functions
- **Precompilation caching**: Julia caches compiled code between sessions; use `PrecompileTools.jl` workloads to reduce time-to-first-execution for package users

## Code Formatting

Format all code with **JuliaFormatter.jl** using **BlueStyle**:

```julia
using JuliaFormatter
format("src/", BlueStyle())
```

BlueStyle key conventions:
- 4-space indentation
- Trailing commas in multi-line expressions
- Short-form functions for one-liners: `f(x) = 2x`
- Long-form for anything with branches or multiple statements

## Static Analysis

- **JET.jl**: Catch type errors and method-not-found issues without running the code. Run `@report_opt f(args...)` for optimization suggestions and `@report_call f(args...)` for correctness.
- **Aqua.jl**: Package-level quality checks — unbound type parameters, ambiguities, piracy detection, stale dependencies. Run `Aqua.test_all(MyPackage)` in your test suite.

## Testing

Use `Test.jl` with organized test sets:

```julia
using Test

@testset "MyModule" begin
    @testset "feature A" begin
        @test f(1) == 2
        @test_throws ArgumentError f(-1)
    end
end
```

- **BenchmarkTools.jl**: `@btime` / `@benchmark` for performance regression testing
- **PropCheck.jl**: Property-based testing for edge case discovery
- **Coverage.jl**: Track test coverage in CI
- **Documenter.jl**: Docstring examples run as tests via `doctest=true`
- CI with GitHub Actions — use `julia-actions/setup-julia`

## Package Development

Create new packages with **PkgTemplates.jl**:

```julia
using PkgTemplates
t = Template(; plugins=[Git(), GitHubActions(), Documenter{GitHubActions}()])
t("MyPackage")
```

Standard project structure:
```
MyPackage/
├── src/MyPackage.jl
├── test/runtests.jl
├── docs/
├── Project.toml
└── README.md
```

- Semantic versioning for compatibility
- `DocStringExtensions.jl` for consistent docstring templates
- `BinaryBuilder.jl` for wrapping C/Fortran libraries

## Interoperability

- **C/Fortran**: `ccall` / `@ccall` for direct calls — no wrapper needed for simple interfaces
- **Python**: `PythonCall.jl` (preferred over PyCall.jl) for bidirectional Python interop
- **R**: `RCall.jl` for R interop

## Style Guide

Distilled from the official Julia Style Guide. For the full version with examples, read `references/official-style-guide.md`.

### Naming Conventions
- Functions and variables: `lowercase` or `snake_case`
- Types and modules: `CamelCase`
- Constants: `UPPERCASE` or `CamelCase`
- Append `!` to functions that mutate their arguments (e.g. `sort!`, `push!`)
- Follow Julia Base naming patterns: `length`, `size`, `push!`, `empty!`

### Function Design
- Write functions, not scripts — code in functions runs faster and is testable
- Write generic signatures: prefer `addone(x) = x + oneunit(x)` over `addone(x::Int)`. Julia specializes automatically at compile time, so overly specific type annotations just limit reuse without gaining speed.
- Handle type conversion in the caller, not the callee: call `foo(Int(x))` instead of writing `foo(x) = (x = Int(x); ...)`
- Order arguments like Julia Base: destination/output first (for `!` functions), then function argument (for HOFs), then main input
- Don't overuse `try-catch` — check conditions before rather than catching errors after
- Don't parenthesize `if`/`while` conditions: `if x` not `if (x)`

### Type Design
- Avoid strange `Union`s — if you need `Union{Function, Nothing}`, consider a different design
- Avoid elaborate container types — keep type hierarchies simple
- Prefer exported methods over direct field access: users should call `get_name(obj)` not `obj.name`, because field layout is an implementation detail
- Don't use unnecessary static parameters — only add `where {T}` when `T` is actually used in the body
- Avoid type piracy (defining methods on types you don't own)
- Be careful with type equality: `isa(x, T)` and `T1 <: T2` are usually better than `typeof(x) == T`

### Documentation
- Write docstrings (not just inline comments) so they appear in `?help` and editors
- Use `DocStringExtensions.jl` for consistent templates

### Miscellaneous
- Don't overuse macros — a function is almost always clearer
- Don't expose unsafe operations at the interface level
- Don't overload methods of base container types (e.g. don't redefine `push!` for `Dict`)
- Don't write `x -> f(x)` when you can just pass `f` directly
- Avoid floats for numeric literals in generic code: use `oneunit(x)` instead of `1.0`

## Key Constraints

- Never edit Project.toml directly — always use Pkg REPL or Pkg.jl API
- Format code with JuliaFormatter.jl using BlueStyle
- Prefer immutable structs unless mutation is specifically needed
- Avoid type piracy — it breaks composability across packages
- Use parametric types for generic code instead of abstract type annotations on fields
