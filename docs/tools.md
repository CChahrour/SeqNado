# Third-Party Tools

SeqNado integrates multiple best-in-class bioinformatics tools to provide comprehensive genomics analysis pipelines. For a full list of tools with references, see the [Citation Guidelines](citation.md#tools).

## Checking Tool Versions

All tools are version-locked in SeqNado containers to ensure reproducibility. To check versions and get tool information, use the `seqnado tools` command:

```bash
# List all tools with versions
seqnado tools

# List tools in a specific category (e.g., Download, Alignment, Analysis)
seqnado tools --category

# View detailed information about a specific tool
seqnado tools macs2

# Show tool help/options from the container
seqnado tools macs2 --options
```

See the [CLI Reference](cli.md#cli-seqnado-tools) for complete documentation of the `tools` command.
