# Multi-Agent Ticket Classification Architecture

## System Architecture

```mermaid
graph TB
    subgraph "User Interface"
        UI[Streamlit Dashboard<br/>4 Tabs]
        UI --> TAB1[Quick Classify]
        UI --> TAB2[6-Phase Classification]
        UI --> TAB3[Batch Processing]
        UI --> TAB4[🤖 AI Agent Assistant]
    end
    
    subgraph "AI Agent Assistant Flow"
        TAB4 --> INPUT[User Input<br/>Ticket Description]
        INPUT --> AGENT1[🎯 Classification Agent]
        INPUT --> AGENT2[📊 Metadata Agent]
        INPUT --> AGENT3[📚 Knowledge Base Agent]
        INPUT --> AGENT4[🔍 Historical Agent]
    end
    
    subgraph "Unity Catalog Functions"
        AGENT1 --> UC1[ai_classify<br/>Category/Priority/Team]
        AGENT2 --> UC2[ai_extract<br/>Priority Score/Urgency/Systems]
    end
    
    subgraph "Vector Search"
        AGENT3 --> VS[Vector Search Index<br/>knowledge_base_index]
        VS --> EMBED[BGE Embeddings]
        VS --> KB[(Knowledge Base<br/>12 Documents)]
    end
    
    subgraph "Genie"
        AGENT4 --> GENIE[Genie Conversation API]
        GENIE --> HIST[(ticket_history<br/>30 Sample Tickets)]
    end
    
    subgraph "Foundation Model"
        UC1 --> LLM[Llama 3.3 70B<br/>Instruct]
        UC2 --> LLM
        GENIE --> LLM
    end
    
    subgraph "Results Aggregation"
        UC1 --> AGG[Results Aggregator]
        UC2 --> AGG
        VS --> AGG
        GENIE --> AGG
        
        AGG --> REC[Smart Recommendations<br/>Generator]
        REC --> EXPORT[JSON Export]
        REC --> DISPLAY[UI Display]
    end
    
    style TAB4 fill:#e1f5ff
    style AGENT1 fill:#fff4e6
    style AGENT2 fill:#fff4e6
    style AGENT3 fill:#fff4e6
    style AGENT4 fill:#fff4e6
    style LLM fill:#f3e5f5
    style AGG fill:#e8f5e9
```

## Agent Coordination Flow

```mermaid
sequenceDiagram
    participant User
    participant Dashboard
    participant Agent1 as 🎯 Classification Agent
    participant Agent2 as 📊 Metadata Agent
    participant Agent3 as 📚 KB Agent
    participant Agent4 as 🔍 History Agent
    participant UC as Unity Catalog
    participant VS as Vector Search
    participant Genie as Genie API
    
    User->>Dashboard: Enter ticket & click Analyze
    Dashboard->>Dashboard: Show status: "Agent Processing..."
    
    par Parallel Execution
        Dashboard->>Agent1: Classify ticket
        Agent1->>UC: CALL ai_classify(ticket_text)
        UC-->>Agent1: {category, priority, team}
        Agent1-->>Dashboard: ✅ Classification (1-2s)
        
        Dashboard->>Agent2: Extract metadata
        Agent2->>UC: CALL ai_extract(ticket_text)
        UC-->>Agent2: {priority_score, urgency, systems}
        Agent2-->>Dashboard: ✅ Metadata (1-2s)
        
        Dashboard->>Agent3: Search knowledge base
        Agent3->>VS: POST /query {query_text}
        VS-->>Agent3: {documents[]}
        Agent3-->>Dashboard: ✅ KB Results (500ms)
    end
    
    Note over Dashboard: Build intelligent Genie query<br/>based on classification
    
    Dashboard->>Agent4: Query historical tickets
    Agent4->>Genie: POST /start-conversation
    Genie-->>Agent4: {conversation_id, message_id}
    
    loop Poll every 5s (max 120s)
        Agent4->>Genie: GET /messages/{message_id}
        Genie-->>Agent4: {status: IN_PROGRESS}
    end
    
    Genie-->>Agent4: {status: COMPLETED, attachments}
    Agent4-->>Dashboard: ✅ Historical data (15-30s)
    
    Dashboard->>Dashboard: Aggregate all results
    Dashboard->>Dashboard: Generate recommendations
    Dashboard->>User: Display comprehensive analysis
    User->>Dashboard: Export JSON (optional)
```

## Data Flow Architecture

