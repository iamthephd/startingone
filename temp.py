# LLM-Based Data Commentary and Chatbot System Design Document

## 1) System Architecture
### High-level architecture diagram
*Already provided in the project materials*

### Components and their interactions
1. **Streamlit UI**
   - User interface for table selection, viewing commentary, and interacting with the chatbot
   - Displays summary tables, reason codes, attributes, and commentary
   - Provides dropdowns for manual modification of parameters
   - Integrates chat interface for natural language interaction

2. **Oracle Database**
   - Primary data source storing raw and processed data
   - Maintains connections for both data retrieval and storage

3. **Data Processing Layer**
   - Custom pre-processing functions specific to each table
   - Python code for summary table generation
   - Data transformation and aggregation utilities

4. **LLM Services**
   - Commentary generation LLM: Analyzes data patterns and generates natural language insights
   - Reason code identification LLM: Determines appropriate reason codes and attributes
   - SQL query generation LLM: Converts natural language to SQL for chatbot functionality
   - Response generation LLM: Creates natural language responses based on retrieved data

5. **SQL Template Engine**
   - Manages and updates SQL query templates based on reason codes, attributes, and other parameters
   - Handles dynamic query generation for data retrieval

## 2) Data Flow and Processing Pipeline
### Data Management
- **Data access patterns**: Read-heavy with periodic writes for processed data
- **Data lifecycle**: Raw data → Pre-processed data → Summary data → LLM input → Generated commentary
- **Data governance**: Centralized metadata repository for tracking lineage and transformations

### Data Sources and Acquisition Methods
- **Primary source**: Oracle Database tables
- **Selection mechanism**: User-driven table selection via Streamlit UI
- **Access method**: Direct database connection using Oracle client libraries
- **Polling frequency**: On-demand when user selects a table

### Data Storage Architecture
- **Raw data**: Original Oracle DB tables (unchanged)
- **Processed data**: Separate schema in Oracle DB for transformed data
- **Summary tables**: Dedicated tables for aggregated views used by LLMs
- **Commentary storage**: Persistent storage for generated commentaries with version history
- **Chat history**: Short-term storage for conversation context

### Data Preprocessing and Transformation Techniques
- **Table-specific preprocessing**: Custom functions per table addressing unique data characteristics
- **Common transformations**:
  - Normalization and standardization
  - Outlier detection and handling
  - Missing value imputation
  - Feature engineering for trend detection
- **Summary table creation**: Aggregation, pivoting, and time-series transformations
- **Input formatting for LLMs**: JSON structures with context, data points, and metadata

## 3) Model Development
### Selection of AI/ML Algorithms
- **Commentary generation**: Large language model (e.g., Claude) fine-tuned on financial/data commentary
- **Reason code identification**: Classification model integrated with LLM
- **SQL generation**: LLM with specialized SQL generation capabilities
- **Response generation**: Same LLM as commentary with different prompt engineering

### Model Training Process
- **Base models**: Pre-trained LLMs as foundation
- **Fine-tuning**: Domain adaptation using synthetic and historical commentary data
- **Prompt engineering**: Carefully designed prompts for each specific task
- **Few-shot learning**: Including examples in prompts for better performance
- **RAG implementation**: Retrieval-augmented generation for data-grounded responses

### Performance Evaluation Metrics
- **Commentary quality**: Human evaluation using clarity, accuracy, and relevance scales
- **Reason code accuracy**: F1 score, precision, recall against expert-labeled data
- **SQL accuracy**: Query correctness, execution success rate, and result relevance
- **Response quality**: Answer accuracy, relevance to query, and factual consistency
- **User satisfaction**: Explicit feedback and implicit metrics (acceptance rate of generated content)

### Model Versioning and Lifecycle Management
- **Version control**: Git repository for all model artifacts and prompts
- **Model registry**: Central repository for tracking model versions and performance
- **A/B testing**: Framework for evaluating model improvements before deployment
- **Rollback capability**: System to revert to previous model versions if issues arise
- **Documentation**: Comprehensive documentation of model characteristics and behavior

## 4) Infrastructure and Deployment
### Computing Resources
- **Development environment**: Containers with GPU access for model development
- **Production environment**: Cloud-based deployment with auto-scaling
- **Storage requirements**: 
  - Database: Sized according to Oracle DB table volumes
  - Model storage: ~10GB for model weights and artifacts
  - Application storage: ~2GB for application code and dependencies

### Deployment Strategies
- **Containerization**: Docker containers for application components
- **Orchestration**: Kubernetes for container management
- **CI/CD pipeline**: Automated testing and deployment
- **Blue-green deployment**: For zero-downtime updates
- **Feature flags**: For controlled rollout of new capabilities

### Scalability Considerations
- **Horizontal scaling**: Additional application instances for increased user load (up to 100 concurrent users)
- **Vertical scaling**: Resource allocation for memory-intensive operations
- **Load balancing**: Distribution of requests across multiple instances
- **Database scaling**: Read replicas for improved query performance
- **Caching strategy**: Redis cache for frequently accessed data and commentaries
- **Rate limiting**: Protection against excessive API calls

