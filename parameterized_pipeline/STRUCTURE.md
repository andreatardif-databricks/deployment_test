# Bundle Structure

This document shows the complete structure of the parameterized pipeline bundle.

## Directory Layout

```
parameterized_pipeline/
│
├── databricks.yml                          # Main bundle configuration
│                                          # - Defines variables (catalog, schema, config_file_path)
│                                          # - Defines targets (dev, staging, prod)
│                                          # - Each target uses different variable values
│
├── config/                                # Configuration files directory
│   ├── dev_config.yml                    # Development environment config
│   ├── ppe_config.yml                    # PPE/Staging environment config (customer sample)
│   └── prod_config.yml                   # Production environment config
│
├── resources/                             # DABs resource definitions
│   └── pipeline.yml                      # DLT pipeline definitions
│                                          # - data_pipeline: Basic pipeline using variables
│                                          # - data_pipeline_with_config: Pipeline using YAML config
│
├── src/                                   # Source code and notebooks
│   ├── config_loader.py                  # Python module to load YAML configurations
│   ├── pipeline.ipynb                    # Basic DLT pipeline (uses simple variables)
│   ├── pipeline_with_config.ipynb        # DLT pipeline using external YAML config
│   └── requirements.txt                  # Python dependencies (pyyaml)
│
├── fixtures/                              # Test fixtures directory
│   └── .gitkeep                          # Keeps directory in git
│
├── .gitignore                            # Git ignore patterns
├── README.md                             # Main documentation
├── CONFIG_USAGE.md                       # Detailed guide for using YAML config files
├── QUICK_START.md                        # Quick start guide
└── STRUCTURE.md                          # This file
```

## File Descriptions

### Configuration Files

| File | Purpose |
|------|---------|
| `databricks.yml` | Main bundle configuration defining variables and targets |
| `config/dev_config.yml` | Development environment configuration |
| `config/ppe_config.yml` | PPE/Staging environment configuration (customer sample) |
| `config/prod_config.yml` | Production environment configuration |

### Resource Definitions

| File | Purpose |
|------|---------|
| `resources/pipeline.yml` | Defines two DLT pipelines: basic and config-based |

### Source Code

| File | Purpose |
|------|---------|
| `src/config_loader.py` | Helper module to load and parse YAML config files |
| `src/pipeline.ipynb` | Basic DLT pipeline using simple variables |
| `src/pipeline_with_config.ipynb` | DLT pipeline demonstrating YAML config usage |
| `src/requirements.txt` | Python package dependencies |

### Documentation

| File | Purpose |
|------|---------|
| `README.md` | Main documentation and overview |
| `CONFIG_USAGE.md` | Complete guide for using external YAML config files |
| `QUICK_START.md` | Quick start guide to get running in 5 minutes |
| `STRUCTURE.md` | This file - explains bundle structure |

## Configuration Flow

```
databricks.yml
    ↓
    Defines: config_file_path = "../config/dev_config.yml"
    ↓
resources/pipeline.yml
    ↓
    Passes: config_file_path to pipeline configuration
    ↓
src/pipeline_with_config.ipynb
    ↓
    Loads: config = ConfigLoader(config_file_path)
    ↓
    Uses: kafka_host = config.get('general.kafka.main.host')
```

## Two Approaches Comparison

### Approach 1: Simple Variables (data_pipeline)

```
databricks.yml → resources/pipeline.yml → src/pipeline.ipynb
     ↓                    ↓                       ↓
  Variables         configuration           spark.conf.get()
```

**Best for:** 3-5 simple configuration values

### Approach 2: External YAML Config (data_pipeline_with_config)

```
databricks.yml → resources/pipeline.yml → src/pipeline_with_config.ipynb → config/*.yml
     ↓                    ↓                       ↓                              ↓
config_file_path    configuration         ConfigLoader()                 YAML config
```

**Best for:** Complex configurations with many nested values

## Key Features

### 1. No Duplication
- One pipeline definition works for all environments
- Configuration varies by target (dev/staging/prod)

### 2. Flexible Configuration
- Simple variables for basic configs
- External YAML files for complex configs

### 3. Environment Isolation
- Each target has its own:
  - Catalog and schema
  - Configuration file
  - Environment-specific settings

### 4. Easy Deployment
```bash
databricks bundle deploy -t dev     # Uses dev_config.yml
databricks bundle deploy -t staging # Uses ppe_config.yml
databricks bundle deploy -t prod    # Uses prod_config.yml
```

## Adding New Configurations

### Add a Simple Variable

1. Add to `databricks.yml` variables section
2. Add to target-specific variables
3. Add to pipeline configuration in `resources/pipeline.yml`
4. Access via `spark.conf.get()` in notebook

### Add a YAML Config Value

1. Add to config YAML file (e.g., `config/dev_config.yml`)
2. Access via `config.get('path.to.value')` in notebook

### Add a New Environment

1. Create config file: `config/new_env_config.yml`
2. Add target in `databricks.yml`:
   ```yaml
   targets:
     new_env:
       variables:
         config_file_path: "../config/new_env_config.yml"
   ```
3. Deploy: `databricks bundle deploy -t new_env`

## Best Practices

✅ **Use simple variables for**: catalog, schema, basic table names  
✅ **Use YAML configs for**: Kafka settings, OAuth, checkpoints, complex nested configs  
✅ **Keep secrets in Secret Scopes**: Don't put actual secrets in YAML files  
✅ **Version control configs**: Commit all config files to git  
✅ **Document your configs**: Add comments in YAML files  
✅ **Test before deploying**: Validate configs in dev first  

## Dependencies

- Python packages: `pyyaml>=6.0` (specified in `src/requirements.txt`)
- Databricks CLI for deployment
- Workspace with Unity Catalog (catalog/schema support)

## Size Metrics

- Total files: ~15
- Configuration files: 3 (dev, ppe, prod)
- Pipeline definitions: 2 (basic, config-based)
- Notebooks: 2
- Lines of documentation: ~700+
