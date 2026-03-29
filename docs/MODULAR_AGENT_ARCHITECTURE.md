# Modular Agent Architecture Design

## Vision
Transform the rigid 10-agent pipeline into a **flexible, user-configurable agent orchestration platform** where users can:

- Add/remove/modify agents
- Define custom system prompts
- Select models per agent
- Visually connect agents into workflows
- Save and share workflow templates
- Deploy custom use cases beyond event marketing

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MODULAR AGENT PLATFORM                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐   │
│  │  AGENT DEFINITION │────▶│  WORKFLOW BUILDER │────▶│  EXECUTION ENGINE │   │
│  │     SCHEMA        │     │   (Visual DAG)    │     │   (Runtime)       │   │
│  └──────────────────┘     └──────────────────┘     └──────────────────┘   │
│         │                         │                        │               │
│         ▼                         ▼                        ▼               │
│  ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐   │
│  │   Agent Store    │     │  Connection      │     │  Agent Registry  │   │
│  │   (Database)     │     │  Validation      │     │  (Dynamic Load)  │   │
│  └──────────────────┘     └──────────────────┘     └──────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Agent Definition Schema

Each agent is defined by a configuration object:

```typescript
interface AgentDefinition {
  // Identity
  id: string;                    // Unique identifier
  name: string;                  // Display name
  description: string;           // What this agent does
  icon: string;                  // Icon identifier
  
  // AI Configuration
  model: string;                 // LLM model ID
  systemPrompt: string;          // System prompt template
  temperature: number;           // 0.0 - 1.0
  maxTokens: number;             // Max output tokens
  
  // Capabilities
  capabilities: {
    webSearch: boolean;          // Needs web access?
    webFetch: boolean;           // Can fetch URLs?
    fileUpload: boolean;         // Accepts files?
    codeExecution: boolean;      // Can run code?
  };
  
  // Input/Output Contract
  inputSchema: JSONSchema;       // Expected input structure
  outputSchema: JSONSchema;      // Guaranteed output structure
  
  // Execution
  timeout: number;               // Max execution time (seconds)
  retryPolicy: {
    maxRetries: number;
    backoffStrategy: 'exponential' | 'linear';
  };
  
  // Metadata
  version: string;               // Agent version
  author: string;                // Creator
  tags: string[];                // Categories
  isCustom: boolean;             // User-created vs system
}
```

### Example Agent Definitions

```typescript
// Default Event Discovery Agent
const eventDiscoveryAgent: AgentDefinition = {
  id: 'event_discovery',
  name: 'Event Discovery',
  description: 'Finds industry events matching criteria',
  icon: 'search',
  model: 'gemini-3-flash-preview',
  systemPrompt: `You are an expert event researcher...`,
  temperature: 0.3,
  maxTokens: 4000,
  capabilities: { webSearch: true, webFetch: false },
  inputSchema: {
    type: 'object',
    properties: {
      query: { type: 'string' },
      industry: { type: 'string' },
      region: { type: 'string' }
    }
  },
  outputSchema: {
    type: 'object',
    properties: {
      events: {
        type: 'array',
        items: {
          type: 'object',
          properties: {
            name: { type: 'string' },
            date: { type: 'string' },
            location: { type: 'string' }
          }
        }
      }
    }
  },
  timeout: 120,
  retryPolicy: { maxRetries: 3, backoffStrategy: 'exponential' },
  version: '1.0.0',
  author: 'System',
  tags: ['research', 'events'],
  isCustom: false
};

// User-Created Custom Agent
const competitorAnalysisAgent: AgentDefinition = {
  id: 'competitor_analysis_abc123',
  name: 'Competitor Analysis',
  description: 'Analyzes competitor presence at events',
  icon: 'target',
  model: 'claude-opus-4-6',
  systemPrompt: `You are a competitive intelligence analyst...`,
  capabilities: { webSearch: true, webFetch: true },
  inputSchema: { /* ... */ },
  outputSchema: { /* ... */ },
  isCustom: true,
  author: 'user@company.com'
};
```

