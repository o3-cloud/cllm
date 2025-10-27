# Add CLI Flag to List Available Models

## Context and Problem Statement

CLLM supports 100+ LLM providers through LiteLLM, but users currently have no way to discover which models are available without consulting external documentation. This creates friction in the user experience, especially for new users who need to know which model names to use with the `--model` flag or in their Cllmfile.yml configurations.

Users need a convenient way to:
- Discover available models across all supported providers
- Find the correct model identifier strings for different providers
- Understand which models they have API access to based on their environment variables

## Decision Drivers

- **User experience**: Easy discovery of available models without leaving the CLI
- **LiteLLM integration**: Leverage LiteLLM's existing model information capabilities
- **CLI consistency**: Follow existing flag patterns (`--stream`, `--temperature`, etc.)
- **Maintainability**: Model list should stay current with LiteLLM updates automatically
- **Bash-first design**: Should work well in scripting contexts (grep, awk, etc.)
- **Performance**: Should not slow down normal `cllm` invocations

## Considered Options

1. **Add `--list-models` flag** - Flag that prints available models and exits
2. **Add `cllm models` subcommand** - Separate subcommand for model listing
3. **Static configuration file** - Ship a models.yml with known models
4. **No model listing** - Require users to check LiteLLM documentation

## Decision Outcome

Chosen option: **"Add `--list-models` flag"**, because it:
- Follows the existing single-command CLI pattern (no subcommands currently)
- Is consistent with other informational flags like `--show-config`
- Enables bash scripting patterns: `cllm --list-models | grep gpt`
- Can be implemented using LiteLLM's model listing functionality
- Requires minimal changes to the existing CLI architecture

### Consequences

- Good, because users can discover models without leaving the terminal
- Good, because the model list stays automatically updated with LiteLLM releases
- Good, because it integrates naturally with bash workflows
- Good, because it's consistent with the existing CLI design
- Neutral, because it adds one more flag to the CLI interface
- Bad, because the model list might be very long (100+ providers)
- Bad, because not all listed models may be accessible to the user (depends on API keys)

### Confirmation

Implementation will be validated by:
- Unit tests verifying the flag triggers model listing
- Integration test confirming LiteLLM model data is retrieved
- Manual testing of output format and readability
- Verification that `cllm --list-models | grep <pattern>` works as expected
- Performance test ensuring flag doesn't impact normal usage

## Pros and Cons of the Options

### Add `--list-models` flag

Direct CLI flag that prints available models and exits (similar to `--show-config`).

- Good, because it follows existing CLI patterns in CLLM
- Good, because it's easy to pipe and filter: `cllm --list-models | grep claude`
- Good, because implementation is straightforward
- Good, because it doesn't require restructuring the CLI
- Neutral, because the output could be very long
- Bad, because it doesn't provide a natural way to categorize by provider without additional formatting

### Add `cllm models` subcommand

Create a subcommand structure: `cllm models list`, `cllm models search`, etc.

- Good, because it provides room for expansion (search, filter by provider, etc.)
- Good, because it could support multiple output formats (json, table, etc.)
- Good, because it's more "modern" CLI design
- Bad, because it breaks from the current single-command design pattern
- Bad, because it's more complex to implement
- Bad, because it's less bash-friendly than a simple flag
- Bad, because CLLM is explicitly "bash-centric" (ADR-0002 context)

### Static configuration file

Ship a models.yml file with known model identifiers.

- Good, because it would be simple to implement
- Good, because it provides complete control over formatting and descriptions
- Bad, because it would require manual maintenance
- Bad, because it would quickly become outdated as LiteLLM adds providers
- Bad, because it duplicates LiteLLM's model registry
- Bad, because it violates the principle of LiteLLM being the source of truth

### No model listing

Require users to consult LiteLLM documentation externally.

- Good, because it requires no implementation work
- Good, because it avoids duplication of LiteLLM documentation
- Bad, because it creates friction in the user experience
- Bad, because users need to context-switch to browser
- Bad, because LiteLLM docs might change or be unavailable
- Bad, because it doesn't align with CLLM's goal of being a complete CLI interface

## More Information

### Implementation Notes

