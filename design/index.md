## Design and structure of `docdigest`

The tooling to generate AI summaries for the docs has the following stages, each corresponding to a Python module in this package.

1. 📖 Parse documentation
2. 🤖 Generate summaries (writes summaries.js)
   1. 🧮 Parallel option to dry-run (optional, exits early)
3. 📝 Update markdown imports (modifies .md files)
4. 📦 Commit changes (individual commits per summary)

### Package structure

```
docdigest
├── __init__.py
├── commitify.py
├── config.py
├── file_utils.py
├── git_utils.py
├── import_results.py
├── main.py
├── parse_docs.py
└── summarize.py
```

NOTE: If you update or add a module, also update `pyproject.toml` for GHA installation.

### Diagram of components

```mermaid
graph TD
    A[User runs docdigest] --> B[main.py<br/>Orchestrator]
    
    B --> C[parse_docs.py<br/>Part 1: Markdown Parsing]
    B --> D[summarize.py<br/>Part 2: LLM Generation]
    B --> E[import_results.py<br/>Part 3: Summary Imports]
    B --> F[commitify.py<br/>Part 4: Git Commit]
    
    subgraph Utilities["Shared Utilities"]
        G[file_utils.py<br/>File Operations]
        H[config.py<br/>Configuration]
        I[git_utils.py<br/>Git Operations]
    end
    
    subgraph Inputs["Inputs"]
        R[Markdown Files]
    end
    
    subgraph Outputs["Outputs"]
        S[Summary File]
        T[Documentation Pages<br/>with Expanders]
        U[Git Repository<br/>bot-summaries branch]
    end
    
    C --> J[Extract content<br/>Identify changed files]
    D --> K[Generate AI summaries<br/>via Claude]
    E --> L[Import summaries<br/>into docs]
    F --> M[Create branch<br/>Commit & push<br/>Return to original]
    
    R --> J
    K --> S
    L --> T
    M --> U
    
    style B fill:#4A90E2,stroke:#2E5C8A,color:#fff
    style C fill:#50C878,stroke:#2E7D4E,color:#fff
    style D fill:#9B59B6,stroke:#6C3A7C,color:#fff
    style E fill:#E67E22,stroke:#A0522D,color:#fff
    style F fill:#E74C3C,stroke:#A93226,color:#fff
    style G fill:#D3D3D3,stroke:#A9A9A9,color:#333
    style H fill:#D3D3D3,stroke:#A9A9A9,color:#333
    style I fill:#D3D3D3,stroke:#A9A9A9,color:#333
    style Utilities fill:#F5F5F5,stroke:#CCCCCC
    style Inputs fill:#E8F4F8,stroke:#B3D9E6
    style Outputs fill:#FFF4E6,stroke:#FFD699
```