```mermaid
graph LR
    subgraph "Input Sources"
        T1[Sample Tickets<br/>8 predefined]
        T2[Custom Ticket<br/>User input]
    end
    
    subgraph "Processing Layer"
        T1 --> PROC[Agent Orchestrator]
        T2 --> PROC
        
        PROC --> P1[Classification<br/>ai_classify]
        PROC --> P2[Extraction<br/>ai_extract]
        PROC --> P3[Vector Search<br/>knowledge_base]
        PROC --> P4[Genie Query<br/>ticket_history]
    end
    
    subgraph "Knowledge Sources"
        KB1[IT Infrastructure Runbook]
        KB2[Security Incident Playbook]
        KB3[Application Support Guide]
        KB4[User Access Policies]
        KB5[Ticket Classification Rules]
        KB6[Database Admin Guide]
        KB7[Network Troubleshooting]
        KB8[Monitoring & Alerting]
        KB9[Slack Collaboration]
        KB10[Storage & Backup]
        
        KB1 --> P3
        KB2 --> P3
        KB3 --> P3
        KB4 --> P3
        KB5 --> P3
        KB6 --> P3
        KB7 --> P3
        KB8 --> P3
        KB9 --> P3
        KB10 --> P3
    end
    
    subgraph "Output Layer"
        P1 --> OUT[Comprehensive<br/>Analysis]
        P2 --> OUT
        P3 --> OUT
        P4 --> OUT
        
        OUT --> UI1[UI Display<br/>Streamlit]
        OUT --> UI2[JSON Export<br/>Download]
        OUT --> UI3[Recommendations<br/>Context-aware]
    end
    
    style PROC fill:#fff4e6
    style OUT fill:#e8f5e9
```

## Technology Stack

```mermaid
graph TB
    subgraph "Frontend"
        ST[Streamlit<br/>Python Web Framework]
    end
    
    subgraph "Authentication & SDK"
        SDK[Databricks SDK<br/>WorkspaceClient]
        AUTH[OAuth / Service Principal]
    end
    
    subgraph "AI Services"
        UC[Unity Catalog<br/>AI Functions]
        VS[Vector Search<br/>Delta Sync]
        GE[Genie<br/>Conversation API]
        LLM[Foundation Models<br/>Llama 3.3 70B]
    end
    
    subgraph "Data Storage"
        DELTA[Delta Lake<br/>Tables]
        VOL[Unity Catalog<br/>Volumes]
    end
    
    subgraph "Deployment"
        DAB[Databricks Asset Bundles]
        APP[Databricks Apps]
    end
    
    ST --> SDK
    SDK --> AUTH
    SDK --> UC
    SDK --> VS
    SDK --> GE
    
    UC --> LLM
    GE --> LLM
    VS --> DELTA
    UC --> DELTA
    
    DAB --> APP
    ST --> APP
    
    style ST fill:#61dafb
    style SDK fill:#ff6b35
    style UC fill:#00d084
    style VS fill:#00d084
    style GE fill:#00d084
    style LLM fill:#f3e5f5
    style APP fill:#ff3621
```

## Agent Decision Tree

```mermaid
graph TD
    START[User Submits Ticket] --> CLASS{Classification Result}
    
    CLASS -->|P1 Critical| P1REC[🚨 URGENT Actions]
    CLASS -->|P2 High| P2REC[⚡ Prompt Actions]
    CLASS -->|P3 Normal| P3REC[📝 Queue Actions]
    
    P1REC --> ACT1[Escalate to on-call team]
    P1REC --> ACT2[Initiate incident response]
    P1REC --> ACT3[Send immediate notifications]
    
    P2REC --> ACT4[Assign to next available]
    P2REC --> ACT5[Monitor for similar issues]
    P2REC --> ACT6[Check knowledge base]
    
    P3REC --> ACT7[Add to team queue]
    P3REC --> ACT8[Schedule within SLA]
    P3REC --> ACT9[Standard workflow]
    
    CLASS --> KB{KB Results Found?}
    KB -->|Yes| KBACT[📚 Review N documentation articles]
    KB -->|No| KBSKIP[Continue without KB refs]
    
    CLASS --> HIST{Historical Tickets?}
    HIST -->|Enabled| GENQ[Query Genie]
    HIST -->|Disabled| SKIP[Skip historical analysis]
    
    GENQ --> GENR{Genie Success?}
    GENR -->|Yes| HISTACT[🔍 Check resolution patterns]
    GENR -->|Timeout/Error| SKIP
    
    ACT1 --> ROUTE[👥 Route to Team]
    ACT4 --> ROUTE
    ACT7 --> ROUTE
    KBACT --> ROUTE
    HISTACT --> ROUTE
    KBSKIP --> ROUTE
    SKIP --> ROUTE
    
    ROUTE --> FINAL[Display Comprehensive Analysis]
    
    style START fill:#e1f5ff
    style CLASS fill:#fff4e6
    style P1REC fill:#ffebee
    style P2REC fill:#fff3e0
    style P3REC fill:#e8f5e9
    style FINAL fill:#f3e5f5
```

## Cost & Performance Breakdown

```mermaid
pie title Cost Distribution per Ticket
    "ai_classify UC Function" : 40
    "ai_extract UC Function" : 45
    "Vector Search Query" : 5
    "Genie Conversation" : 10
```

