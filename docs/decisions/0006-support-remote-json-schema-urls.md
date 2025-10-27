# Support Remote JSON Schema URLs

## Context and Problem Statement

CLLM currently supports structured output with JSON schemas (ADR-0005) via four methods: inline CLI flags, local file references, inline Cllmfile schemas, and local file references in Cllmfiles. All file-based schemas must exist on the local filesystem, which creates friction for teams sharing schemas or using published schema repositories.

Many organizations publish canonical JSON schemas in version-controlled repositories (e.g., GitHub) that define standard data formats. For example:

- API response schemas hosted on GitHub
- Industry-standard schemas from organizations
- Shared team schemas in centralized repositories
- Published artifact specifications like https://raw.githubusercontent.com/o3-cloud/artifact-specs/refs/heads/main/specs/artifacts/morning_brief.schema.json

Users currently must download these schemas manually to use them with CLLM, breaking the workflow and creating version sync issues. Supporting remote schema URLs would enable direct references to authoritative schemas, ensuring consistency and reducing duplication.

## Decision Drivers

- **Developer Experience**: Eliminate manual schema downloads, streamline workflows
- **Schema Versioning**: Enable explicit version pinning via URL (branch/tag/commit references)
- **Collaboration**: Teams can share schemas via URLs without distributing files
- **Canonical Sources**: Use authoritative schemas directly from their source
- **Consistency**: Ensure all team members use identical schema versions
- **Flexibility**: Support both local and remote schemas for different use cases
- **Performance**: Minimize network overhead, enable caching
- **Security**: Protect against malicious schemas and network attacks
- **Offline Support**: Graceful degradation when network unavailable

## Considered Options

1. **URL support in CLI flags only** - Allow `--json-schema-file https://...`
2. **URL support in Cllmfile only** - Reference remote schemas in configuration files
3. **Full URL support** - Support URLs in both CLI flags and Cllmfiles
4. **New dedicated flags** - Add `--json-schema-url` and separate Cllmfile key
5. **No remote schema support** - Continue requiring local files only

## Decision Outcome

Chosen option: **"Full URL support - Support URLs in both CLI flags and Cllmfiles"**, because it provides maximum flexibility while maintaining consistency with the existing hybrid approach from ADR-0005. Users can reference remote schemas the same way they reference local files, without learning new flags.

### Implementation Details

**1. CLI Flag with Remote URL:**

```bash
# Direct URL reference
cllm "Extract person info" --json-schema-file https://raw.githubusercontent.com/example/schemas/main/person.json

# Works with any HTTPS URL
echo "Parse this data" | cllm --json-schema-file https://schemas.example.com/v1/data.json
```

**2. Cllmfile with Remote URL:**

```yaml
# extraction.Cllmfile.yml
model: "gpt-4o"
temperature: 0
json_schema_file: "https://raw.githubusercontent.com/o3-cloud/artifact-specs/refs/heads/main/specs/artifacts/morning_brief.schema.json"
```

**3. Mixed Local and Remote (different configs):**

```yaml
# Use remote schema for production
json_schema_file: "https://schemas.example.com/v2/response.json"
# Local override during development
# Override with: cllm --config prod --json-schema-file ./local-schema.json
```

**URL Detection:**

- Automatically detect URLs by checking if path starts with `http://` or `https://`
- No new flags needed - reuse existing `--json-schema-file` and `json_schema_file`
- Precedence rules remain unchanged from ADR-0005

**Caching Strategy:**

Remote schemas will be cached to improve performance and enable offline usage:

1. **Cache Location**: `~/.cllm/cache/schemas/`
2. **Cache Key**: SHA-256 hash of the URL (collision-resistant, filesystem-safe)
3. **Cache Validity**: 24 hours (configurable via environment variable `CLLM_SCHEMA_CACHE_TTL`)
4. **Cache Behavior**:
   - First request: Download, validate, cache, and use
   - Subsequent requests (within TTL): Use cached version
   - Expired cache: Re-download and update cache
   - Network failure: Use stale cache if available, error otherwise