---

## 2. Workflow Definition (DAG)

Workflows are Directed Acyclic Graphs (DAGs) of connected agents:

```typescript
interface WorkflowDefinition {
  id: string;
  name: string;
  description: string;
  
  // DAG Structure
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  
  // Execution Settings
  executionMode: 'sequential' | 'parallel' | 'conditional';
  checkpointEnabled: boolean;
  autoRetry: boolean;
  
  // Metadata
  version: string;
  createdBy: string;
  createdAt: Date;
  updatedAt: Date;
  isTemplate: boolean;
  tags: string[];
}

interface WorkflowNode {
  id: string;                    // Unique within workflow
  agentId: string;               // References AgentDefinition
  position: { x: number; y: number };  // For visual builder
  config: {
    // Agent-specific overrides
    model?: string;
    temperature?: number;
    customPrompt?: string;
  };
}

interface WorkflowEdge {
  id: string;
  source: string;                // Source node ID
  target: string;                // Target node ID
  condition?: string;            // Optional condition (for branching)
  dataMapping?: {                // Map output fields to input
    sourceField: string;
    targetField: string;
  }[];
}
```

### Example Workflows

```typescript
// Default Event Marketing Workflow
const eventMarketingWorkflow: WorkflowDefinition = {
  id: 'event_marketing_default',
  name: 'Event Marketing Pipeline',
  nodes: [
    { id: 'node_1', agentId: 'schema_initialization', position: { x: 100, y: 100 } },
    { id: 'node_2', agentId: 'intent_understanding', position: { x: 100, y: 200 } },
    { id: 'node_3', agentId: 'event_discovery', position: { x: 100, y: 300 } },
    { id: 'node_4', agentId: 'vendor_discovery', position: { x: 300, y: 300 } },
    // ... more nodes
  ],
  edges: [
    { id: 'edge_1', source: 'node_1', target: 'node_2' },
    { id: 'edge_2', source: 'node_2', target: 'node_3' },
    { id: 'edge_3', source: 'node_2', target: 'node_4' },  // Branching
    // ... more edges
  ],
  executionMode: 'sequential'
};

// Custom Competitor Tracking Workflow
const competitorWorkflow: WorkflowDefinition = {
  id: 'competitor_tracking',
  name: 'Competitor Event Tracker',
  nodes: [
    { id: 'node_1', agentId: 'event_discovery' },
    { id: 'node_2', agentId: 'competitor_analysis_abc123' },  // Custom agent
    { id: 'node_3', agentId: 'outreach_email' }
  ],
  edges: [
    { id: 'edge_1', source: 'node_1', target: 'node_2' },
    { id: 'edge_2', source: 'node_2', target: 'node_3' }
  ]
};
```

---

## 3. Visual Workflow Builder

### Features

1. **Canvas**: Infinite scroll workspace
2. **Agent Palette**: Sidebar with available agents
   - System agents (pre-built)
   - Custom agents (user-created)
   - Templates (drag-and-drop)

3. **Node Operations**:
   - Drag to position
   - Click to configure
   - Right-click menu (duplicate, delete)
   - Resize handles

4. **Connection System**:
   - Click-and-drag to connect
   - Auto-route lines around obstacles
   - Color-coded by data type
   - Validation on connection

5. **Configuration Panel**:
   - Model selection dropdown
   - System prompt editor (with templates)
   - Temperature slider
   - Capability toggles
   - Input/output preview

### UI Mockup

```
┌────────────────────────────────────────────────────────────────┐
│  PALETTE    │         CANVAS (Workflow Builder)                 │
│             │                                                   │
│ 🔍 Search   │     ┌─────────┐        ┌─────────┐               │
│             │     │ Schema  │───────▶│ Intent  │               │
│ SYSTEM      │     │  Init   │        │Understand│               │
│ 📋 Schema   │     └─────────┘        └────┬────┘               │
│ 🧠 Intent   │                              │                    │
│ 🔍 Discover │     ┌─────────┐        ┌────▼────┐               │
│ 🌍 Vendor   │     │ Vendor  │◀───────│ Events  │               │
│             │     │Discover │        │Discover │               │
│ CUSTOM      │     └────┬────┘        └────┬────┘               │
│ 🎯 MyAgent  │          │                    │                   │
│ 📊 Analytics│          └────────────────────┘                   │
│             │                        │                          │
│ TEMPLATES   │                   ┌────▼────┐                    │
│ 📦 Events   │                   │Qualify  │                    │
│ 📦 Sales    │                   └─────────┘                    │
│             │                                                   │
└─────────────┴───────────────────────────────────────────────────┘
```

---

## 4. Execution Engine

### Dynamic Agent Loading

```python
class ModularAgentExecutor:
    def __init__(self, agent_registry: AgentRegistry):
        self.registry = agent_registry
        self.active_executions: Dict[str, ExecutionContext] = {}
    
    async def execute_workflow(
        self,
        workflow: WorkflowDefinition,
        initial_input: Dict,
        context: ExecutionContext
    ) -> ExecutionResult:
        """Execute a workflow dynamically"""
        
        # Build execution graph
        graph = self._build_execution_graph(workflow)
        
        # Topological sort for execution order
        execution_order = graph.topological_sort()
        
        results = {}
        
        for node_id in execution_order:
            node = workflow.get_node(node_id)
            agent_def = self.registry.get_agent(node.agent_id)
            
            # Prepare input from previous nodes
            node_input = self._prepare_node_input(
                node, 
                results, 
                workflow.edges
            )
            
            # Execute agent
            agent_instance = self._load_agent(agent_def)
            result = await agent_instance.execute(
                input_data=node_input,
                config=node.config
            )
            
            results[node_id] = result
            
            # Checkpoint if enabled
            if workflow.checkpoint_enabled:
                await self._save_checkpoint(context, node_id, result)
        
        return ExecutionResult(
            final_output=results[execution_order[-1]],
            all_results=results,
            context=context
        )
    
    def _load_agent(self, agent_def: AgentDefinition) -> BaseAgent:
        """Dynamically load agent class based on definition"""
        
        if agent_def.is_custom:
            # Create runtime agent from definition
            return DynamicAgent(agent_def)
        else:
            # Load system agent
            return self.registry.get_system_agent(agent_def.id)
```

### Connection Validation

```typescript
class ConnectionValidator {
  validateConnection(
    sourceAgent: AgentDefinition,
    targetAgent: AgentDefinition,
    edge: WorkflowEdge
  ): ValidationResult {
    const errors: string[] = [];
    
    // Check output -> input compatibility
    const outputSchema = sourceAgent.outputSchema;
    const inputSchema = targetAgent.inputSchema;
    
    if (edge.dataMapping) {
      // Validate explicit mappings
      for (const mapping of edge.dataMapping) {
        if (!this.fieldExists(outputSchema, mapping.sourceField)) {
          errors.push(`Source field '${mapping.sourceField}' not found`);
        }
        if (!this.fieldExists(inputSchema, mapping.targetField)) {
          errors.push(`Target field '${mapping.targetField}' not found`);
        }
      }
    } else {
      // Check automatic compatibility
      const compatibility = this.checkSchemaCompatibility(
        outputSchema, 
        inputSchema
      );
      if (!compatibility.isCompatible) {
        errors.push(...compatibility.issues);
      }
    }
    
    // Check for cycles
    if (this.wouldCreateCycle(sourceAgent.id, targetAgent.id)) {
      errors.push('Connection would create a cycle');
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  }
}
```

---

## 5. Storage & Persistence

### Database Schema