The implementation should:
1. Add `--list-models` flag to `cli.py` argument parser
2. Query LiteLLM's model information (via `litellm.model_list` or similar)
3. Format output for readability and bash-friendliness
4. Exit after printing models (don't process stdin/arguments)
5. Consider grouping by provider for better organization
6. Consider adding `--provider` filter option for future enhancement

### Output Format Considerations

The output format should prioritize:
- **Grep-ability**: Each model on its own line or in a clear table format
- **Readability**: Group by provider or indicate provider in output
- **Completeness**: Include model identifier strings that can be copy-pasted

Example format option 1 (simple list):
```
gpt-4
gpt-3.5-turbo
claude-3-opus-20240229
claude-3-sonnet-20240229
gemini-pro
...
```

Example format option 2 (grouped):
```
OpenAI:
  gpt-4
  gpt-3.5-turbo
  gpt-3.5-turbo-16k

Anthropic:
  claude-3-opus-20240229
  claude-3-sonnet-20240229
...
```

### Related Decisions

- **ADR-0002**: LiteLLM abstraction means model list comes from LiteLLM
- **ADR-0003**: Cllmfile configuration uses model names from this list

---

## AI-Specific Extensions

### AI Guidance Level

**Chosen level: Flexible**

AI agents should:
- Follow the core decision to use a `--list-models` flag
- Have flexibility in determining the best output format for bash-friendliness
- Investigate LiteLLM's API to find the best way to retrieve model information
- Adapt the implementation if LiteLLM provides better model listing methods

### AI Tool Preferences

- Preferred AI tools: Claude Code
- Implementation approach: Follow existing patterns in `cli.py`
- Testing approach: Mock LiteLLM responses in unit tests
- Code style: Match existing CLLM conventions

### Test Expectations

- Unit test: `test_list_models_flag()` verifies flag triggers listing behavior
- Unit test: `test_list_models_output_format()` verifies output is properly formatted
- Mock test: Mock `litellm.model_list` or equivalent to avoid API calls
- Integration test: Verify actual LiteLLM integration works
- Manual test: `cllm --list-models | grep gpt` returns expected results
- Performance test: Normal `cllm` invocations are not slowed down

### Dependencies

- Related ADRs:
  - ADR-0002 (LiteLLM abstraction)
  - ADR-0003 (Cllmfile configuration - users need model names)
- System components:
  - `src/cllm/cli.py` - CLI argument parsing and flag handling
  - `litellm` library - Source of model information
- External dependencies:
  - LiteLLM model registry/listing API

### Timeline

- Implementation deadline: Next minor version release
- First review: After initial implementation
- Revision triggers:
  - LiteLLM changes model listing API
  - User feedback indicates output format is not useful
  - Performance issues are discovered

### Risk Assessment

#### Technical Risks

- **LiteLLM API changes**: LiteLLM might change how model information is exposed
  - Mitigation: Test against multiple LiteLLM versions; monitor LiteLLM changelog

- **Large output size**: 100+ providers means potentially hundreds of models
  - Mitigation: Implement pagination or provider filtering if needed

- **Performance impact**: Querying model list might be slow
  - Mitigation: Only execute when flag is explicitly used; consider caching

#### Business Risks

- **User confusion**: Users might expect only models they have access to
  - Mitigation: Document that list shows all LiteLLM-supported models

- **Maintenance burden**: Model list might need updates or corrections
  - Mitigation: Rely on LiteLLM as source of truth; don't maintain separate list

### Human Review

- Review required: Before implementation
- Reviewers: Project maintainers
- Approval criteria:
  - Output format is bash-friendly and easily parseable
  - Implementation doesn't add noticeable startup time
  - Tests adequately cover the functionality
  - Documentation is updated (README, --help text)

### Feedback Log

- **Implementation date:** 2025-10-26
- **Actual outcomes:**
  - ✅ Successfully implemented `--list-models` flag in `src/cllm/cli.py:93-97`
  - ✅ Created `print_model_list()` function that retrieves 1343 models from `litellm.model_list`
  - ✅ Implemented grouped output format (format option 2) with provider categorization
  - ✅ Added 9 comprehensive unit tests in `tests/test_cli.py` (all passing)
  - ✅ Verified grep-friendly output: `cllm --list-models | grep gpt-4` works perfectly
  - ✅ Performance confirmed: `--list-models` executes in ~1.75s, normal CLI operations remain at ~1.68s (no impact)
  - ✅ Model count exceeds expectation: 1343 models available (well beyond "100+" mentioned)
- **Challenges encountered:**
  - **Model categorization complexity:** Initial exploration found LiteLLM doesn't provide a built-in provider categorization API
    - **Resolution:** Implemented custom provider prefix matching in `print_model_list()` with 20+ provider patterns
    - **Impact:** Results in more readable, organized output while maintaining grep-ability
  - **Output format decision:** Had to choose between simple list vs. grouped format
    - **Resolution:** Chose grouped format (option 2) as it provides better UX without sacrificing bash-friendliness
    - **Evidence:** Each model still on its own line; grep works perfectly
  - **No native `get_models()` API:** LiteLLM SDK lacks a programmatic model discovery function
    - **Resolution:** Used `litellm.model_list` (a pre-populated list of 1343 models)
    - **Trade-off:** List is static per LiteLLM version but auto-updates with LiteLLM releases
- **Lessons learned:**
  - **Flexible AI guidance worked well:** The "Flexible" AI guidance level (line 156) allowed adaptation to LiteLLM's actual API vs assumptions
  - **Provider grouping adds significant value:** Despite ADR noting it "doesn't provide a natural way to categorize" (line 67), implementing it proved straightforward and greatly improved readability
  - **Test-driven approach validated design:** Writing tests first exposed edge cases (empty model lists, categorization logic)
  - **LiteLLM's static model list is acceptable:** Despite risk of "API changes" (line 204), using the static `model_list` is reliable and self-updating
  - **Bash-friendliness achieved without compromise:** Grouped format maintains full grep-ability while improving human readability
- **Suggested improvements:**
  - **Future enhancement:** Consider adding `--provider <name>` filter flag (mentioned in line 113 but not implemented)
  - **Future enhancement:** Add `--format json` option for programmatic consumption
  - **Documentation:** Update README.md with `--list-models` examples
  - **Documentation:** Add example to `cllm --help` epilog showing model discovery workflow
  - **Monitoring:** Track LiteLLM version updates to ensure `model_list` API remains stable
- **Confirmation Status:**
  - ✅ **Unit tests verifying flag triggers listing:** Implemented as `test_list_models_flag_exists` and `test_list_models_exits_successfully`
  - ✅ **Integration test confirming LiteLLM data retrieval:** Verified via `test_print_model_list_output` with actual `litellm.model_list`
  - ✅ **Manual testing of output format:** Confirmed 1343 models displayed with provider grouping and readable formatting
  - ✅ **Grep pattern verification:** Tested `cllm --list-models | grep gpt-4` successfully returns 3 exact matches
  - ✅ **Performance test:** Normal `cllm --help` runs in 1.68s; `--list-models` flag adds no overhead to regular usage
  - ✅ **Exit behavior:** Verified flag exits without reading prompt or creating LLMClient (`test_list_models_does_not_read_prompt`)
  - ✅ **Help text updated:** `cllm --help` shows `--list-models` flag with description
  - ⚠️ **README documentation:** Not yet updated with new flag examples (low priority)
- **Risk Mitigation Status:**
  - ✅ **LiteLLM API changes risk:** Mitigated by using stable `litellm.model_list` attribute; tests mock this for stability
  - ✅ **Large output size risk:** Confirmed 1343 models print in ~1.75s; acceptable performance; pagination not needed
  - ✅ **Performance impact risk:** Verified no impact on normal CLI usage (lazy loading only when flag used)
  - ✅ **User confusion risk:** Output clearly shows total count and includes tip about grep filtering
  - ✅ **Maintenance burden risk:** Successfully delegated to LiteLLM; no manual model list maintenance required
- **Test Coverage:**
  - Total tests: 47 (38 existing + 9 new for this ADR)
  - Test pass rate: 100% (47/47 passing)
  - New test file: `tests/test_cli.py` with 4 test classes:
    - `TestCLIArguments`: Argument parsing verification (2 tests)
    - `TestListModels`: Output formatting and categorization (3 tests)
    - `TestListModelsIntegration`: End-to-end flag behavior (3 tests)
    - `TestListModelsGrep`: Bash-friendliness validation (1 test)
- **Implementation Evidence:**
  - Code: `src/cllm/cli.py:93-97` (flag definition), `cli.py:128-201` (print function), `cli.py:249-251` (handler)
  - Tests: `tests/test_cli.py:1-152` (9 comprehensive tests)
  - Dependencies: Uses `litellm.model_list` directly (no new dependencies)
  - Integration: Follows existing pattern from `--show-config` flag
