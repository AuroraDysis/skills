---
name: julia-performance
description: Julia performance optimization guide — type stability, allocation reduction, memory layout, SIMD, profiling, and performance annotations. Use whenever writing or reviewing Julia code for performance, diagnosing slow Julia code, reducing allocations, or asking about @code_warntype, @inbounds, @fastmath, @simd, type instability, or Julia profiling.
---

Distilled from the official Julia Performance Tips. For detailed examples and edge cases, read `references/official-performance-tips.md`. For general Julia development practices, see the `julia-dev` skill. For PDE/ODE solving packages, see the `julia-pde` skill.

## Core Principle

Julia's compiler generates fast code when it can **infer concrete types at compile time**. Most performance problems trace back to the compiler not knowing a type — leading to heap allocations, boxing, and dynamic dispatch. When you see unexpected allocations in `@time` output, suspect a type problem first.

## General Rules

### Keep performance-critical code inside functions
Top-level code runs in global scope where the compiler cannot optimize effectively. Wrap hot paths in functions and pass data as arguments.

### Eliminate untyped globals
Global variables can change type at any time, blocking compiler optimization. Fix with:
- `const` for true constants: `const DT = 0.01`
- Type annotation for typed globals: `x::Float64 = 1.0`
- Passing values as function arguments (preferred — more reusable)

### Measure before optimizing
- Use `@time` (run twice — first call includes compilation) to spot unexpected allocations
- Use `BenchmarkTools.@btime` / `@benchmark` for reliable microbenchmarks
- Unexpected heap allocations almost always signal a type-stability problem

## Type Stability

The single most important optimization axis in Julia. A function is "type-stable" when the compiler can predict the return type from the argument types alone.

### Return consistent types
```julia
# Bad — returns Int or Float64 depending on value
pos(x) = x < 0 ? 0 : x

# Good — always returns same type as x
pos(x) = x < 0 ? zero(x) : x
```
Use `zero(x)`, `oneunit(x)`, `oftype(x, y)` to keep types consistent.

### Don't change variable types mid-function
```julia
# Bad — x starts Int, becomes Float64
x = 1
for i = 1:10; x /= rand(); end

# Good — x is Float64 from the start
x = 1.0
for i = 1:10; x /= rand(); end
```

### Use concrete type parameters in structs
```julia
# Bad — compiler cannot infer field type
struct Wrapper
    f::Function    # abstract type
    a::AbstractVector  # abstract container
end

# Good — parametric, fully concrete at construction
struct Wrapper{F, A<:AbstractVector}
    f::F
    a::A
end
```
This applies to all fields: avoid `Any`, `Function`, `AbstractArray`, `Real` as field types. Use type parameters instead. The same rule applies to container elements — `Vector{Float64}` is far faster than `Vector{Real}`.

### Function barriers (kernel functions)
When a type is determined at runtime (e.g. from a file or user input), isolate the type-unstable setup from the hot loop by calling a separate kernel function. Julia re-specializes at function boundaries:
```julia
function process(data)
    # Type determined at runtime — unstable
    T = eltype(data)
    _process_kernel(data, zero(T))  # barrier: kernel sees concrete types
end

function _process_kernel(data, init)
    s = init
    for x in data; s += x; end
    s
end
```

### Use `@code_warntype` to diagnose
Run `@code_warntype f(args...)` and look for red/uppercase `Union` or `Any` types in the output. These indicate type instability. Common patterns:
- `Body::Union{T1,T2}` → unstable return type
- `Any` on a `getfield` → abstract struct field
- `Union` on a `getindex` → poorly typed container

### Closures and captured variables
Captured variables that are reassigned get boxed (heap-allocated as `Any`). Fix with:
- Type annotation on the variable: `r::Int = r0`
- `let` block to create an unboxed copy: `f = let r = r; x -> x * r; end`

### Force specialization when Julia skips it
Julia avoids specializing on `Type`, `Function`, and `Vararg` arguments by default. Force it with a type parameter:
```julia
# Won't specialize on f
apply(f, x) = f(x)

# Will specialize — each callable type gets its own compiled version
apply(f::F, x) where {F} = f(x)
```

## Memory & Arrays

### Use StaticArrays.jl for small fixed-size data
For arrays with known small size (< 100 elements), `SVector` / `SMatrix` from StaticArrays.jl are stack-allocated and allow the compiler to unroll operations completely. Common in geometry (3D vectors), small matrix operations, and stencil computations.

### Use FastBroadcast.jl for performance-critical broadcasts
The `@..` macro compiles broadcasts into more compiler-friendly loops with optional threading support. Gives ~4x speedup for static broadcasts where array dimensions align. Not effective for dynamic broadcasts with singleton dimension expansion.

### Pre-allocate and mutate in-place
Use `!` convention functions that write into pre-allocated buffers instead of allocating new arrays each call:
```julia
# Allocates every call
result = compute(x)

# Pre-allocate once, reuse
buf = similar(x)
compute!(buf, x)  # writes into buf
```
Use `x .= f.(y)` for fused in-place broadcast.

### Use `@views` for slices
`array[1:5, :]` copies data. Wrap with `@views` to avoid the copy:
```julia
@views function f(x)
    s = sum(x[2:end-1])  # no copy, just a SubArray reference
    ...
end
```
Exception: when you access the same irregular slice many times, copying to a contiguous array can be faster due to cache locality.

### Fuse broadcasts with dot syntax
```julia
# Bad — 3 temporary arrays, 3 separate loops
y = 3 .* x.^2 .+ 4 .* x .+ 7 .* x.^3

# Good — single fused loop, one output array
@. y = 3x^2 + 4x + 7x^3
```
But beware over-fusion: if a sub-expression is constant along one axis of a multidimensional broadcast, pre-compute it to avoid redundant work.

### Access arrays in column-major order
Julia stores arrays column-major (like Fortran). Iterate with the first index varying fastest:
```julia
# Fast — column-major access
for col in axes(A, 2), row in axes(A, 1)
    A[row, col] = ...
end

# Slow — row-major access
for row in axes(A, 1), col in axes(A, 2)
    A[row, col] = ...
end
```

### Multithreading + BLAS
When using Julia threads alongside linear algebra, set `OPENBLAS_NUM_THREADS=1` to prevent thread oversubscription. Each Julia thread calling BLAS otherwise contends for the same OpenBLAS thread pool. Consider MKL.jl or AppleAccelerate.jl as alternative backends.

## Performance Annotations

Use these in **verified** hot loops only — they trade safety for speed:

- **`@inbounds`**: Skip bounds checking. Use only when you are certain indices are valid. Prefer `eachindex(x)` over `1:length(x)` for safe iteration.
- **`@fastmath`**: Allow IEEE-unsafe floating-point reordering (e.g. hoist `1/(2*dx)` out of loops). Breaks `NaN`/`Inf` handling — `@fastmath isnan(NaN)` returns `false`.
- **`@simd`**: Promise loop iterations are independent for vectorization. Only needed when auto-vectorization fails (e.g. floating-point re-association).

These compose: `@fastmath @inbounds @simd for i in eachindex(u) ... end`

## Miscellaneous

- **`abs2(z)`** instead of `abs(z)^2` for complex numbers
- **`div(x,y)`** instead of `trunc(x/y)` for integer truncating division
- **Avoid string interpolation in I/O**: use `println(file, a, " ", b)` not `println(file, "$a $b")`
- **Use `lazy"..."`** for strings only needed on error paths (avoids eager allocation)
- **Fix all deprecation warnings** — deprecated functions do an extra lookup per call
- **Subnormal numbers**: `set_zero_subnormals(true)` can speed up computations that produce many subnormals (e.g. exponential decay), but breaks some floating-point identities

## Diagnostic Workflow

1. **Profile first**: `@time` to find unexpected allocations, `Profile.@profile` + `ProfileView` to find hotspots
2. **Check type stability**: `@code_warntype` on the hot function
3. **Fix the type issue**: concrete fields, function barriers, consistent return types
4. **Re-measure**: verify allocations dropped and time improved
5. **Then annotate**: `@inbounds`, `@simd`, `@fastmath` only on verified hot loops
6. **Advanced tools**: JET.jl for static analysis, `--track-allocation=user` for allocation source tracking
