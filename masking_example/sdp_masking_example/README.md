# Using this project using the CLI

The Databricks workspace and IDE extensions provide a graphical interface for working
with this project. It's also possible to interact with it directly using the CLI:

1. Authenticate to your Databricks workspace, if you have not done so already:
    ```
    $ databricks configure
    ```

2. To deploy a development copy of this project, type:
    ```
    $ databricks bundle deploy -t dev
    ```

3. To run a job or pipeline, use the "run" command:
   ```
   $ databricks bundle run sdp_masking_example_job -t dev
   ```
