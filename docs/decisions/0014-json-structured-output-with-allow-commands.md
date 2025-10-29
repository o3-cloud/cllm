# JSON Structured Output with --allow-commands

## Context and Problem Statement

CLLM supports dynamic command execution via `--allow-commands` (ADR-0011, ADR-0013) and JSON structured output via `--json-schema` (ADR-0005). However, these features currently cannot be used together effectively. When workflows involve dynamic command execution, the final output is returned as unstructured text, making it difficult to parse, validate, or integrate into automated pipelines. Users need the ability to receive structured, parseable JSON output from command-enhanced LLM interactions.

## Decision Drivers

- Need for parseable output in automated workflows and scripts
- Ability to save structured results for later processing or analysis
- Integration with downstream tools that expect JSON input
- Consistency with existing JSON schema support (ADR-0005)
- Support for complex workflows that combine dynamic context (via commands) with structured output
- Programmatic access to LLM responses in predictable formats

## Considered Options

1. **Enable JSON schema with --allow-commands** - Allow both flags to work together, with the LLM returning structured output after command execution
2. **Separate command output from LLM output** - Return commands results and LLM response in separate JSON structure
3. **Post-process text output** - Keep features separate and rely on external parsing tools
4. **Command-aware schema validation** - Create special schemas that include command execution metadata

## Decision Outcome

Chosen option: "Enable JSON schema with --allow-commands", because it provides the most straightforward user experience, maintains consistency with existing features, and enables the most common use case: getting structured output after dynamic context injection.

### Consequences

- Good, because users can parse final output reliably in automated workflows
- Good, because it maintains consistency with existing `--json-schema` flag behavior
- Good, because it enables end-to-end structured workflows (dynamic input → LLM → structured output)
- Good, because it simplifies integration with downstream tools and APIs
- Neutral, because command execution still happens before LLM inference (no change to execution model)
- Bad, because it adds complexity to the CLI flag combination validation
- Bad, because debugging may be harder when both features are active simultaneously

### Confirmation

The implementation will be validated by:
- Unit tests verifying both flags can be used together without errors
- Integration tests showing commands execute and JSON schema is applied to final output
- Example workflows demonstrating common use cases (e.g., context gathering + structured analysis)
- Validation that invalid JSON outputs are properly handled and reported
- Performance tests ensuring command execution doesn't interfere with schema validation

## Pros and Cons of the Options

### Enable JSON schema with --allow-commands

Implementation: Allow `--json-schema` and `--allow-commands` flags to be used simultaneously. Commands execute first to inject context, then the LLM response is validated against the provided schema.

- Good, because it's the most intuitive behavior users would expect
- Good, because it requires minimal new code (mostly flag validation changes)
- Good, because it follows the principle of least surprise
- Good, because users can leverage both features without workarounds
- Neutral, because the execution order is implicit (commands → LLM → schema validation)
- Bad, because error messages may be ambiguous when both features interact

### Separate command output from LLM output

Implementation: Return a JSON structure with two keys: `command_results` and `llm_response`, where the latter conforms to the schema.

- Good, because it provides transparency into command execution
- Good, because it allows inspection of intermediate results
- Neutral, because it changes the output format significantly
- Bad, because it breaks the existing JSON schema contract (response is wrapped)
- Bad, because it requires more complex output parsing by users
- Bad, because it's inconsistent with existing behavior

### Post-process text output

Implementation: Keep features separate. Users pipe output through `jq` or custom parsers.

- Good, because it's simple to implement (no code changes)
- Good, because it follows Unix philosophy (do one thing well)
- Bad, because it shifts complexity to users
- Bad, because it makes structured output less reliable
- Bad, because it defeats the purpose of native JSON schema support
- Bad, because error handling becomes the user's responsibility

### Command-aware schema validation

Implementation: Extend JSON schema support to include command execution metadata (e.g., which commands ran, their outputs, timing).

- Good, because it provides full transparency
- Good, because it enables advanced debugging workflows
- Neutral, because it adds significant new functionality
- Bad, because it requires complex schema extensions
- Bad, because it makes schemas more complex to write
- Bad, because it's over-engineered for the common use case