## 5) Security and Compliance
### Data Privacy and Protection Measures
- **Data encryption**: At rest and in transit
- **PII handling**: Identification and masking of personally identifiable information
- **Data minimization**: Only necessary data sent to LLM services
- **Retention policies**: Clear timelines for data storage and deletion
- **Audit trails**: Comprehensive logging of data access and modifications

### Access Control and Authentication
- **User authentication**: Integration with company SSO system
- **Role-based access control**: Different permission levels for users
- **API authentication**: Token-based authentication for all API calls
- **Session management**: Secure session handling with appropriate timeouts
- **Least privilege principle**: Minimal permissions for each system component

## 6) Monitoring and Maintenance
### Model Performance Tracking
- **Performance dashboards**: Real-time visualization of key metrics
- **Drift detection**: Monitoring for data and concept drift
- **Usage statistics**: Tracking of feature utilization and user engagement
- **Error rate monitoring**: Identification of systematic failures or issues
- **Response time tracking**: Ensuring acceptable latency for all operations

### Retraining and Model Updates
- **Scheduled retraining**: Regular intervals for model refreshing
- **Trigger-based retraining**: Performance degradation triggers retraining
- **Continuous learning**: Integration of user feedback into training data
- **Update procedures**: Documented processes for model updates
- **Testing framework**: Comprehensive testing before deployment of new models

### Logging and Error Handling
- **Centralized logging**: ELK stack (Elasticsearch, Logstash, Kibana) for log management
- **Error classification**: Categorization of errors for prioritized resolution
- **Alerting system**: Notifications for critical errors and anomalies
- **Graceful degradation**: Fallback mechanisms when components fail
- **User feedback collection**: Mechanisms for reporting issues directly from the UI

## 7) Integration and API Design
### Interaction with Existing Systems
- **Oracle DB integration**: Direct connection with appropriate credentials
- **Authentication system**: Integration with corporate identity provider
- **Notification systems**: Email or messaging integration for alerts
- **Reporting tools**: Export capabilities for integration with BI platforms
- **Version control**: Integration with Git repositories

### API Specifications and Endpoints
- **Commentary generation API**:
  - Endpoint: `/api/commentary/generate`
  - Method: POST
  - Inputs: Table name, parameters
  - Outputs: Generated commentary, metadata
  
- **Reason code API**:
  - Endpoint: `/api/analysis/reason-codes`
  - Method: POST
  - Inputs: Table name, data metrics
  - Outputs: Ranked reason codes, confidence scores
  
- **Chatbot API**:
  - Endpoint: `/api/chat/query`
  - Method: POST
  - Inputs: User query, conversation history
  - Outputs: Response, SQL used (if applicable)
  
- **Data retrieval API**:
  - Endpoint: `/api/data/retrieve`
  - Method: POST
  - Inputs: SQL query or table name
  - Outputs: Retrieved data, metadata

### Data Input/Output Formats
- **API request/response**: JSON format with standardized schema
- **Database queries**: SQL with parameterized queries
- **Chatbot interface**: Natural language text
- **Commentary output**: Markdown-formatted text
- **Error responses**: Standardized error objects with codes and descriptions

### Consumption Interfaces and Inference APIs
- **Streamlit UI**: Primary user interface
- **REST APIs**: For programmatic access by other systems
- **Batch processing**: For scheduled commentary generation
- **Export capabilities**: CSV, Excel, PDF for generated commentaries
- **Embedded views**: Capability to embed components in other applications

## 8) Risk Assessment and Mitigation
### Potential Risks and Their Impact
1. **Data quality issues**:
   - Impact: Incorrect or misleading commentary
   - Likelihood: Medium
   
2. **LLM hallucinations**:
   - Impact: False information in commentary or chat responses
   - Likelihood: Medium-high
   
3. **System performance degradation**:
   - Impact: Poor user experience, timeout errors
   - Likelihood: Low-medium
   
4. **Security breaches**:
   - Impact: Data exposure, system compromise
   - Likelihood: Low
   
5. **Model drift**:
   - Impact: Declining quality of generated content
   - Likelihood: Medium over time

### Risk Mitigation Strategies
1. **Data quality issues**:
   - Implement data validation checks
   - Create data quality dashboards
   - Establish data governance procedures
   
2. **LLM hallucinations**:
   - Ground all responses in retrieved data
   - Implement factual consistency checks
   - Create human review process for critical outputs
   
3. **System performance degradation**:
   - Implement performance monitoring
   - Create scaling rules based on load metrics
   - Optimize database queries and caching
   
4. **Security breaches**:
   - Regular security audits
   - Penetration testing
   - Security training for team members
   
5. **Model drift**:
   - Regular performance evaluation
   - Feedback loops from users
   - Scheduled model retraining

### Contingency Planning
1. **Service disruption**:
   - Fallback to simpler, rule-based commentary
   - Cache recent outputs for quick retrieval
   - Implement circuit breakers for failing components
   
2. **Database unavailability**:
   - Read-only mode with cached data
   - Clear user messaging about limitations
   - Automatic retry mechanisms
   