5. **Cache Invalidation**:
   - Manual: `cllm --clear-schema-cache` flag
   - Automatic: TTL expiration (default 24h)
   - Environment variable: `CLLM_SCHEMA_CACHE_TTL=3600` (seconds)

**Example Cache Workflow:**

```bash
# First use - downloads and caches
cllm "Extract data" --json-schema-file https://example.com/schema.json
# Output: Downloaded schema from https://example.com/schema.json (cached for 24h)

# Second use (within 24h) - uses cache
cllm "Extract more data" --json-schema-file https://example.com/schema.json
# Output: Using cached schema from https://example.com/schema.json

# Force refresh
cllm --clear-schema-cache
# Output: Cleared 15 cached schemas

# Use with stale cache (network error)
cllm "Extract data" --json-schema-file https://example.com/schema.json
# Output: Warning: Network error, using cached schema from https://example.com/schema.json (downloaded 2 days ago)
```

**Security Measures:**

1. **HTTPS Only**: Only allow `https://` URLs by default (reject `http://`)
   - Environment variable override: `CLLM_ALLOW_HTTP_SCHEMAS=1` (not recommended)
2. **Schema Validation**: Validate downloaded content is valid JSON Schema before use
3. **Size Limits**: Reject schemas larger than 1MB (configurable)
4. **Timeout**: 10-second timeout for schema downloads
5. **User Confirmation**: Optional confirmation for first-time URLs (environment variable `CLLM_CONFIRM_REMOTE_SCHEMAS=1`)
6. **Content-Type Checking**: Verify `Content-Type: application/json` or `application/schema+json`

**Error Handling:**

```bash
# Network error with no cache
cllm --json-schema-file https://unreachable.com/schema.json
# Error: Failed to download schema from https://unreachable.com/schema.json
# Network error: Connection timeout
# Cache miss: No cached version available
# Suggestion: Check network connection or use a local schema file

# Invalid schema
cllm --json-schema-file https://example.com/invalid.json
# Error: Invalid JSON Schema from https://example.com/invalid.json
# Schema validation error: Missing required 'type' field
# Suggestion: Verify URL points to a valid JSON Schema file

# HTTP (non-HTTPS) URL
cllm --json-schema-file http://example.com/schema.json
# Error: Insecure schema URL (HTTP not allowed)
# URL: http://example.com/schema.json
# Suggestion: Use HTTPS URL or set CLLM_ALLOW_HTTP_SCHEMAS=1 to override (not recommended)
```

### Consequences

- Good, because remote schemas can be referenced directly without manual downloads
- Good, because teams can share schemas via version-controlled URLs (e.g., GitHub raw URLs)
- Good, because schema updates propagate automatically (within cache TTL)
- Good, because explicit version pinning via URL paths (commit hashes, tags, branches)
- Good, because caching reduces network overhead and enables offline usage
- Good, because it's backward compatible (local files still work exactly as before)
- Good, because no new CLI flags needed (reuses existing `--json-schema-file`)
- Neutral, because adds network dependency for remote schemas (mitigated by caching)
- Neutral, because cache management adds complexity (mitigated by automatic TTL)
- Bad, because network failures can break workflows if cache miss (mitigated by error messages)
- Bad, because introduces security considerations (mitigated by HTTPS-only, validation, size limits)
- Bad, because cache invalidation could be confusing (mitigated by clear TTL and `--clear-schema-cache` flag)

### Confirmation

Implementation will be validated through:

1. **Unit tests** for URL detection, downloading, caching, and error handling
2. **Integration tests** with mocked HTTP responses (success, failure, timeout, invalid content)
3. **Cache tests** for TTL expiration, cache hits/misses, and invalidation
4. **Security tests** for HTTP rejection, size limits, and malformed schemas
5. **Error handling tests** for network failures, invalid URLs, and timeout scenarios
6. **Example scripts** demonstrating remote schema usage with real GitHub URLs
7. **Documentation** for cache behavior, security considerations, and troubleshooting

Success metrics:

- Remote schema URLs work in CLI flags and Cllmfiles
- Caching reduces redundant downloads (second request uses cache)
- Network failures gracefully fallback to cache or show clear errors
- HTTPS-only enforcement works (HTTP URLs rejected by default)
- Cache invalidation works correctly (TTL expiration and manual clearing)
- Documentation includes security best practices

