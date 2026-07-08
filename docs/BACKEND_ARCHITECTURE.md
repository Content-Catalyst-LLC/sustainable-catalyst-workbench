# Backend Architecture

WordPress is the interface. FastAPI is the analytics and AI backend.

Flow:

```text
WordPress shortcode
→ WordPress REST proxy
→ FastAPI backend
→ model registry
→ calculator engine
→ Python/R/Julia/Haskell/C++ bridge as needed
→ structured result + SVG graph
→ WordPress display
```

Python is the primary execution layer. R, Julia, Haskell, and C++ are extension bridges.