```mermaid
gantt
    title Execution Timeline (With Genie)
    dateFormat X
    axisFormat %Ls
    
    section Classification
    ai_classify :a1, 0, 2000
    
    section Metadata
    ai_extract :a2, 0, 2000
    
    section Vector Search
    KB Query :a3, 0, 500
    
    section Genie
    Start Conversation :a4, 2000, 500
    Poll for Results :a5, 2500, 15000
    
    section Aggregation
    Generate Recommendations :a6, 17500, 500
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Development"
        CODE[Source Code<br/>Git Repository]
        CODE --> DAB[databricks.yml<br/>Asset Bundle Config]
    end
    
    subgraph "CI/CD"
        DAB --> BUNDLE[databricks bundle deploy]
        BUNDLE --> VALIDATE[Validate Resources]
    end
    
    subgraph "Databricks Workspace"
        VALIDATE --> UC_DEPLOY[Deploy UC Functions]
        VALIDATE --> VS_DEPLOY[Deploy Vector Index]
        VALIDATE --> APP_DEPLOY[Deploy Streamlit App]
        
        UC_DEPLOY --> CAT[Catalog:<br/>classify_tickets_new_dev]
        VS_DEPLOY --> CAT
        APP_DEPLOY --> APPS[Databricks Apps]
        
        CAT --> SCHEMA[Schema:<br/>support_ai]
        
        SCHEMA --> FUNCS[UC Functions:<br/>ai_classify, ai_extract,<br/>ai_gen, quick_classify]
        SCHEMA --> TABLES[Tables:<br/>knowledge_base,<br/>ticket_history]
        SCHEMA --> INDEX[Vector Index:<br/>knowledge_base_index]
    end
    
    subgraph "Runtime"
        APPS --> WEB[Web Interface<br/>Public URL]
        WEB --> USERS[End Users]
        
        APPS --> AUTH[Service Principal<br/>Authentication]
        AUTH --> PERMS[Permissions:<br/>SELECT on UC objects<br/>EXECUTE on functions]
    end
    
    style CODE fill:#e1f5ff
    style DAB fill:#fff4e6
    style APPS fill:#ff3621
    style WEB fill:#4caf50
```

## Key Metrics Dashboard

| Metric | Without Genie | With Genie |
|--------|--------------|------------|
| **Total Execution Time** | 2-4 seconds | 20-35 seconds |
| **Classification Time** | 1-2 seconds | 1-2 seconds |
| **Metadata Extraction** | 1-2 seconds | 1-2 seconds |
| **Vector Search** | 500ms | 500ms |
| **Genie Query** | N/A | 15-30 seconds |
| **Total Cost** | $0.001 | $0.002 |
| **Agents Invoked** | 3 | 4 |

## Success Criteria

✅ **Performance**
- Classification completes in < 3s (without Genie)
- Vector Search returns results in < 1s
- Genie queries complete in < 60s (typical)

✅ **Accuracy**
- Classification matches expected categories 95%+
- Priority scoring aligns with severity
- Knowledge base returns relevant docs 90%+

✅ **Reliability**
- System handles warehouse cold start (30-60s)
- Graceful fallback if Genie times out
- Error handling for all API calls

✅ **User Experience**
- Real-time status updates
- Clear error messages
- Export functionality works
- Mobile-responsive UI

✅ **Cost Efficiency**
- < $0.002 per ticket analyzed
- Reuses warehouse connections
- Caches Databricks client

## Monitoring & Observability

```mermaid
graph LR
    subgraph "Application Logs"
        APP[Streamlit App] --> LOGS[Application Logs]
        LOGS --> ERR[Error Tracking]
        LOGS --> PERF[Performance Metrics]
    end
    
    subgraph "UC Function Logs"
        FUNCS[UC Functions] --> UCLOGS[Function Execution Logs]
        UCLOGS --> UCPERF[Query Performance]
    end
    
    subgraph "Vector Search Metrics"
        VS[Vector Search] --> VSMETRICS[Query Latency]
        VSMETRICS --> VSQUAL[Result Quality]
    end
    
    subgraph "Genie Analytics"
        GENIE[Genie API] --> GMETRICS[Conversation Metrics]
        GMETRICS --> GPERF[Query Success Rate]
    end
    
    ERR --> DASH[Monitoring Dashboard]
    PERF --> DASH
    UCPERF --> DASH
    VSQUAL --> DASH
    GPERF --> DASH
    
    DASH --> ALERTS[Alerts & Notifications]
    
    style DASH fill:#fff4e6
    style ALERTS fill:#ffebee
```

---

## Summary

This architecture provides:

🎯 **Modular Design** - Each agent is independent and can be updated separately

⚡ **Parallel Execution** - Classification, extraction, and search run simultaneously

🔄 **Fault Tolerance** - Graceful degradation if any agent fails

📊 **Observable** - Detailed logging and metrics at each stage

💰 **Cost-Effective** - ~$0.002 per ticket with predictable pricing

🚀 **Scalable** - Can process thousands of tickets per hour

🔒 **Secure** - Uses Databricks authentication and Unity Catalog governance

---

**Next Steps:**
1. Review deployed dashboard
2. Test with various ticket types
3. Monitor performance metrics
4. Gather user feedback
5. Plan Phase 2 enhancements