3. **LLM service failure**:
   - Local backup models (smaller, less capable)
   - Template-based fallback responses
   - Queue requests for processing when service restores
   
4. **Critical bugs in production**:
   - Automated rollback procedures
   - Feature toggle system for quick disabling
   - Incident response team and procedures

5. **User misuse or overloading**:
   - Rate limiting at user and IP level
   - Graduated service degradation under load
   - Automated abuse detection



####################################### 
## 1) System Architecture
### Components and their interactions

1. **Streamlit UI**
   - **Interactions**:
     - Sends table selection to Data Processing Layer
     - Receives and displays summary tables from Data Processing Layer
     - Displays reason codes and attributes from LLM Services
     - Presents generated commentary to users
     - Forwards user modifications (dropdown selections) to SQL Template Engine
     - Sends user chat messages to LLM Services for chatbot functionality
     - Receives and displays chatbot responses

2. **Oracle Database**
   - **Interactions**:
     - Provides raw data to Data Processing Layer
     - Stores processed data received from Data Processing Layer
     - Responds to SQL queries from SQL Template Engine
     - Stores generated summary tables from Data Processing Layer

3. **Data Processing Layer**
   - **Interactions**:
     - Receives table selection from Streamlit UI
     - Retrieves raw data from Oracle Database
     - Applies table-specific pre-processing functions
     - Sends processed data back to Oracle Database
     - Creates summary tables and stores them in Oracle Database
     - Forwards summary data to LLM Services for analysis

4. **LLM Services**
   - **Interactions**:
     - Receives summary data from Data Processing Layer
     - Identifies reason codes and attributes and sends to Streamlit UI
     - Receives user chat queries from Streamlit UI
     - Sends SQL query generation requests to SQL Template Engine
     - Receives query results from SQL Template Engine
     - Generates commentary based on data and sends to Streamlit UI
     - Generates chatbot responses and sends to Streamlit UI

5. **SQL Template Engine**
   - **Interactions**:
     - Receives reason codes, attributes, and parameters from LLM Services
     - Receives user modifications from Streamlit UI
     - Generates SQL queries based on inputs
     - Sends SQL queries to Oracle Database
     - Receives query results from Oracle Database
     - Forwards retrieved data to LLM Services for commentary generation or chatbot responses

## 2) Data Flow and Processing Pipeline

### End-to-End Data Flow

1. **User Interaction Initiation**:
   - User selects a table from dropdown in Streamlit UI
   - UI sends table selection to Data Processing Layer

2. **Data Preprocessing Flow**:
   - Data Processing Layer connects to Oracle DB
   - Retrieves selected table data
   - Applies table-specific custom preprocessing function
   - Stores processed data back in Oracle DB

3. **Summary Table Creation Flow**:
   - Data Processing Layer retrieves processed data
   - Applies table-specific Python code to create summary table
   - Stores summary table in Oracle DB
   - Sends summary table data to LLM Services

4. **Reason Code & Attribute Identification Flow**:
   - LLM Services analyze summary table data
   - Identify appropriate reason codes (e.g., Tax, Concession)
   - Determine relevant attributes (e.g., Y/Y change, Q/Q change)
   - Identify top contributing factors and columns
   - Send identified parameters to SQL Template Engine and Streamlit UI

5. **SQL Query Generation Flow**:
   - SQL Template Engine receives reason codes, attributes, top n, and contributing columns
   - Generates appropriate SQL queries based on these parameters
   - Sends SQL queries to Oracle DB
   - Receives query results with specific data for commentary

6. **Commentary Generation Flow**:
   - LLM Services receive query results from SQL Template Engine
   - Generate natural language commentary based on data
   - Send generated commentary to Streamlit UI for display

7. **User Modification Flow - Manual Selection**:
   - User deselects/selects reason codes, attributes, top n, or contributing columns via dropdowns
   - Streamlit UI sends updated parameters to SQL Template Engine
   - SQL Template Engine generates new SQL queries
   - New data is retrieved and sent to LLM Services
   - LLM Services generate updated commentary
   - Updated commentary is displayed in Streamlit UI

8. **User Modification Flow - Chat Interaction**:
   - User enters natural language query/modification in chat interface
   - Streamlit UI sends message to LLM Services
   - For data-related queries:
     - LLM Services generate SQL query via SQL Template Engine
     - SQL Template Engine retrieves data from Oracle DB
     - LLM Services generate response based on retrieved data
   - For commentary modification requests:
     - LLM Services modify existing commentary based on user input
   - Response/modified commentary is sent back to Streamlit UI

9. **Data Feedback Loop**:
   - User interactions and modifications are logged
   - System tracks which reason codes and attributes are manually selected
   - This feedback can be used to improve LLM performance over time

### Data Management Strategy

- **Real-time processing**: All data processing occurs on-demand when user selects a table
- **Caching strategy**: 
  - Recently accessed tables' summary data is cached
  - Generated commentaries are cached with their parameters
  - Chat history is maintained during session
- **Data retention**:
  - Raw data: Persistent in Oracle DB
  - Processed data: Stored until updated
  - Generated commentaries: Stored with version history
  - User modifications: Logged for improvement of system