## More Information

This ADR builds on:
- **ADR-0005**: Structured Output (JSON Schema) - Base JSON schema support
- **ADR-0011**: Dynamic Context Injection via Command Execution
- **ADR-0012**: Jinja2 Templating for Context Commands
- **ADR-0013**: LLM-Driven Dynamic Command Execution

The implementation should ensure that:
1. Command execution happens first (maintaining ADR-0011 behavior)
2. Command outputs are injected into the prompt as context
3. The LLM generates a response conforming to the provided schema
4. Schema validation errors are reported clearly with context about command execution status

Example usage:
```bash
# Get structured analysis after gathering dynamic context
cllm --allow-commands --json-schema analysis-schema.json \
  "Analyze the current git status and recent commits" \
  < analysis-prompt.txt > results.json

# Use in automated pipelines
cllm --allow-commands --json-schema bug-report.json \
  "Summarize test failures and suggest fixes" | \
  jq '.suggestions[]' | \
  while read fix; do apply_fix "$fix"; done
```

---

## AI-Specific Extensions

### AI Guidance Level

Chosen level: **Flexible**

Implementation details may vary (e.g., how errors are formatted, exact validation timing), but core principles must be maintained:
- Both flags must work together without conflicts
- Command execution always precedes LLM inference
- Final output must conform to provided JSON schema
- Error messages must be clear and actionable

### AI Tool Preferences

- Preferred AI tools: Any LLM with JSON mode support (GPT-4, Claude 3+, etc.)
- Model parameters: May need to adjust `temperature` lower (e.g., 0.3-0.5) for more consistent structured output
- Special instructions: Ensure LiteLLM's `response_format` parameter is properly set when schema is provided

### Test Expectations

- Unit test: `test_allow_commands_with_json_schema()` verifies flags work together
- Integration test: Full workflow with real command execution and schema validation
- Integration test: Error handling when commands fail but schema is requested
- Integration test: Error handling when LLM output doesn't match schema
- Performance test: Overhead of combined features is acceptable (<10% vs individual features)
- Example test: Documentation examples execute successfully and produce valid JSON

### Dependencies

- Related ADRs:
  - ADR-0005 (Structured Output JSON Schema)
  - ADR-0011 (Dynamic Context Injection)
  - ADR-0013 (LLM-Driven Dynamic Command Execution)
- System components:
  - `src/cllm/cli.py` (flag parsing and validation)
  - `src/cllm/client.py` (LiteLLM integration with response_format)
  - `src/cllm/config.py` (configuration precedence for both features)
- External dependencies:
  - LiteLLM library (must support `response_format` parameter)
  - JSON Schema validation library (jsonschema or similar)

### Timeline

- Implementation deadline: Q1 2025
- First review: After initial implementation and tests pass
- Revision triggers:
  - User reports of confusing error messages
  - LiteLLM changes to JSON mode support
  - Requests for command output visibility in structured responses

### Risk Assessment

#### Technical Risks

- **Risk: Command execution failures may leave unclear error states**
  - Mitigation: Clearly differentiate between command errors and schema validation errors in output

- **Risk: Performance degradation with both features active**
  - Mitigation: Profile and optimize command execution pipeline; add timeout controls

- **Risk: LLM providers may not support JSON mode consistently**
  - Mitigation: Test with multiple providers; document provider-specific limitations

#### Business Risks

- **Risk: Complex feature interaction may confuse users**
  - Mitigation: Provide clear documentation with examples; add warning messages for edge cases

- **Risk: Breaking changes to output format may affect existing scripts**
  - Mitigation: Maintain backward compatibility; add feature flag if needed

### Human Review

- Review required: Before implementation
- Reviewers: Project maintainers, users relying on structured output workflows
- Approval criteria:
  - Implementation passes all tests
  - Documentation is clear with practical examples
  - Error messages are actionable
  - No breaking changes to existing functionality

### Feedback Log

*To be filled post-implementation*

- Implementation date:
- Actual outcomes:
- Challenges encountered:
- Lessons learned:
- Suggested improvements:
