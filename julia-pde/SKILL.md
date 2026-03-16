---
name: julia-pde
description: Julia PDE/ODE solving — DifferentialEquations.jl, spatial discretization, sparse linear algebra, automatic differentiation (Enzyme.jl, ForwardDiff.jl), Symbolics.jl code generation, HPC threading (Polyester.jl, ThreadPinning.jl), GPU solvers (CUDA.jl), HDF5/JLD2 checkpointing. Use whenever working with PDE/ODE solvers, finite difference/element methods, method of lines, sensitivity analysis, or Julia HPC simulation workflows.
---

For general Julia development (Pkg, testing, formatting), see `julia-dev`. For performance optimization (type stability, allocations, profiling), see `julia-performance`.

## DifferentialEquations.jl

The primary solver ecosystem. Choose the right problem type and algorithm:

- `ODEProblem` / `solve(prob, Tsit5())` for non-stiff ODEs
- `solve(prob, Rodas5P())` or `TRBDF2()` for stiff systems (typical for PDE semi-discretizations)
- `SDEProblem` for stochastic DEs
- `DDEProblem` for delay DEs
- `SteadyStateProblem` for finding equilibria
- Use `EnsembleProblem` for parameter sweeps / Monte Carlo

### Performance-critical patterns
- In-place form `f!(du, u, p, t)` is essential for large systems — out-of-place allocates a new array every RHS call
- Pass analytical Jacobians or set `jac=true` to let AD compute them — dramatically improves stiff solver performance
- Use `SciMLSensitivity.jl` for adjoint/forward sensitivity analysis of DE solutions
- `MethodOfLines.jl` automates spatial discretization from symbolic PDEs

## Spatial Discretization

### Finite Differences
- Build sparse operators with `SparseArrays.jl`: `spdiagm` for banded matrices (e.g. Laplacian stencils)
- Use `@views` on array slices to avoid copies in stencil computations
- For structured grids, store operators as sparse matrices and apply with `mul!` (in-place)

### Symbolics.jl for Code Generation
- Define PDE symbolically, then use `build_function` to generate optimized Julia kernels
- `Symbolics.sparsejacobian` computes symbolic sparsity patterns — feed these to sparse AD or sparse direct solvers

## Linear Algebra for PDEs

- `LinearAlgebra.jl`: `mul!` for in-place matrix-vector products, `ldiv!` for in-place solves
- `SparseArrays.jl`: `sparse()`, `spdiagm()`, `SparseMatrixCSC` — the backbone of PDE discretizations
- `LinearSolve.jl`: Unified interface for direct and iterative solvers. Automatically selects between UMFPACK, KLU, GMRES, etc.
- Alternative BLAS backends: MKL.jl, AppleAccelerate.jl
- Set `BLAS.set_num_threads(1)` when using Julia threads alongside BLAS to prevent oversubscription

## Automatic Differentiation

| Tool | Mode | Best for |
|------|------|----------|
| **ForwardDiff.jl** | Forward | Few inputs, many outputs; Jacobians of small systems |
| **Enzyme.jl** | Forward+Reverse | Performance-critical AD; works on mutating `!` code; lowest overhead |
| **Zygote.jl** | Reverse | Many inputs, few outputs (loss functions, parameter estimation) |

- Enzyme.jl handles in-place mutation that Zygote cannot — important for PDE RHS functions
- `SparseDiffTools.jl`: Exploits Jacobian sparsity patterns for efficient coloring-based AD — essential for large PDE systems where the Jacobian is sparse

## HPC Parallelism

### Multi-threading for PDE kernels
- **Polyester.jl `@batch`**: Preferred for PDE RHS evaluation. Low-overhead static scheduling with a reusable task pool — much faster than `Threads.@threads` for tight loops.
- **ThreadPinning.jl**: Pin threads to CPU cores / NUMA domains with `pinthreads()`. Use `threadinfo()` to inspect mapping. Critical for cache locality on multi-socket HPC nodes.
- **`Threads.@threads`**: Fall back for dynamic workloads.

### GPU Computing
- **CUDA.jl**: Use `CuArray` as drop-in replacement. Many SciML solvers accept GPU arrays via `EnsembleGPUArray`.
- **Metal.jl**: Apple Silicon GPU support.
- For custom PDE kernels, write CUDA kernels with `CUDA.@cuda` for full control.

### Distributed
- `MPI.jl` for domain decomposition across nodes
- `Distributed.jl` for multi-process parallelism

## Data I/O & Checkpointing

- **HDF5.jl**: Preferred for large numerical arrays — efficient binary format, widely portable. Use `h5open` / `read` / `write`.
- **JLD2.jl**: Save/load arbitrary Julia objects and simulation state snapshots. Essential for checkpointing long-running PDE simulations.
- **Lightweight CSV**: For convergence history logging, implement a `CSVWriter` struct wrapping an IO handle with `open_csv(path, header)` and `write_row!(writer, values)` methods. Avoid depending on CSV.jl.
- **NaNMath.jl**: NaN-propagation-safe math (`log`, `pow`) — returns NaN instead of DomainError. Important when solver evaluations can leave the valid domain.
