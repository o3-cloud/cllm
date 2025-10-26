# Use uv as Python Package Manager

## Context and Problem Statement

Python package management has traditionally been fragmented across multiple tools (pip, pip-tools, poetry, pipenv, pyenv, virtualenv), each serving different aspects of dependency management, environment isolation, and Python version management. This fragmentation leads to complexity in tooling setup, inconsistent developer experiences, and slower dependency resolution times that can impact development velocity.

## Decision Drivers

- **Performance**: Dependency resolution and installation speed significantly impacts developer productivity
- **Developer Experience**: Unified tooling reduces cognitive overhead and onboarding time
- **Modern Workflow Support**: Need for lockfiles, workspaces, and reproducible builds
- **Maintenance Burden**: Reducing the number of tools to maintain and learn
- **Ecosystem Compatibility**: Must work seamlessly with existing Python ecosystem standards

## Considered Options

- uv (Astral's Rust-based package manager)
- poetry (Traditional Python-based solution)
- pip + pip-tools (Minimal traditional approach)
- rye (Another Rust-based alternative)

## Decision Outcome

Chosen option: "uv", because it provides 10-100x performance improvements over traditional tools while serving as a unified replacement for pip, pip-tools, pipx, poetry, pyenv, and virtualenv. Its Rust-based implementation delivers exceptional speed without sacrificing compatibility with the Python ecosystem.

### Consequences

- Good, because dependency resolution and installation becomes significantly faster (10-100x)
- Good, because we consolidate multiple tools (pip, pip-tools, poetry, pyenv, virtualenv, pipx) into one
- Good, because it supports modern features like lockfiles, workspaces, and inline script dependencies
- Good, because it provides Python version management, eliminating the need for pyenv
- Good, because it maintains CLI compatibility with familiar tools (drop-in replacement syntax)
- Neutral, because the tool is in 0.x versioning, indicating active development
- Bad, because team members need to learn a new tool (though CLI compatibility reduces friction)
- Bad, because contributing to uv requires Rust knowledge, unlike Python-based alternatives

### Confirmation

- Measure dependency installation times compared to previous tooling (target: >5x improvement)
- Monitor developer feedback on tooling experience during first 30 days
- Verify successful CI/CD pipeline integration within first sprint
- Track any compatibility issues with existing Python packages

## Pros and Cons of the Options

### uv (Astral's Rust-based package manager)

uv is an extremely fast Python package and project manager written in Rust by the creators of Ruff.

- Good, because it's 10-100x faster than pip and other traditional tools
- Good, because it replaces multiple tools (pip, pip-tools, pipx, poetry, pyenv, virtualenv) with a single utility
- Good, because it supports universal lockfiles for reproducible builds
- Good, because it includes Python version management and installation
- Good, because it has workspace support similar to Cargo (Rust) or npm workspaces
- Good, because it can be installed without requiring Rust or Python pre-installed
- Good, because it's backed by Astral, who also maintains Ruff (widely adopted tool)
- Good, because it supports inline dependency metadata for scripts
- Neutral, because it's currently in 0.x versioning (indicating ongoing development)
- Bad, because it's relatively new compared to established tools like poetry
- Bad, because contributing requires Rust knowledge

### poetry (Traditional Python-based solution)

Poetry is a mature Python dependency management and packaging tool.

- Good, because it has a large, established community and ecosystem
- Good, because it's written in Python, making contributions accessible
- Good, because it provides deterministic dependency resolution with lockfiles
- Good, because it's feature-complete and stable (1.x versioning)
- Neutral, because it combines dependency management and packaging (not needed for all projects)
- Bad, because dependency resolution can be slow, especially with large dependency trees
- Bad, because it doesn't include Python version management (still need pyenv)
- Bad, because it doesn't replace pip or pipx (multiple tools still needed)

### pip + pip-tools (Minimal traditional approach)

The traditional combination of pip for installation and pip-tools for lockfile generation.

- Good, because it's the most widely known and documented approach
- Good, because it has minimal learning curve for Python developers
- Good, because pip-tools provides lockfile support (requirements.txt)
- Neutral, because it's simple but requires understanding multiple workflows
- Bad, because dependency resolution is slow
- Bad, because it requires multiple tools (pip, pip-tools, virtualenv, pyenv) for complete workflow
- Bad, because it lacks modern features like workspaces
- Bad, because pip-tools workflow is less intuitive than integrated solutions

### rye (Another Rust-based alternative)

Rye is another Rust-based Python project and package management tool.

- Good, because it's also fast (Rust-based implementation)
- Good, because it provides unified Python and package management
- Good, because it has good workspace support
- Neutral, because it has a smaller community than uv or poetry
- Neutral, because it was created before uv by some of the same ecosystem contributors
- Bad, because uv has gained more momentum and community adoption
- Bad, because it doesn't have the backing of an established tool company like Astral

## More Information

uv is developed by Astral (https://github.com/astral-sh/uv), the creators of Ruff, which has become the de facto standard for Python linting and formatting. The team's track record with Ruff demonstrates their ability to build high-performance, widely adopted Python tooling.

This decision positions the project to adopt modern Python development practices with minimal tooling overhead. As uv approaches 1.0, we can expect increased stability while maintaining the performance benefits.

Related resources:

- uv GitHub repository: https://github.com/astral-sh/uv
- uv documentation: https://docs.astral.sh/uv/

---

## AI-Specific Extensions

### AI Guidance Level

**Flexible**: AI agents should use uv for all package management tasks, but may adapt commands based on specific context. If uv doesn't support a particular operation, AI should document the limitation and propose alternatives.

### AI Tool Preferences

- Preferred AI tools: Claude Code, GitHub Copilot
- Special instructions:
  - Always use `uv` commands instead of `pip` when managing dependencies
  - Use `uv add <package>` instead of `pip install <package>`
  - Use `uv sync` to install dependencies from lockfile
  - Use `uv run` to execute scripts with project dependencies
  - Reference uv documentation when uncertain about command syntax

### Test Expectations

- Installation scripts should use uv commands
- CI/CD pipelines should be updated to use uv
- Documentation should reference uv in setup instructions
- Performance benchmarks should show improvement over previous tooling

### Dependencies

- Related ADRs: None (first ADR)
- System components: Development environment, CI/CD pipelines, documentation
- External dependencies: uv binary (can be installed via curl, pip, or pipx)

### Timeline

- Implementation deadline: Immediate (for new setup)
- First review: 30 days after initial adoption
- Revision triggers:
  - uv reaches 1.0 stable release
  - Discovery of critical bugs or compatibility issues
  - Significant changes to Python packaging ecosystem standards

### Risk Assessment

#### Technical Risks

- **Early versioning (0.x)**: uv is still in active development
  - Mitigation: Monitor uv releases and changelog; participate in community feedback
  - Impact: Low - tool is already production-ready for many users

- **Compatibility issues with specific packages**: Some packages may have edge cases
  - Mitigation: Test with critical dependencies; maintain fallback to pip if needed
  - Impact: Low - uv aims for pip compatibility

#### Business Risks

- **Team adoption and learning curve**: Developers need to learn new commands
  - Mitigation: Provide documentation and examples; leverage CLI compatibility with familiar tools
  - Impact: Low - CLI is similar to existing tools

- **Tooling support in CI/CD**: May require updates to existing pipelines
  - Mitigation: Update CI/CD configurations early; test thoroughly
  - Impact: Medium - requires coordination but straightforward implementation

### Human Review

- Review required: After implementation feedback period (30 days)
- Reviewers: Development team lead, DevOps engineer
- Approval criteria:
  - Performance improvements verified
  - No blocking compatibility issues
  - Team feedback is positive or neutral
  - CI/CD pipelines functioning correctly

### Feedback Log

- Implementation date: 2025-10-26 (ADR creation date)
- Actual outcomes: _To be filled after implementation period_
- Challenges encountered: _To be filled after implementation period_
- Lessons learned: _To be filled after implementation period_
- Suggested improvements: _To be filled after implementation period_