## Pros and Cons of the Options

### URL support in CLI flags only

**Example:**

```bash
cllm "prompt" --json-schema-file https://example.com/schema.json
```

- Good, because it's simple to implement (minimal code changes)
- Good, because CLI usage is explicit and obvious
- Neutral, because Cllmfiles would still require local files
- Bad, because inconsistent with Cllmfile workflow (can't reference remote in config)
- Bad, because teams can't share remote schema references in config files
- Bad, because less flexible than full support

### URL support in Cllmfile only

**Example:**

```yaml
# config.Cllmfile.yml
json_schema_file: "https://example.com/schema.json"
```

- Good, because Cllmfiles are version-controlled (schema URLs tracked in git)
- Good, because it encourages configuration-based workflows
- Neutral, because CLI would still require local files for one-off usage
- Bad, because inconsistent with CLI workflow
- Bad, because quick CLI experiments can't use remote schemas
- Bad, because less flexible than full support

### Full URL support (chosen)

**Supports URLs in both CLI flags and Cllmfiles**

- Good, because maximum flexibility for all workflows
- Good, because consistent with ADR-0005 hybrid approach
- Good, because no new flags needed (reuses existing `--json-schema-file`)
- Good, because teams can use remote schemas in configs AND override with CLI
- Good, because supports both quick CLI usage and persistent config
- Good, because enables gradual adoption (start with local, move to remote)
- Neutral, because requires URL detection logic in both CLI and config parsing
- Neutral, because same implementation complexity as other options (caching needed regardless)
- Bad, because slightly more code than single-method support (mitigated by shared URL handling logic)

### New dedicated flags

**Example:**

```bash
cllm "prompt" --json-schema-url https://example.com/schema.json
```

```yaml
json_schema_url: "https://example.com/schema.json"
```

- Good, because explicit separation of local vs remote schemas
- Good, because clearer intent in CLI usage
- Neutral, because requires new flags and config keys
- Bad, because adds API surface area (more flags to learn)
- Bad, because inconsistent with existing `--json-schema-file` pattern
- Bad, because users need to remember which flag for which use case
- Bad, because precedence rules become more complex (local vs remote vs file vs url)
- Bad, because breaks the principle of "URLs are just paths" (less Unix-like)

### No remote schema support (status quo)

**Continue requiring local files only**

- Good, because no implementation work needed
- Good, because no network dependencies
- Good, because simpler security model
- Neutral, because current workflows still work
- Bad, because users must manually download schemas
- Bad, because schema version sync across team is manual and error-prone
- Bad, because can't reference canonical sources directly
- Bad, because duplicates schema files across projects
- Bad, because doesn't solve the stated problem

## More Information

### Related Features

- **Cache Management**: `--clear-schema-cache` flag to invalidate all cached schemas
- **Cache Inspection**: `--show-schema-cache` to list cached schemas with URLs and timestamps
- **Offline Mode**: Environment variable `CLLM_OFFLINE_MODE=1` to prevent network requests (use cache only)
- **Custom Cache TTL**: Environment variable `CLLM_SCHEMA_CACHE_TTL=86400` (seconds)

### Implementation Details

**URL Detection (config.py and cli.py):**

```python
def is_remote_schema(path: str) -> bool:
    """Check if path is a remote URL."""
    return path.startswith('https://') or path.startswith('http://')

def load_schema(path: str) -> dict:
    """Load schema from local file or remote URL."""
    if is_remote_schema(path):
        return load_remote_schema(path)
    else:
        return load_local_schema(path)
```

**Remote Schema Loading:**

```python
import hashlib
import json
import os
import time
from pathlib import Path
import requests

CACHE_DIR = Path.home() / '.cllm' / 'cache' / 'schemas'
DEFAULT_CACHE_TTL = 86400  # 24 hours in seconds
MAX_SCHEMA_SIZE = 1024 * 1024  # 1MB

def get_cache_path(url: str) -> Path:
    """Generate cache file path from URL hash."""
    url_hash = hashlib.sha256(url.encode()).hexdigest()
    return CACHE_DIR / f"{url_hash}.json"

def load_remote_schema(url: str) -> dict:
    """Download and cache remote schema."""
    # Check HTTPS
    if not url.startswith('https://'):
        allow_http = os.getenv('CLLM_ALLOW_HTTP_SCHEMAS') == '1'
        if not allow_http:
            raise ValueError(f"Insecure schema URL (HTTP not allowed): {url}")

    # Check cache
    cache_path = get_cache_path(url)
    cache_ttl = int(os.getenv('CLLM_SCHEMA_CACHE_TTL', DEFAULT_CACHE_TTL))

    if cache_path.exists():
        cache_age = time.time() - cache_path.stat().st_mtime
        if cache_age < cache_ttl:
            # Use cached version
            with open(cache_path) as f:
                return json.load(f)

    # Download schema
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # Check size
        content_length = len(response.content)
        if content_length > MAX_SCHEMA_SIZE:
            raise ValueError(f"Schema too large: {content_length} bytes (max {MAX_SCHEMA_SIZE})")

        # Parse and validate
        schema = response.json()

        # Cache it
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(cache_path, 'w') as f:
            json.dump(schema, f)

        return schema

    except requests.RequestException as e:
        # Try stale cache as fallback
        if cache_path.exists():
            print(f"Warning: Network error, using cached schema from {url}")
            with open(cache_path) as f:
                return json.load(f)
        raise ValueError(f"Failed to download schema from {url}: {e}")
```

### Environment Variables

- `CLLM_SCHEMA_CACHE_TTL`: Cache TTL in seconds (default: 86400 = 24 hours)
- `CLLM_ALLOW_HTTP_SCHEMAS`: Allow HTTP URLs (default: disabled, HTTPS only)
- `CLLM_OFFLINE_MODE`: Disable network requests, use cache only (default: disabled)
- `CLLM_CONFIRM_REMOTE_SCHEMAS`: Prompt before downloading new schemas (default: disabled)
- `CLLM_MAX_SCHEMA_SIZE`: Maximum schema size in bytes (default: 1048576 = 1MB)

### URL Versioning Best Practices

**Git-based schemas (GitHub, GitLab, etc.):**

```yaml
# Pin to specific commit (immutable)
json_schema_file: "https://raw.githubusercontent.com/org/repo/abc123def/schema.json"

# Pin to tag (immutable if tag isn't moved)
json_schema_file: "https://raw.githubusercontent.com/org/repo/v1.2.3/schema.json"

# Track branch (mutable, updates with branch)
json_schema_file: "https://raw.githubusercontent.com/org/repo/main/schema.json"
```

**Recommendation**: Use commit hashes or tags for production, branches for development.

### Documentation Requirements

1. **README.md**: Add remote schema section with examples
2. **examples/schemas/README.md**: Update with remote schema examples and caching behavior
3. **examples/configs/**: Add example Cllmfile with remote schema reference
4. **TROUBLESHOOTING.md**: Add network error debugging guide
5. **SECURITY.md**: Document security considerations for remote schemas

### Implementation Phases

**Phase 1**: Core remote schema support

- Add URL detection in `config.py` and `cli.py`
- Implement remote schema downloading with `requests` library
- Add basic error handling for network failures
- Update tests to cover URL detection and downloading (with mocks)

**Phase 2**: Caching and performance

- Implement cache directory structure (`~/.cllm/cache/schemas/`)
- Add TTL-based cache expiration
- Implement stale cache fallback on network errors
- Add `--clear-schema-cache` flag

**Phase 3**: Security and polish

- Add HTTPS-only enforcement
- Implement size limits and timeouts
- Add cache inspection with `--show-schema-cache`
- Create documentation and examples
- Add environment variables for configuration

---

## AI-Specific Extensions

### AI Guidance Level

**Flexible**: Adapt implementation details while maintaining core principles. The caching strategy (TTL, cache directory structure) can be adjusted based on performance testing, but the hybrid URL support in both CLI and Cllmfiles must be preserved. Security measures (HTTPS-only, size limits) are required.

### AI Tool Preferences

- Preferred AI tools: Claude Code, GitHub Copilot
- Special instructions:
  - Use `requests` library for HTTP operations (already used by LiteLLM)
  - Follow existing patterns in `config.py` for path resolution
  - Maintain backward compatibility - local files must continue working
  - Error messages should guide users to solutions (check network, use cache, try local file)
  - Cache implementation should be transparent (no user action required)

### Test Expectations

- `test_config.py`: Test URL detection, remote schema loading with mocked requests
- `test_config.py`: Test cache hit/miss scenarios
- `test_config.py`: Test cache TTL expiration
- `test_config.py`: Test stale cache fallback on network errors
- `test_config.py`: Test HTTPS-only enforcement (HTTP URLs rejected)
- `test_config.py`: Test size limit enforcement
- `test_config.py`: Test timeout handling
- `test_cli.py`: Test `--json-schema-file` with URLs
- `test_cli.py`: Test `--clear-schema-cache` flag
- `test_cli.py`: Test error messages for network failures
- Mock all HTTP requests using `unittest.mock.patch` or `responses` library
- Integration tests: Verify URL schemas work end-to-end (with mocked HTTP)
- Performance: Cache should eliminate redundant downloads (verify with mock call counts)

### Dependencies

- Related ADRs:
  - ADR-0005 (Structured Output Support) - remote schemas extend existing schema system
  - ADR-0003 (Cllmfile Configuration) - URL support in Cllmfile follows same patterns
- System components:
  - `config.py` - add URL detection and remote schema loading
  - `cli.py` - add URL support in `--json-schema-file` flag
  - Cache directory: `~/.cllm/cache/schemas/` (new)
- External dependencies:
  - `requests` - HTTP client for downloading schemas (already in LiteLLM dependencies)
  - No new dependencies needed

### Timeline

- Implementation deadline: No hard deadline, feature-driven
- First review: After Phase 1 implementation (core functionality)
- Second review: After Phase 2 implementation (caching complete)
- Final review: After Phase 3 implementation (security and documentation)
- Revision triggers:
  - Security vulnerabilities in remote schema handling
  - User feedback on cache behavior or network errors
  - Performance issues with schema downloads

### Risk Assessment

#### Technical Risks

- **Network Availability**: Remote schemas fail when network unavailable
  - Mitigation: Cache schemas with 24h TTL, fallback to stale cache on network errors

- **Schema Availability**: Remote URLs could become unavailable (404, server down)
  - Mitigation: Stale cache fallback, clear error messages suggesting local file alternative

- **Schema Mutability**: Remote schemas could change unexpectedly (breaking changes)
  - Mitigation: Document version pinning best practices (commit hashes), cache provides stability

- **Performance Degradation**: Network requests add latency
  - Mitigation: Cache eliminates redundant downloads, 10s timeout prevents hanging

- **Cache Corruption**: Cached schemas could become corrupted
  - Mitigation: Validate JSON on load, invalidate and re-download on parse errors

#### Security Risks

- **Man-in-the-Middle Attacks**: Malicious schemas injected via network
  - Mitigation: HTTPS-only by default, schema validation before use

- **Malicious Schemas**: Remote schemas could be intentionally malicious (DoS via size)
  - Mitigation: 1MB size limit, 10s timeout, schema validation

- **Cache Poisoning**: Malicious schemas cached and reused
  - Mitigation: HTTPS-only, schema validation, cache clearing mechanism

- **URL Injection**: User-provided URLs could point to sensitive endpoints
  - Mitigation: No auth headers sent, schema validation ensures JSON Schema format

### Human Review

- Review required: After each implementation phase
- Reviewers: Project maintainers, security-conscious team member
- Approval criteria:
  - All test expectations met (unit, integration, security tests)
  - Security measures implemented (HTTPS-only, size limits, validation)
  - Caching works correctly (TTL, invalidation, fallback)
  - Documentation complete with examples and security guidance
  - Error messages are clear and actionable
  - Backward compatible (existing local file workflows unchanged)

### Feedback Log

_This section will be filled in after implementation_

**Implementation date:** TBD

**Actual outcomes:** TBD

**Challenges encountered:** TBD

**Lessons learned:** TBD

**Suggested improvements:** TBD
