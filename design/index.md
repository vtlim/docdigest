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
    subgraph User["User actions"]
        U1[Step 1: Create config file]
        U2[Step 2: Run docdigest]
    end
    
    U1 --> CONFIG[docdigest_config.json]
    CONFIG --> U2
    U2 --> MAIN[main.py<br/>Orchestrator]
    CONFIG --> MAIN
    
    MAIN --> P1[parse_docs.py<br/>Markdown parsing]
    
    P1 --> SUMMARY_PATH{Summary workflow}
    P1 --> META_PATH{Meta workflow}
    
    subgraph SummaryFlow["Summary generation path"]
        P2[summarize.py<br/>Generate summaries]
        P3[import_results.py<br/>Import to docs]
        P4[commitify.py<br/>Git commit/push]
    end
    
    subgraph MetaFlow["Meta description path"]
        P5[meta_description.py<br/>Generate meta]
        P6[import_meta.py<br/>Local or PR comment]
    end
    
    SUMMARY_PATH --> P2
    P2 --> P3
    P3 --> P4
    
    META_PATH --> P5
    P5 --> P6
    
    subgraph Utilities["Shared utilities"]
        UT1[file_utils.py]
        UT2[config.py]
        UT3[git_utils.py]
    end
    
    subgraph Inputs["Inputs"]
        IN1[Markdown files]
    end
    
    subgraph SummaryOutputs["Summary outputs"]
        OUT1[summaries.js]
        OUT2[Expanders in Markdown]
        OUT3[Git branch<br/>bot-summaries]
    end
    
    subgraph MetaOutputs["Meta outputs"]
        OUT4[Local mode<br/>Frontmatter in Markdown]
        OUT5[Automation mode<br/>PR comment]
    end
    
    IN1 --> P1
    P2 --> OUT1
    P3 --> OUT2
    P4 --> OUT3
    P6 --> OUT4
    P6 --> OUT5
    
    style U1 fill:#FFE5B4,stroke:#FFA500,color:#333
    style U2 fill:#FFE5B4,stroke:#FFA500,color:#333
    style CONFIG fill:#FFF9E6,stroke:#FFD700,color:#333
    style MAIN fill:#4A90E2,stroke:#2E5C8A,color:#fff
    style P1 fill:#50C878,stroke:#2E7D4E,color:#fff
    style P2 fill:#9B59B6,stroke:#6C3A7C,color:#fff
    style P3 fill:#E67E22,stroke:#A0522D,color:#fff
    style P4 fill:#E74C3C,stroke:#A93226,color:#fff
    style P5 fill:#3498DB,stroke:#2874A6,color:#fff
    style P6 fill:#16A085,stroke:#117A65,color:#fff
    style SUMMARY_PATH fill:#F5E6FF,stroke:#9B59B6,color:#333
    style META_PATH fill:#E6F7FF,stroke:#3498DB,color:#333
    style UT1 fill:#D3D3D3,stroke:#A9A9A9,color:#333
    style UT2 fill:#D3D3D3,stroke:#A9A9A9,color:#333
    style UT3 fill:#D3D3D3,stroke:#A9A9A9,color:#333
    style User fill:#FFF8DC,stroke:#FFD700
    style SummaryFlow fill:#F9F0FF,stroke:#9B59B6
    style MetaFlow fill:#E6F9FF,stroke:#3498DB
    style Utilities fill:#F5F5F5,stroke:#CCCCCC
    style Inputs fill:#E8F4F8,stroke:#B3D9E6
    style SummaryOutputs fill:#FFE6F0,stroke:#E67E22
    style MetaOutputs fill:#E6FFF5,stroke:#16A085
```