```sql
-- Agent definitions
CREATE TABLE agents (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    icon VARCHAR(100),
    model VARCHAR(100) NOT NULL,
    system_prompt TEXT NOT NULL,
    temperature FLOAT DEFAULT 0.3,
    max_tokens INTEGER DEFAULT 2000,
    capabilities JSONB,
    input_schema JSONB,
    output_schema JSONB,
    timeout INTEGER DEFAULT 60,
    retry_policy JSONB,
    version VARCHAR(20) DEFAULT '1.0.0',
    author VARCHAR(255),
    tags TEXT[],
    is_custom BOOLEAN DEFAULT false,
    is_system BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Workflow definitions
CREATE TABLE workflows (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    nodes JSONB NOT NULL,
    edges JSONB NOT NULL,
    execution_mode VARCHAR(50) DEFAULT 'sequential',
    checkpoint_enabled BOOLEAN DEFAULT true,
    auto_retry BOOLEAN DEFAULT true,
    version VARCHAR(20) DEFAULT '1.0.0',
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_template BOOLEAN DEFAULT false,
    tags TEXT[]
);

-- Workflow executions
CREATE TABLE workflow_executions (
    id UUID PRIMARY KEY,
    workflow_id UUID REFERENCES workflows(id),
    status VARCHAR(50) DEFAULT 'pending',
    input_data JSONB,
    output_data JSONB,
    node_results JSONB,
    logs JSONB,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);
```

---

## 6. API Design

### RESTful Endpoints

```typescript
// Agent Management
GET    /api/agents                    // List all agents
POST   /api/agents                    // Create new agent
GET    /api/agents/:id                // Get agent details
PUT    /api/agents/:id                // Update agent
DELETE /api/agents/:id                // Delete agent

// Workflow Management
GET    /api/workflows                 // List workflows
POST   /api/workflows                 // Create workflow
GET    /api/workflows/:id             // Get workflow
PUT    /api/workflows/:id             // Update workflow
DELETE /api/workflows/:id             // Delete workflow
POST   /api/workflows/:id/execute     // Execute workflow
GET    /api/workflows/:id/executions  // List executions

// Templates
GET    /api/templates                 // List templates
POST   /api/templates/:id/clone       // Clone template to workflow

// Execution
GET    /api/executions/:id            // Get execution status
GET    /api/executions/:id/logs       // Stream logs
POST   /api/executions/:id/cancel     // Cancel execution
POST   /api/executions/:id/retry      // Retry failed nodes
```

---

## 7. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Create AgentDefinition schema
- [ ] Refactor existing 10 agents to use schema
- [ ] Build Agent Registry
- [ ] Create database migrations

### Phase 2: Workflow Engine (Week 3-4)
- [ ] Implement DAG execution
- [ ] Build connection validation
- [ ] Add checkpoint system
- [ ] Create execution API

### Phase 3: Visual Builder (Week 5-6)
- [ ] Canvas component with pan/zoom
- [ ] Draggable agent nodes
- [ ] Connection drawing system
- [ ] Node configuration panel

### Phase 4: Agent Creator (Week 7-8)
- [ ] Agent definition form
- [ ] Prompt editor with templates
- [ ] Model selection
- [ ] Input/output schema builder

### Phase 5: Templates & Sharing (Week 9-10)
- [ ] Workflow templates
- [ ] Import/export workflows
- [ ] Community gallery
- [ ] Version control

---

## 8. Use Cases Enabled

### Original: Event Marketing
```
Intent → Discovery → Qualification → Outreach → Excel
```

### New: Sales Prospecting
```
Intent → LinkedIn Search → Enrichment → Scoring → Outreach
```

### New: Content Research
```
Topic → Web Search → Summarization → Outline → Draft
```

### New: Competitive Analysis
```
Competitor → News Monitoring → Sentiment Analysis → Report
```

---

## Summary

**YES, this is absolutely possible and would transform your platform from a rigid tool into a flexible, enterprise-grade agent orchestration system.**

Key benefits:
1. **User Empowerment**: Non-technical users can build custom workflows
2. **Scalability**: New use cases without code changes
3. **Monetization**: Template marketplace, premium agents
4. **Competitive Moat**: Configurability others don't have
5. **Community**: Users share workflows and agents

The architecture supports everything from simple linear pipelines to complex branching workflows with conditional logic.